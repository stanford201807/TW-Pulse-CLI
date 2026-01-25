"""Stock list fetcher for retrieving and saving Taiwan stock lists."""

import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from FinMind.data import DataLoader

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class StockListFetcher:
    """Fetch and manage Taiwan stock lists using FinMind."""

    def __init__(self, token: str = ""):
        """
        Initialize the fetcher.

        Args:
            token: FinMind API token (optional)
        """
        self.dl = DataLoader()
        if token:
            self.dl.login_by_token(api_token=token)
        self._df_cache: Optional[pd.DataFrame] = None

    def _fetch_all_stocks(self) -> pd.DataFrame:
        """Fetch all Taiwan stock info."""
        if self._df_cache is None:
            log.info("Fetching stock list from FinMind...")
            self._df_cache = self.dl.taiwan_stock_info()
        return self._df_cache

    def get_twse_stocks(self) -> List[Dict]:
        """Get all TWSE (上市) stocks."""
        df = self._fetch_all_stocks()
        if df is None or df.empty:
            return []
        
        # Filter for TWSE stocks
        mask = (df["type"] == "twse") & (df["industry_category"].notna()) & (df["industry_category"] != "")
        twse_df = df[mask].copy()
        return twse_df.to_dict("records")

    def get_tpex_stocks(self) -> List[Dict]:
        """Get all TPEx (上櫃) stocks."""
        df = self._fetch_all_stocks()
        if df is None or df.empty:
            return []
        
        # Filter for TPEx stocks
        mask = (df["type"] == "tpex") & (df["industry_category"].notna()) & (df["industry_category"] != "")
        tpex_df = df[mask].copy()
        return tpex_df.to_dict("records")

    def save_all_for_main_program(self) -> Dict[str, str]:
        """
        Save all necessary stock list files to data/ directory.
        
        Returns:
            Dictionary of generated file paths.
        """
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        generated_files = {}

        # 1. Fetch data
        twse = self.get_twse_stocks()
        tpex = self.get_tpex_stocks()
        
        if not twse and not tpex:
            log.warning("No stock data fetched!")
            return {}

        # 2. Save JSON (Unified list)
        json_path = data_dir / "stock_list.json"
        all_stocks = twse + tpex
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_stocks, f, ensure_ascii=False, indent=2)
        generated_files["json"] = str(json_path)

        # 3. Save Ticker Lists (Simple list of strings)
        # Listed (TWSE)
        if twse:
            listed_codes = sorted([s["stock_id"] for s in twse])
            listed_path = data_dir / "tw_codes_listed.json"
            with open(listed_path, "w", encoding="utf-8") as f:
                json.dump(listed_codes, f, ensure_ascii=False)
            generated_files["listed_json"] = str(listed_path)

        # OTC (TPEx)
        if tpex:
            otc_codes = sorted([s["stock_id"] for s in tpex])
            otc_path = data_dir / "tw_codes_otc.json"
            with open(otc_path, "w", encoding="utf-8") as f:
                json.dump(otc_codes, f, ensure_ascii=False)
            generated_files["otc_json"] = str(otc_path)

        # 4. Save CSVs
        if twse:
            twse_csv_path = data_dir / "twse_stocks.csv"
            pd.DataFrame(twse).to_csv(twse_csv_path, index=False, encoding="utf-8-sig")
            generated_files["twse_csv"] = str(twse_csv_path)

        if tpex:
            tpex_csv_path = data_dir / "tpex_stocks.csv"
            pd.DataFrame(tpex).to_csv(tpex_csv_path, index=False, encoding="utf-8-sig")
            generated_files["tpex_csv"] = str(tpex_csv_path)

        return generated_files
