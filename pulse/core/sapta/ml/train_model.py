#!/usr/bin/env python3
"""
SAPTA Model Training Script.

Train SAPTA ML model using historical data from emitens.db.

Usage:
    python -m pulse.core.sapta.ml.train_model
    
    # Or with options
    python -m pulse.core.sapta.ml.train_model --stocks 100 --walk-forward
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from pulse.core.sapta.ml.data_loader import SaptaDataLoader
from pulse.core.sapta.ml.labeling import LabeledSample, SaptaLabeler
from pulse.core.sapta.ml.trainer import SaptaTrainer
from pulse.core.sapta.models import SaptaConfig
from pulse.core.sapta.modules import (
    AntiDistributionModule,
    BBSqueezeModule,
    CompressionModule,
    ElliottModule,
    SupplyAbsorptionModule,
    TimeProjectionModule,
)


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
            window_df = df.iloc[i - window_size:i].copy()

            if len(window_df) < window_size:
                continue

            # Extract features at this point
            features = extract_features_from_df(window_df, modules)

            # Get label from labeled_df at position i
            row = labeled_df.iloc[i]
            label = int(row.get('hit_target', 0))
            forward_return = float(row.get('forward_return', 0))
            max_return = float(row.get('max_forward_return', 0))
            days_to_target = int(row['days_to_target']) if pd.notna(row.get('days_to_target')) else None

            signal_date = df.index[i].date() if hasattr(df.index[i], 'date') else df.index[i]

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


def main():
    parser = argparse.ArgumentParser(description="Train SAPTA ML Model")
    parser.add_argument("--stocks", type=int, default=100, help="Number of stocks to use")
    parser.add_argument("--walk-forward", action="store_true", help="Use walk-forward training")
    parser.add_argument("--window", type=int, default=120, help="Window size for features")
    parser.add_argument("--step", type=int, default=10, help="Step size for sliding window")
    parser.add_argument("--db", type=str, default=None, help="Path to emitens.db")
    args = parser.parse_args()

    print("=" * 60)
    print("SAPTA Model Training")
    print("=" * 60)

    # Initialize components
    config = SaptaConfig()
    loader = SaptaDataLoader(args.db)
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

    print("\nConfiguration:")
    print(f"  Target Gain: {config.target_gain_pct}%")
    print(f"  Target Days: {config.target_days}")
    print(f"  Window Size: {args.window}")
    print(f"  Step Size: {args.step}")
    print(f"  Walk-Forward: {args.walk_forward}")

    # Load data
    stats = loader.get_statistics()
    print("\nDatabase Stats:")
    print(f"  Total Stocks: {stats['total_stocks']}")
    print(f"  Date Range: {stats['start_date']} to {stats['end_date']}")

    # Get tickers (prioritize liquid stocks)
    all_tickers = loader.get_all_tickers()
    tickers = all_tickers[:args.stocks]

    print(f"\nLoading data for {len(tickers)} stocks...")

    # Generate samples
    all_samples: list[LabeledSample] = []
    processed = 0

    for ticker in tickers:
        try:
            df = loader.get_historical_df(ticker)

            if df is None or len(df) < args.window + config.target_days:
                continue

            samples = generate_samples(
                ticker=ticker,
                df=df,
                modules=modules,
                labeler=labeler,
                window_size=args.window,
                step_size=args.step,
            )

            all_samples.extend(samples)
            processed += 1

            if processed % 20 == 0:
                print(f"  Processed {processed}/{len(tickers)} stocks, {len(all_samples)} samples")

        except Exception as e:
            print(f"  Error processing {ticker}: {e}")
            continue

    print(f"\nTotal samples generated: {len(all_samples)}")

    if len(all_samples) < 100:
        print("ERROR: Not enough samples for training!")
        return

    # Calculate label distribution
    positive = sum(1 for s in all_samples if s.label == 1)
    negative = len(all_samples) - positive
    print(f"  Positive (hit target): {positive} ({positive/len(all_samples)*100:.1f}%)")
    print(f"  Negative: {negative} ({negative/len(all_samples)*100:.1f}%)")

    # Train model
    print("\nTraining model...")
    trainer = SaptaTrainer(config=config)

    if args.walk_forward:
        result = trainer.walk_forward_train(all_samples)
    else:
        result = trainer.train(all_samples)

    if result:
        print("\n" + "=" * 60)
        print("Training Complete!")
        print("=" * 60)
        print(f"\nModel saved: {result.model_path}")
        print(f"Thresholds saved: {result.thresholds_path}")
        print("\nMetrics:")
        for metric, value in result.metrics.items():
            print(f"  {metric}: {value:.4f}")

        print("\nLearned Thresholds:")
        print(f"  PRE-MARKUP: >= {result.model_info.threshold_pre_markup:.1f}")
        print(f"  SIAP: >= {result.model_info.threshold_siap:.1f}")
        print(f"  WATCHLIST: >= {result.model_info.threshold_watchlist:.1f}")

        print("\nTop 10 Important Features:")
        sorted_importance = sorted(
            result.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        for name, importance in sorted_importance:
            print(f"  {name}: {importance:.4f}")
    else:
        print("ERROR: Training failed!")


if __name__ == "__main__":
    main()
