"""診斷完整回測的 MA200 計算問題"""

import asyncio
from datetime import datetime, timedelta
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.analysis.technical import TechnicalAnalyzer

async def check_ma200_calculation():
    """檢查不同回測範圍的 MA200 計算情況"""
    
    print("=" * 70)
    print("檢查 MA200 計算問題")
    print("=" * 70)
    
    fetcher = YFinanceFetcher()
    analyzer = TechnicalAnalyzer()
    
    # 完整 5 年回測
    print("\n【5 年回測（2021-01-26 ~ 2026-01-25）】")
    start_5y = datetime(2021, 1, 26)
    end_5y = datetime(2026, 1, 25)
    
    df_5y = await fetcher.fetch_history("2330", start=start_5y, end=end_5y)
    print(f"數據筆數: {len(df_5y)}")
    
    indicators_5y = await analyzer.calculate_indicators(df_5y)
    
    # 檢查 MA200
    ma200_valid = indicators_5y['MA_200'].notna()
    first_valid = indicators_5y[ma200_valid].index[0] if ma200_valid.any() else None
    
    print(f"MA_200 有效筆數: {ma200_valid.sum()} / {len(indicators_5y)}")
    if first_valid:
        print(f"MA_200 首個有效日期: {first_valid.date()}")
    
    # 檢查 2025-06 的 MA200
    print("\n【2025-06 期間的 MA200】")
    june_2025 = indicators_5y[
        (indicators_5y.index >= '2025-06-01') & 
        (indicators_5y.index <= '2025-06-30')
    ]
    
    if not june_2025.empty:
        print(f"2025-06 數據筆數: {len(june_2025)}")
        print(f"MA200 範圍: {june_2025['MA_200'].min():.2f} ~ {june_2025['MA_200'].max():.2f}")
        
        # 檢查站上年線機會
        print("\n站上年線機會檢查：")
        prev_close = None
        for idx in june_2025.head(15).index:
            row = june_2025.loc[idx]
            close = row['close']
            ma200 = row['MA_200']
            
            if prev_close is not None:
                cross = "⬆️ 站上年線" if (prev_close <= ma200 and close > ma200) else ""
                print(f"  {idx.date()} | 前收: {prev_close:.0f} | 今收: {close:.0f} | MA200: {ma200:.0f} {cross}")
            
            prev_close = close
    else:
        print("❌ 無法獲取 2025-06 數據")

if __name__ == "__main__":
    asyncio.run(check_ma200_calculation())
