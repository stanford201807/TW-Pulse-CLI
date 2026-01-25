"""測試 YFinanceFetcher 對回測的支援

測試 YFinanceFetcher 是否能正確支援 start/end 參數用於回測。
"""
import pytest
from datetime import datetime, timedelta
from pulse.core.data.yfinance import YFinanceFetcher


class TestYFinanceBacktest:
    """YFinance 回測支援測試"""
    
    @pytest.mark.asyncio
    async def test_fetch_history_with_start_end(self):
        """測試使用 start/end 參數獲取歷史數據"""
        fetcher = YFinanceFetcher()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        df = await fetcher.fetch_history("2330", start=start_date, end=end_date)
        
        assert df is not None, "應該成功獲取歷史數據"
        assert len(df) > 0, "數據不應為空"
        assert "close" in df.columns, "應包含 close 欄位"
        
    @pytest.mark.asyncio
    async def test_fetch_history_with_period(self):
        """測試使用 period 參數（向後兼容）"""
        fetcher = YFinanceFetcher()
        
        df = await fetcher.fetch_history("2330", period="1y")
        
        assert df is not None, "應該成功獲取歷史數據"
        assert len(df) > 0, "數據不應為空"
        
    @pytest.mark.asyncio
    async def test_fetch_history_default(self):
        """測試預設行為（無參數）"""
        fetcher = YFinanceFetcher()
        
        # 不傳入任何參數時應使用預設 1 年
        df = await fetcher.fetch_history("2330")
        
        assert df is not None, "應該成功獲取歷史數據"
        assert len(df) > 0, "數據不應為空"
    
    def test_get_history_df_with_start_end(self):
        """測試 get_history_df 使用 start/end 參數"""
        fetcher = YFinanceFetcher()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 個月
        
        df = fetcher.get_history_df("2330", start=start_date, end=end_date)
        
        assert df is not None, "應該成功獲取歷史數據"
        assert len(df) > 0, "數據不應為空"
    
    def test_get_history_df_with_period(self):
        """測試 get_history_df 使用 period 參數（向後兼容）"""
        fetcher = YFinanceFetcher()
        
        df = fetcher.get_history_df("2330", period="6mo")
        
        assert df is not None, "應該成功獲取歷史數據"
        assert len(df) > 0, "數據不應為空"


if __name__ == "__main__":
    import asyncio
    
    print("執行 YFinance 回測支援測試...\n")
    
    # 執行測試
    tester = TestYFinanceBacktest()
    
    print("測試 1: fetch_history 使用 start/end 參數")
    asyncio.run(tester.test_fetch_history_with_start_end())
    print("✅ 通過\n")
    
    print("測試 2: fetch_history 使用 period 參數")
    asyncio.run(tester.test_fetch_history_with_period())
    print("✅ 通過\n")
    
    print("測試 3: fetch_history 預設行為")
    asyncio.run(tester.test_fetch_history_default())
    print("✅ 通過\n")
    
    print("測試 4: get_history_df 使用 start/end 參數")
    tester.test_get_history_df_with_start_end()
    print("✅ 通過\n")
    
    print("測試 5: get_history_df 使用 period 參數")
    tester.test_get_history_df_with_period()
    print("✅ 通過\n")
    
    print("🎉 所有測試通過！")
