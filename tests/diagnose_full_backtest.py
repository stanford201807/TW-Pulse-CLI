"""完整回測診斷 - 修復時區問題"""

import asyncio
from datetime import datetime
import pandas as pd
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.base import SignalAction

async def run_full_debug():
    """執行完整回測並診斷 2025-06 前後狀態"""
    
    print("=" * 70)
    print("完整回測診斷（5 年）")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    # 載入數據
    df = await engine.fetcher.fetch_history(
        engine.ticker, start=engine.start_date, end=engine.end_date
    )
    print(f"載入 {len(df)} 筆數據")
    
    # 計算指標
    indicators_df = await engine.analyzer.calculate_indicators(df)
    print(f"技術指標計算完成")
    
    # 初始化策略
    await strategy.initialize(engine.ticker, engine.initial_cash, {})
    
    # 只關注 2025-05-15 到 2025-06-20 期間
    print("\n" + "=" * 70)
    print("診斷 2025-05-15 ~ 2025-06-20 期間")
    print("=" * 70)
    
    signals = []
    
    for i in range(len(indicators_df)):
        row = indicators_df.iloc[i]
        date = row.name
        close = row['close']
        open_price = row['open']
        ma200 = row.get('MA_200')
        rsi = row.get('RSI_14')
        
        bar = {
            "date": date,
            "open": open_price,
            "high": row["high"],
            "low": row["low"],
            "close": close,
            "volume": row.get("volume", 0),
        }
        indicators = {
            "rsi_14": rsi,
            "ma_200": ma200,
        }
        
        # 使用字串比較判斷日期範圍
        date_str = str(date.date()) if hasattr(date, 'date') else str(date)[:10]
        in_focus_period = date_str >= '2025-05-15' and date_str <= '2025-06-20'
        
        if in_focus_period:
            prev_close = strategy.prev_close
            positions = strategy.state.positions
            
            # 輸出狀態
            ma200_str = f"{ma200:.0f}" if ma200 and pd.notna(ma200) else "NaN"
            print(f"{date_str} | 持倉:{positions} | 前收:{prev_close:.0f} | 今收:{close:.0f} | MA200:{ma200_str}", end="")
        
        # 執行策略
        signal = await strategy.on_bar(bar, indicators)
        
        if in_focus_period:
            if signal:
                print(f" | ➡️ {signal.action.value}: {signal.reason}")
                signals.append((date, signal))
            else:
                print()
    
    print("\n" + "=" * 70)
    print(f"期間內訊號總數: {len(signals)}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_full_debug())
