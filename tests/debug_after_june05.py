"""診斷 2025-06-05 買進後為何沒有後續交易"""

import asyncio
import pandas as pd
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy

async def debug_after_june05():
    """診斷 2025-06-05 之後的狀態"""
    
    print("=" * 70)
    print("診斷 2025-06-05 買進後的交易狀況")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    engine = BacktestEngine(
        strategy=strategy, ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    df = await engine.fetcher.fetch_history(engine.ticker, start=engine.start_date, end=engine.end_date)
    indicators_df = await engine.analyzer.calculate_indicators(df)
    await strategy.initialize(engine.ticker, engine.initial_cash, {})
    
    print("\n逐日執行策略...\n")
    
    # 追蹤 2025-06-05 之後的狀態
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
        
        # 只看 2025-06-05 之後
        if date_str >= '2025-06-05' and date_str <= '2025-07-15':
            positions = strategy.state.positions
            base_price = strategy.state.base_price
            peak_price = strategy.state.peak_price
            
            # 檢查各種條件
            add_level = base_price * 1.03 if base_price > 0 else 0
            reduce_level = base_price * 0.97 if base_price > 0 else 0
            stop_price = peak_price * 0.80 if peak_price > 0 else 0
            defense_level = ma200 * 0.96 if pd.notna(ma200) else 0
            ma200_str = f"{ma200:.0f}" if pd.notna(ma200) else "NaN"
            
            print(f"\n{date_str}:")
            print(f"  持倉: {positions} | 基準價: {base_price:.0f} | 波段高點: {peak_price:.0f}")
            print(f"  今收: {close:.0f} | 開盤: {open_price:.0f} | MA200: {ma200_str}")
            if positions > 0:
                print(f"  加碼條件: 收盤({close:.0f}) >= {add_level:.0f}? {close >= add_level}")
                print(f"  減碼條件: 收盤({close:.0f}) <= {reduce_level:.0f}? {close <= reduce_level}")
                print(f"  停利條件: 收盤({close:.0f}) <= {stop_price:.0f}? {close <= stop_price}")
                print(f"  防禦條件: 收盤({close:.0f}) <= {defense_level:.0f}? {close <= defense_level}")
        
        # 執行策略
        signal = await strategy.on_bar(bar, indicators)
        
        if date_str >= '2025-06-05' and date_str <= '2025-07-15':
            if signal:
                print(f"  ➡️ 訊號: {signal.action.value} | {signal.reason}")

if __name__ == "__main__":
    asyncio.run(debug_after_june05())
