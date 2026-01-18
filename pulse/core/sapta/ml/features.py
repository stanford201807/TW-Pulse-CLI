"""
SAPTA Feature Extraction for ML.

Extracts features from module scores for ML training.
"""

import numpy as np
import pandas as pd

from pulse.core.sapta.models import ModuleScore, SaptaResult


class SaptaFeatureExtractor:
    """
    Extract features from SAPTA module scores for ML training.

    Features are organized by module and include both raw scores
    and derived metrics useful for prediction.
    """

    # Define feature order for consistent training/inference
    FEATURE_ORDER = [
        # Absorption features
        "absorption_score",
        "absorption_score_pct",
        "absorption_volume_spike_ratio",
        "absorption_price_held",
        "absorption_higher_lows_count",
        "absorption_avg_close_strength",
        # Compression features
        "compression_score",
        "compression_score_pct",
        "compression_atr_slope",
        "compression_range_contraction",
        "compression_higher_lows",
        "compression_lower_highs",
        "compression_avg_body_ratio",
        # BB Squeeze features
        "bb_squeeze_score",
        "bb_squeeze_score_pct",
        "bb_squeeze_bb_width_current",
        "bb_squeeze_bb_width_percentile",
        "bb_squeeze_squeeze_duration",
        "bb_squeeze_price_position_in_bb",
        # Elliott features
        "elliott_score",
        "elliott_score_pct",
        "elliott_fib_retracement",
        "elliott_trend_context",
        "elliott_abc_pattern",
        "elliott_rule_violations",
        "elliott_rsi_divergence",
        # Time Projection features
        "time_projection_score",
        "time_projection_score_pct",
        "time_projection_days_since_low",
        "time_projection_in_fib_window",
        "time_projection_lunar_phase",
        # Anti-Distribution features
        "anti_distribution_score",
        "anti_distribution_score_pct",
        "anti_distribution_distribution_candles",
        "anti_distribution_false_breakout",
        "anti_distribution_obv_divergence",
        # Aggregate features
        "total_score",
        "weighted_score",
        "modules_active",
        "penalty_score",
    ]

    def __init__(self):
        self.feature_names = self.FEATURE_ORDER.copy()

    def extract_from_result(self, result: SaptaResult) -> dict[str, float]:
        """
        Extract feature dict from a SaptaResult.

        Args:
            result: SAPTA analysis result

        Returns:
            Dictionary of feature_name -> value
        """
        features = {}

        # Module scores and features
        modules = [
            ("absorption", result.absorption),
            ("compression", result.compression),
            ("bb_squeeze", result.bb_squeeze),
            ("elliott", result.elliott),
            ("time_projection", result.time_projection),
            ("anti_distribution", result.anti_distribution),
        ]

        modules_active = 0

        for name, data in modules:
            if data:
                features[f"{name}_score"] = data.get("score", 0.0)
                max_score = data.get("max_score", 1.0)
                features[f"{name}_score_pct"] = (
                    data.get("score", 0.0) / max_score * 100 if max_score > 0 else 0.0
                )
                if data.get("status", False):
                    modules_active += 1
            else:
                features[f"{name}_score"] = 0.0
                features[f"{name}_score_pct"] = 0.0

        # Add raw features from result.features
        for feat_name, feat_val in result.features.items():
            if isinstance(feat_val, (int, float)):
                features[feat_name] = float(feat_val)
            elif isinstance(feat_val, bool):
                features[feat_name] = 1.0 if feat_val else 0.0

        # Aggregate features
        features["total_score"] = result.total_score
        features["weighted_score"] = result.weighted_score
        features["modules_active"] = float(modules_active)
        features["penalty_score"] = result.penalty_score

        return features

    def extract_from_scores(
        self,
        module_scores: dict[str, ModuleScore],
    ) -> dict[str, float]:
        """
        Extract features directly from module scores.

        Args:
            module_scores: Dict of module_name -> ModuleScore

        Returns:
            Dictionary of feature_name -> value
        """
        features = {}
        modules_active = 0

        for name, score in module_scores.items():
            features[f"{name}_score"] = score.score
            features[f"{name}_score_pct"] = score.score_pct

            if score.status:
                modules_active += 1

            # Add raw features with prefix
            for feat_name, feat_val in score.raw_features.items():
                if isinstance(feat_val, (int, float)):
                    features[f"{name}_{feat_name}"] = float(feat_val)
                elif isinstance(feat_val, bool):
                    features[f"{name}_{feat_name}"] = 1.0 if feat_val else 0.0

        features["modules_active"] = float(modules_active)

        return features

    def to_vector(self, features: dict[str, float]) -> np.ndarray:
        """
        Convert feature dict to numpy array in consistent order.

        Args:
            features: Feature dictionary

        Returns:
            Numpy array of features
        """
        return np.array([features.get(name, 0.0) for name in self.feature_names])

    def to_dataframe(self, feature_list: list[dict[str, float]]) -> pd.DataFrame:
        """
        Convert list of feature dicts to DataFrame.

        Args:
            feature_list: List of feature dictionaries

        Returns:
            DataFrame with consistent columns
        """
        # Collect all unique feature names
        all_names = set()
        for f in feature_list:
            all_names.update(f.keys())

        # Sort for consistency
        columns = sorted(all_names)

        # Build DataFrame
        data = []
        for f in feature_list:
            row = [f.get(col, 0.0) for col in columns]
            data.append(row)

        return pd.DataFrame(data, columns=columns)

    def get_feature_names(self) -> list[str]:
        """Get list of feature names in order."""
        return self.feature_names.copy()
