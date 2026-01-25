#!/usr/bin/env python
"""Standalone script to fetch Taiwan stock code lists.

Usage:
    python scripts/fetch_stock_list.py [--json] [--csv] [--twse] [--tpex]

Examples:
    # Fetch all stocks and save to JSON
    python scripts/fetch_stock_list.py --json

    # Fetch only TWSE stocks
    python scripts/fetch_stock_list.py --twse

    # Fetch both markets and save to CSV
    python scripts/fetch_stock_list.py --csv

    # Get tickers only (for use in other programs)
    python scripts/fetch_stock_list.py --tickers
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch Taiwan stock code lists (上市/上櫃股票代碼清單)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Save to JSON file (data/stock_list.json)"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save to CSV files (data/twse_stocks.csv, data/tpex_stocks.csv)",
    )
    parser.add_argument("--twse", action="store_true", help="Only fetch TWSE (上市) stocks")
    parser.add_argument("--tpex", action="store_true", help="Only fetch TPEx (上櫃) stocks")
    parser.add_argument(
        "--tickers",
        action="store_true",
        help="Output only ticker codes (one per line)",
    )

    args = parser.parse_args()

    # Import after path setup
    from dotenv import load_dotenv

    load_dotenv()

    from pulse.core.data.stock_list_fetcher import StockListFetcher

    import os

    token = os.getenv("FINMIND_TOKEN", "") or ""

    fetcher = StockListFetcher(token=token)

    try:
        # Save all files for main program
        print("Generating all stock list files for main program...")
        files = fetcher.save_all_for_main_program()

        print("\n[OK] Generated files:")
        for name, path in files.items():
            print(f"   - {path}")

        # Also show summary
        twse_stocks = fetcher.get_twse_stocks()
        tpex_stocks = fetcher.get_tpex_stocks()
        print(f"\n上市 (TWSE): {len(twse_stocks)} stocks")
        print(f"上櫃 (TPEx): {len(tpex_stocks)} stocks")
        print(f"總計: {len(twse_stocks) + len(tpex_stocks)} stocks")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()