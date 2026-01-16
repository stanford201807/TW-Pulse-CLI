"""
SAPTA ML Trainer.

Walk-forward training with XGBoost for SAPTA model.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

from pulse.core.sapta.ml.features import SaptaFeatureExtractor
from pulse.core.sapta.ml.labeling import LabeledSample, SaptaLabeler
from pulse.core.sapta.models import MLModelInfo, SaptaConfig
from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class TrainingResult:
    """Result from training."""

    model_path: str
    thresholds_path: str
    model_info: MLModelInfo
    metrics: dict[str, float]
    feature_importance: dict[str, float]


class SaptaTrainer:
    """
    Train SAPTA ML model using walk-forward validation.

    Walk-forward process:
    1. Split data into train/validation windows
    2. Train on window, validate on next period
    3. Roll forward and repeat
    4. Combine results for final model
    """

    def __init__(
        self,
        config: SaptaConfig | None = None,
        model_dir: str | None = None,
    ):
        """
        Initialize trainer.

        Args:
            config: SAPTA configuration
            model_dir: Directory to save trained models
        """
        self.config = config or SaptaConfig()
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent.parent / "data"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.feature_extractor = SaptaFeatureExtractor()
        self.labeler = SaptaLabeler(
            target_gain_pct=self.config.target_gain_pct,
            target_days=self.config.target_days,
        )

    def train(
        self,
        samples: list[LabeledSample],
        test_size: float = 0.2,
    ) -> TrainingResult | None:
        """
        Train model on labeled samples.

        Args:
            samples: List of labeled samples
            test_size: Fraction for test set

        Returns:
            TrainingResult with model info and paths
        """
        try:
            from sklearn.metrics import (
                accuracy_score,
                f1_score,
                precision_score,
                recall_score,
                roc_auc_score,
            )
            from sklearn.model_selection import train_test_split

            try:
                import xgboost as xgb

                use_xgboost = True
            except (ImportError, Exception):
                from sklearn.ensemble import GradientBoostingClassifier

                use_xgboost = False
                log.info("XGBoost not available, using sklearn GradientBoosting")
            import joblib
        except ImportError as e:
            log.error(f"Missing ML dependencies: {e}")
            return None

        if len(samples) < 100:
            log.warning(f"Too few samples ({len(samples)}), need at least 100")
            return None

        # Prepare data
        X, y = self._prepare_data(samples)  # noqa: N806

        if X is None or len(X) == 0:
            log.error("No valid features extracted")
            return None

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(  # noqa: N806
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        log.info(f"Training on {len(X_train)} samples, testing on {len(X_test)}")

        # Train model (XGBoost or sklearn fallback)
        if use_xgboost:
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective="binary:logistic",
                eval_metric="auc",
                random_state=42,
            )
            model.fit(
                X_train,
                y_train,
                eval_set=[(X_test, y_test)],
                verbose=False,
            )
        else:
            model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            )
            model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1": f1_score(y_test, y_pred, zero_division=0),
            "auc_roc": roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0,
        }

        log.info(f"Model metrics: {metrics}")

        # Feature importance
        feature_names = self._get_feature_names(samples)
        importance = dict(zip(feature_names, model.feature_importances_))

        # Learn thresholds from tree splits
        thresholds = self._learn_thresholds(model, X, y)

        # Save model
        model_path = self.model_dir / "sapta_model.pkl"
        joblib.dump(model, model_path)

        # Save thresholds
        thresholds_path = self.model_dir / "thresholds.json"
        with open(thresholds_path, "w") as f:
            json.dump(thresholds, f, indent=2)

        # Create model info
        model_info = MLModelInfo(
            model_version="1.0.0",
            trained_at=datetime.now(),
            training_samples=len(X_train),
            validation_samples=len(X_test),
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1"],
            auc_roc=metrics["auc_roc"],
            threshold_pre_markup=thresholds.get("pre_markup", 80.0),
            threshold_siap=thresholds.get("siap", 65.0),
            threshold_watchlist=thresholds.get("watchlist", 50.0),
            feature_importance=importance,
            target_gain_pct=self.config.target_gain_pct,
            target_days=self.config.target_days,
            tickers_used=list(set(s.ticker for s in samples)),
        )

        return TrainingResult(
            model_path=str(model_path),
            thresholds_path=str(thresholds_path),
            model_info=model_info,
            metrics=metrics,
            feature_importance=importance,
        )

    def walk_forward_train(
        self,
        samples: list[LabeledSample],
        train_months: int = 36,
        test_months: int = 6,
    ) -> TrainingResult | None:
        """
        Walk-forward training.

        Args:
            samples: All labeled samples
            train_months: Months of training data
            test_months: Months of test data

        Returns:
            TrainingResult from final combined model
        """
        try:
            try:
                import xgboost as xgb

                use_xgboost = True
            except (ImportError, Exception):
                from sklearn.ensemble import GradientBoostingClassifier

                use_xgboost = False
            import joblib
            from sklearn.metrics import (
                accuracy_score,
                f1_score,
                precision_score,
                recall_score,
                roc_auc_score,
            )
        except ImportError as e:
            log.error(f"Missing ML dependencies: {e}")
            return None

        # Sort samples by date
        samples = sorted(samples, key=lambda s: s.date)

        if len(samples) < 100:
            log.warning("Too few samples for walk-forward training")
            return self.train(samples)

        # Convert to DataFrame for easier date handling
        dates = [s.date for s in samples]
        min_date = min(dates)
        max_date = max(dates)

        log.info(f"Walk-forward training: {min_date} to {max_date}")

        # Collect all out-of-sample predictions
        all_predictions = []
        all_labels = []
        all_probas = []

        # Walk forward
        current_start = min_date

        while True:
            train_end = self._add_months(current_start, train_months)
            test_end = self._add_months(train_end, test_months)

            if train_end >= max_date:
                break

            # Split samples
            train_samples = [s for s in samples if s.date < train_end]
            test_samples = [s for s in samples if train_end <= s.date < test_end]

            if len(train_samples) < 50 or len(test_samples) < 10:
                current_start = self._add_months(current_start, test_months)
                continue

            # Prepare data
            X_train, y_train = self._prepare_data(train_samples)  # noqa: N806
            X_test, y_test = self._prepare_data(test_samples)  # noqa: N806

            if X_train is None or X_test is None:
                current_start = self._add_months(current_start, test_months)
                continue

            # Train model
            if use_xgboost:
                model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    objective="binary:logistic",
                    random_state=42,
                )
                model.fit(X_train, y_train, verbose=False)
            else:
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                )
                model.fit(X_train, y_train)

            # Predict
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            all_predictions.extend(y_pred)
            all_labels.extend(y_test)
            all_probas.extend(y_proba)

            log.info(f"Fold {train_end}: train={len(train_samples)}, test={len(test_samples)}")

            # Move forward
            current_start = self._add_months(current_start, test_months)

        if not all_predictions:
            log.warning("No predictions from walk-forward, falling back to simple split")
            return self.train(samples)

        # Calculate overall metrics
        metrics = {
            "accuracy": accuracy_score(all_labels, all_predictions),
            "precision": precision_score(all_labels, all_predictions, zero_division=0),
            "recall": recall_score(all_labels, all_predictions, zero_division=0),
            "f1": f1_score(all_labels, all_predictions, zero_division=0),
            "auc_roc": roc_auc_score(all_labels, all_probas) if len(set(all_labels)) > 1 else 0.0,
        }

        log.info(f"Walk-forward metrics: {metrics}")

        # Train final model on all data
        X_all, y_all = self._prepare_data(samples)  # noqa: N806

        if use_xgboost:
            final_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective="binary:logistic",
                random_state=42,
            )
            final_model.fit(X_all, y_all, verbose=False)
        else:
            final_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
            )
            final_model.fit(X_all, y_all)

        # Feature importance
        feature_names = self._get_feature_names(samples)
        importance = dict(zip(feature_names, final_model.feature_importances_))

        # Learn thresholds
        thresholds = self._learn_thresholds(final_model, X_all, y_all)

        # Save
        model_path = self.model_dir / "sapta_model.pkl"
        joblib.dump(final_model, model_path)

        thresholds_path = self.model_dir / "thresholds.json"
        with open(thresholds_path, "w") as f:
            json.dump(thresholds, f, indent=2)

        model_info = MLModelInfo(
            model_version="1.0.0",
            trained_at=datetime.now(),
            training_samples=len(samples),
            validation_samples=len(all_predictions),
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1"],
            auc_roc=metrics["auc_roc"],
            threshold_pre_markup=thresholds.get("pre_markup", 80.0),
            threshold_siap=thresholds.get("siap", 65.0),
            threshold_watchlist=thresholds.get("watchlist", 50.0),
            feature_importance=importance,
            target_gain_pct=self.config.target_gain_pct,
            target_days=self.config.target_days,
            tickers_used=list(set(s.ticker for s in samples)),
        )

        return TrainingResult(
            model_path=str(model_path),
            thresholds_path=str(thresholds_path),
            model_info=model_info,
            metrics=metrics,
            feature_importance=importance,
        )

    def _prepare_data(
        self,
        samples: list[LabeledSample],
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Prepare feature matrix and labels."""
        if not samples:
            return None, None

        # Get all feature names
        all_names = set()
        for s in samples:
            all_names.update(s.features.keys())
        feature_names = sorted(all_names)

        # Build matrices
        X = []  # noqa: N806
        y = []  # noqa: N806

        for s in samples:
            row = [s.features.get(name, 0.0) for name in feature_names]
            X.append(row)
            y.append(s.label)

        return np.array(X), np.array(y)

    def _get_feature_names(self, samples: list[LabeledSample]) -> list[str]:
        """Get sorted list of feature names."""
        all_names = set()
        for s in samples:
            all_names.update(s.features.keys())
        return sorted(all_names)

    def _learn_thresholds(
        self,
        model: Any,
        X: np.ndarray,  # noqa: N803
        y: np.ndarray,  # noqa: N803
    ) -> dict[str, float]:
        """
        Learn optimal thresholds from model predictions.

        Uses predicted probabilities to find score thresholds
        that maximize precision at different recall levels.
        """
        # Get predicted probabilities
        probas = model.predict_proba(X)[:, 1]

        # Sort by probability
        sorted_indices = np.argsort(probas)[::-1]

        # Find thresholds at different percentiles
        n = len(probas)

        # PRE-MARKUP: Top 10% (high precision)
        pre_markup_idx = int(n * 0.10)
        pre_markup_threshold = probas[sorted_indices[pre_markup_idx]] if pre_markup_idx < n else 0.8

        # SIAP: Top 25%
        siap_idx = int(n * 0.25)
        siap_threshold = probas[sorted_indices[siap_idx]] if siap_idx < n else 0.65

        # WATCHLIST: Top 50%
        watchlist_idx = int(n * 0.50)
        watchlist_threshold = probas[sorted_indices[watchlist_idx]] if watchlist_idx < n else 0.5

        # Convert to score scale (0-100)
        return {
            "pre_markup": float(pre_markup_threshold * 100),
            "siap": float(siap_threshold * 100),
            "watchlist": float(watchlist_threshold * 100),
        }

    def _add_months(self, d: date, months: int) -> date:
        """Add months to a date."""
        year = d.year + (d.month + months - 1) // 12
        month = (d.month + months - 1) % 12 + 1
        day = min(d.day, 28)  # Safe day
        return date(year, month, day)
