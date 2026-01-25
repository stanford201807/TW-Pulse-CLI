"""精確診斷 2025-06-02 後無交易問題"""

import asyncio
import pandas as pd
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.base import SignalAction

async def debug_june():
    """精確診斷 6 月初的狀態"""
    
    print("=" * 70)
    print("精確診斷 2025-06-01 ~ 2025-06-10")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    df = await engine.fetcher.fetch_history(
        engine.ticker, start=engine.start_date, end=engine.end_date
    )
    indicators_df = await engine.analyzer.calculate_indicators(df)
    await strategy.initialize(engine.ticker, engine.initial_cash, {})
    
    print(f"\n逐日執行策略並追蹤狀態：\n")
    
    for i in range(len(indicators_df)):
        row = indicators_df.iloc[i]
        date = row.name
        date_str = str(date.date()) if hasattr(date, 'date') else str(date)[:10]
        
        close = row['close']
        open_price = row['open']
        ma200 = row.get('MA_200')
        rsi = row.get('RSI_14')
        
        bar = {"date": date, "open": open_price, "high": row["high"], 
               "low": row["low"], "close": close, "volume": row.get("volume", 0)}
        indicators = {"rsi_14": rsi, "ma_200": ma200}
        
        # 只看 2025-06-01 ~ 06-10
        if date_str >= '2025-06-01' and date_str <= '2025-06-10':
            prev = strategy.prev_close
            pos = strategy.state.positions
            ma_str = f"{ma200:.0f}" if pd.notna(ma200) else "NaN"
            
            # 詳細打印條件
            print(f"\n{date_str}:")
            print(f"  持倉: {pos}, prev_close: {prev:.0f}, 今收: {close:.0f}, MA200: {ma_str}")
            
            # 檢查站上年線條件
            if pos == 0 and pd.notna(ma200) and prev > 0:
                cond1 = prev <= ma200
                cond2 = close > ma200
                print(f"  站上年線檢查: prev({prev:.0f}) <= MA200({ma200:.0f})? {cond1}")
                print(f"  站上年線檢查: close({close:.0f}) > MA200({ma200:.0f})? {cond2}")
                if cond1 and cond2:
                    print(f"  ✅ 應該觸發買進！")
        
        # 執行策略
        signal = await strategy.on_bar(bar, indicators)
        
        if date_str >= '2025-06-01' and date_str <= '2025-06-10':
            if signal:
                print(f"  ➡️ 訊號: {signal.action.value} | {signal.reason}")

if __name__ == "__main__":
    asyncio.run(debug_june())
