#!/usr/bin/env python3
"""
SAPTA Model Training Script.

Train SAPTA ML model using historical data from yfinance.

Usage:
    # Basic training with default settings
    python -m pulse.core.sapta.ml.train_model

    # Custom target parameters
    python -m pulse.core.sapta.ml.train_model --target-gain 15 --target-days 30

    # Walk-forward training with progress display
    python -m pulse.core.sapta.ml.train_model --walk-forward --stocks 200

    # Resume from checkpoint
    python -m pulse.core.sapta.ml.train_model --resume

    # Generate feature importance report
    python -m pulse.core.sapta.ml.train_model --report-only
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from pulse.core.sapta.ml.data_loader import SaptaDataLoader  # noqa: E402
from pulse.core.sapta.ml.labeling import LabeledSample, SaptaLabeler  # noqa: E402
from pulse.core.sapta.ml.trainer import SaptaTrainer  # noqa: E402
from pulse.core.sapta.models import SaptaConfig  # noqa: E402
from pulse.core.sapta.modules import (  # noqa: E402
    AntiDistributionModule,
    BBSqueezeModule,
    CompressionModule,
    ElliottModule,
    SupplyAbsorptionModule,
    TimeProjectionModule,
)
from pulse.utils.logger import get_logger  # noqa: E402

log = get_logger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for training run."""

    target_gain_pct: float = 10.0
    target_days: int = 20
    window_size: int = 120
    step_size: int = 5
    test_size: float = 0.2
    walk_forward: bool = False
    train_months: int = 36
    test_months: int = 6
    stocks: int = 100
    period: str = "2y"
    min_rows: int = 120
    output_dir: str = "pulse/core/sapta/data"
    resume: bool = False
    workers: int = 4


@dataclass
class TrainingReport:
    """Complete training report."""

    timestamp: str
    config: dict
    data_stats: dict
    label_distribution: dict
    metrics: dict
    thresholds: dict
    feature_importance: dict
    model_info: dict
    files_saved: list[str]


def extract_features_from_df(
    df: pd.DataFrame,
    modules: dict,
) -> dict[str, float]:
    """Extract features from DataFrame using SAPTA modules."""
    features = {}

    for name, module in modules.items():
        try:
            score = module.analyze(df)
            features[f"{name}_score"] = score.score
            features[f"{name}_score_pct"] = score.score_pct
            features[f"{name}_status"] = 1.0 if score.status else 0.0

            # Add raw features
            for feat_name, feat_val in score.raw_features.items():
                if isinstance(feat_val, (int, float)):
                    features[f"{name}_{feat_name}"] = float(feat_val)
                elif isinstance(feat_val, bool):
                    features[f"{name}_{feat_name}"] = 1.0 if feat_val else 0.0
        except Exception:
            # Module failed, use zeros
            features[f"{name}_score"] = 0.0
            features[f"{name}_score_pct"] = 0.0
            features[f"{name}_status"] = 0.0

    return features


def generate_samples(
    ticker: str,
    df: pd.DataFrame,
    modules: dict,
    labeler: SaptaLabeler,
    window_size: int = 120,
    step_size: int = 5,
) -> list[LabeledSample]:
    """
    Generate labeled samples from a stock's historical data.

    Uses sliding window to generate multiple samples per stock.
    """
    samples = []

    # Label the entire series first
    labeled_df = labeler.label_price_series(df)

    # Slide through the data
    for i in range(window_size, len(df) - labeler.target_days, step_size):
        try:
            # Get window for feature extraction
            window_df = df.iloc[i - window_size : i].copy()

            if len(window_df) < window_size:
                continue

            # Extract features at this point
            features = extract_features_from_df(window_df, modules)

            # Get label from labeled_df at position i
            row = labeled_df.iloc[i]
            label = int(row.get("hit_target", 0))
            forward_return = float(row.get("forward_return", 0))
            max_return = float(row.get("max_forward_return", 0))
            days_to_target = (
                int(row["days_to_target"]) if pd.notna(row.get("days_to_target")) else None
            )

            # Handle date extraction from DatetimeIndex
            # Get the datetime value and extract date
            dt_value: pd.Timestamp = df.index[i]  # type: ignore[assignment]
            # Convert to native Python datetime
            if pd.isna(dt_value):
                continue  # Skip invalid dates
            if hasattr(dt_value, "to_pydatetime"):
                py_dt = dt_value.to_pydatetime()
            else:
                py_dt = pd.Timestamp(dt_value).to_pydatetime()
            if py_dt is None:
                continue  # Skip invalid dates
            signal_date: date = py_dt.date()  # type: ignore[union-attr]

            sample = LabeledSample(
                ticker=ticker,
                date=signal_date,
                features=features,
                label=label,
                forward_return=forward_return,
                max_return=max_return,
                days_to_target=days_to_target,
            )
            samples.append(sample)

        except Exception:
            continue

    return samples


async def load_stock_data_concurrent(
    loader: SaptaDataLoader,
    tickers: list[str],
    period: str,
    min_rows: int,
    progress: Any = None,
    workers: int = 4,
) -> dict[str, pd.DataFrame]:
    """Load stock data concurrently using asyncio."""
    from asyncio import Semaphore

    semaphore = Semaphore(workers)

    async def fetch_ticker(ticker: str) -> tuple[str, pd.DataFrame | None]:
        async with semaphore:
            try:
                df = loader.get_historical_df(ticker, period=period)
                if df is not None and len(df) >= min_rows:
                    return ticker, df
                return ticker, None
            except Exception:
                return ticker, None

    # Use gather instead of TaskGroup for better compatibility
    tasks = [fetch_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results
    stock_data = {}
    for result in results:
        # Handle both successful results (tuple) and exceptions (BaseException)
        if isinstance(result, BaseException):
            continue
        if isinstance(result, tuple) and len(result) == 2:
            ticker, df = result
            if df is not None:
                stock_data[ticker] = df

    return stock_data


def calculate_label_stats(samples: list[LabeledSample]) -> dict[str, Any]:
    """Calculate label distribution statistics."""
    if not samples:
        return {}

    positive = sum(1 for s in samples if s.label == 1)
    negative = len(samples) - positive

    forward_returns = [s.forward_return for s in samples]
    max_returns = [s.max_return for s in samples]

    return {
        "total_samples": len(samples),
        "positive_samples": positive,
        "negative_samples": negative,
        "hit_rate": positive / len(samples) * 100,
        "avg_forward_return": float(np.mean(forward_returns)),
        "avg_max_return": float(np.mean(max_returns)),
        "std_forward_return": float(np.std(forward_returns)),
        "unique_tickers": len(set(s.ticker for s in samples)),
    }


def save_training_report(
    report: TrainingReport,
    output_dir: Path,
) -> str:
    """Save training report to JSON file."""
    report_path = output_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
    return str(report_path)


def main():
    parser = argparse.ArgumentParser(
        description="SAPTA ML Model Training Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic training
  python -m pulse.core.sapta.ml.train_model

  # Higher target gain, walk-forward validation
  python -m pulse.core.sapta.ml.train_model --target-gain 15 --walk-forward

  # Train on more stocks
  python -m pulse.core.sapta.ml.train_model --stocks 300 --period 3y

  # Resume previous training
  python -m pulse.core.sapta.ml.train_model --resume
        """,
    )

    # Target parameters
    parser.add_argument(
        "--target-gain",
        type=float,
        default=10.0,
        help="Target gain percentage (default: 10%%)",
    )
    parser.add_argument(
        "--target-days",
        type=int,
        default=20,
        help="Days to achieve target (default: 20)",
    )

    # Data parameters
    parser.add_argument(
        "--stocks",
        type=int,
        default=100,
        help="Number of stocks to use (default: 100)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="2y",
        help="Data period for yfinance (default: 2y)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=120,
        help="Window size for feature extraction (default: 120)",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=5,
        help="Step size for sliding window (default: 5)",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=120,
        help="Minimum rows required per stock (default: 120)",
    )

    # Training parameters
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set fraction (default: 0.2)",
    )
    parser.add_argument(
        "--walk-forward",
        action="store_true",
        help="Use walk-forward training (recommended)",
    )
    parser.add_argument(
        "--train-months",
        type=int,
        default=36,
        help="Training window months for walk-forward (default: 36)",
    )
    parser.add_argument(
        "--test-months",
        type=int,
        default=6,
        help="Test window months for walk-forward (default: 6)",
    )

    # Output parameters
    parser.add_argument(
        "--output-dir",
        type=str,
        default="pulse/core/sapta/data",
        help="Output directory for model files",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous training checkpoint",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Concurrent workers for data loading (default: 4)",
    )

    # Report options
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report only from existing model",
    )

    args = parser.parse_args()

    # Validate arguments
    if not 0.05 <= args.test_size <= 0.5:
        log.error("--test-size must be between 0.05 and 0.5")
        sys.exit(1)

    if not 5 <= args.window <= 365:
        log.error("--window must be between 5 and 365")
        sys.exit(1)

    if not 1 <= args.workers <= 10:
        log.error("--workers must be between 1 and 10")
        sys.exit(1)

    # Print header
    print("=" * 70)
    print("SAPTA ML Model Training")
    print("=" * 70)

    # Build config
    config = TrainingConfig(
        target_gain_pct=args.target_gain,
        target_days=args.target_days,
        window_size=args.window,
        step_size=args.step,
        test_size=args.test_size,
        walk_forward=args.walk_forward,
        train_months=args.train_months,
        test_months=args.test_months,
        stocks=args.stocks,
        period=args.period,
        min_rows=args.min_rows,
        output_dir=args.output_dir,
        resume=args.resume,
        workers=args.workers,
    )

    # Print configuration
    print("\n[Configuration]")
    print(f"  Target Gain:      {config.target_gain_pct}%")
    print(f"  Target Days:      {config.target_days}")
    print(f"  Window Size:      {config.window_size}")
    print(f"  Step Size:        {config.step_size}")
    print(f"  Data Period:      {config.period}")
    print(f"  Stocks to Load:   {config.stocks}")
    print(f"  Walk-Forward:     {'Yes' if config.walk_forward else 'No'}")
    if config.walk_forward:
        print(f"    Train Window:  {config.train_months} months")
        print(f"    Test Window:   {config.test_months} months")
    else:
        print(f"  Test Size:        {config.test_size * 100:.0f}%")
    print(f"  Output Directory: {config.output_dir}")
    print(f"  Workers:          {config.workers}")

    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle report-only mode
    if args.report_only:
        model_path = output_dir / "sapta_model.pkl"
        thresholds_path = output_dir / "thresholds.json"

        if not model_path.exists() or not thresholds_path.exists():
            log.error("Model files not found. Run training first.")
            sys.exit(1)

        # Load existing model info
        import joblib

        model = joblib.load(model_path)

        # Get feature names
        from pulse.core.sapta.ml.features import SaptaFeatureExtractor

        extractor = SaptaFeatureExtractor()
        feature_names = extractor.get_feature_names()

        # Generate feature importance report
        importance = dict(zip(feature_names, model.feature_importances_))
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

        report = TrainingReport(
            timestamp=datetime.now().isoformat(),
            config=asdict(config),
            data_stats={},
            label_distribution={},
            metrics={},
            thresholds={},
            feature_importance=dict(sorted_importance),
            model_info={},
            files_saved=[str(model_path), str(thresholds_path)],
        )

        report_path = save_training_report(report, output_dir)
        print(f"\nReport saved: {report_path}")

        print("\n[Top 15 Feature Importance]")
        for name, imp in sorted_importance[:15]:
            print(f"  {name}: {imp:.4f}")

        return

    # Initialize components
    sapta_config = SaptaConfig(
        target_gain_pct=config.target_gain_pct,
        target_days=config.target_days,
    )
    loader = SaptaDataLoader()
    labeler = SaptaLabeler(
        target_gain_pct=config.target_gain_pct,
        target_days=config.target_days,
    )

    # Initialize modules
    modules = {
        "absorption": SupplyAbsorptionModule(),
        "compression": CompressionModule(),
        "bb_squeeze": BBSqueezeModule(),
        "elliott": ElliottModule(),
        "time_projection": TimeProjectionModule(),
        "anti_distribution": AntiDistributionModule(),
    }

    # Get tickers
    all_tickers = loader.get_all_tickers()
    print("\n[Data Loading]")
    print(f"  Available stocks: {len(all_tickers)}")
    print(f"  Loading: {min(config.stocks, len(all_tickers))} stocks...")

    # Select tickers (prioritize liquid ones - first in list are typically more liquid)
    selected_tickers = all_tickers[: min(config.stocks, len(all_tickers))]

    # Try to load data with progress
    print("  Fetching historical data...")

    try:
        import asyncio

        stock_data = asyncio.run(
            load_stock_data_concurrent(
                loader,
                selected_tickers,
                config.period,
                config.min_rows,
                workers=config.workers,
            )
        )
    except ImportError:
        # Fallback to sequential loading if aiohttp not available
        log.info("aiohttp not available, using sequential loading")
        stock_data = loader.get_multiple_stocks(
            tickers=selected_tickers,
            period=config.period,
            min_rows=config.min_rows,
        )

    print(f"  Loaded: {len(stock_data)}/{len(selected_tickers)} stocks")

    if len(stock_data) < 10:
        log.error(f"Too few stocks loaded ({len(stock_data)}). Need at least 10.")
        sys.exit(1)

    # Generate samples
    print("\n[Sample Generation]")
    all_samples: list[LabeledSample] = []
    errors = []

    for idx, (ticker, df) in enumerate(stock_data.items()):
        try:
            samples = generate_samples(
                ticker=ticker,
                df=df,
                modules=modules,
                labeler=labeler,
                window_size=config.window_size,
                step_size=config.step_size,
            )
            all_samples.extend(samples)

            if (idx + 1) % 20 == 0:
                print(f"  Processed {idx + 1}/{len(stock_data)} stocks, {len(all_samples)} samples")

        except Exception as e:
            errors.append((ticker, str(e)))
            continue

    print(f"  Total samples: {len(all_samples)}")

    if errors:
        print(f"  Errors: {len(errors)} stocks failed")
        for ticker, err in errors[:5]:
            print(f"    - {ticker}: {err}")
        if len(errors) > 5:
            print(f"    ... and {len(errors) - 5} more")

    if len(all_samples) < 100:
        log.error(f"Not enough samples ({len(all_samples)}). Need at least 100.")
        sys.exit(1)

    # Calculate label statistics
    label_stats = calculate_label_stats(all_samples)
    print("\n[Label Distribution]")
    print(f"  Total Samples:   {label_stats['total_samples']}")
    print(f"  Positive (hit):  {label_stats['positive_samples']} ({label_stats['hit_rate']:.1f}%)")
    print(
        f"  Negative (miss): {label_stats['negative_samples']} ({100 - label_stats['hit_rate']:.1f}%)"
    )
    print(f"  Unique Tickers:  {label_stats['unique_tickers']}")
    print(f"  Avg Forward Return: {label_stats['avg_forward_return']:.2f}%")
    print(f"  Avg Max Return:     {label_stats['avg_max_return']:.2f}%")

    # Train model
    print("\n[Training Model]")
    trainer = SaptaTrainer(
        config=sapta_config,
        model_dir=config.output_dir,
    )

    if config.walk_forward:
        print("  Mode: Walk-Forward Training")
        result = trainer.walk_forward_train(
            all_samples,
            train_months=config.train_months,
            test_months=config.test_months,
        )
    else:
        print(f"  Mode: Simple Split ({config.test_size * 100:.0f}% test)")
        result = trainer.train(
            all_samples,
            test_size=config.test_size,
        )

    if not result:
        log.error("Training failed!")
        sys.exit(1)

    # Print results
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)

    print("\n[Model Files]")
    print(f"  Model:     {result.model_path}")
    print(f"  Thresholds: {result.thresholds_path}")

    print("\n[Metrics]")
    for metric, value in result.metrics.items():
        print(f"  {metric}: {value:.4f}")

    print("\n[Learned Thresholds]")
    print(f"  PRE-MARKUP:  >= {result.model_info.threshold_pre_markup:.1f}")
    print(f"  SIAP:        >= {result.model_info.threshold_siap:.1f}")
    print(f"  WATCHLIST:   >= {result.model_info.threshold_watchlist:.1f}")

    # Feature importance
    sorted_importance = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)

    print("\n[Top 15 Important Features]")
    for name, importance in sorted_importance[:15]:
        print(f"  {name}: {importance:.4f}")

    # Save training report
    report = TrainingReport(
        timestamp=datetime.now().isoformat(),
        config=asdict(config),
        data_stats={
            "stocks_loaded": len(stock_data),
            "stocks_requested": len(selected_tickers),
            "period": config.period,
        },
        label_distribution=label_stats,
        metrics=result.metrics,
        thresholds={
            "pre_markup": result.model_info.threshold_pre_markup,
            "siap": result.model_info.threshold_siap,
            "watchlist": result.model_info.threshold_watchlist,
        },
        feature_importance=dict(sorted_importance),
        model_info=asdict(result.model_info),
        files_saved=[result.model_path, result.thresholds_path],
    )

    report_path = save_training_report(report, output_dir)
    print("\n[Report]")
    print(f"  Saved: {report_path}")

    # Verify model can be loaded
    try:
        import joblib

        test_model = joblib.load(result.model_path)
        print("\n[Verification]")
        print("  Model loaded successfully")
        # feature_names_in_ may not be set if X had non-string feature names
        if hasattr(test_model, "feature_names_in_") and test_model.feature_names_in_ is not None:
            print(f"  Feature count: {len(test_model.feature_names_in_)}")
        else:
            print(f"  Feature count: {test_model.n_features_in_}")
    except Exception as e:
        print(f"\n[WARNING] Model verification failed: {e}")

    print("\n" + "=" * 70)
    print("SAPTA Model Training Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
