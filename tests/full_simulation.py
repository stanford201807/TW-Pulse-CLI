"""完整模擬回測引擎行為，包含狀態更新"""

import asyncio
import pandas as pd
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.base import SignalAction
from pulse.core.backtest.position import PositionManager

async def full_simulation():
    """完整模擬回測引擎，包含狀態更新"""
    
    print("=" * 70)
    print("完整模擬回測（包含狀態更新）")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2026, 1, 25),
        initial_cash=1_000_000,
    )
    
    df = await engine.fetcher.fetch_history(engine.ticker, start=engine.start_date, end=engine.end_date)
    indicators_df = await engine.analyzer.calculate_indicators(df)
    
    shares_per_position = 1000
    await strategy.initialize(engine.ticker, engine.initial_cash, {})
    position_manager = PositionManager(engine.initial_cash, shares_per_position)
    
    print("\n逐日執行（只顯示 2025-06-05 之後）:\n")
    
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
        
        # 只在 2025-06-05 之後輸出
        show_output = date_str >= '2025-06-04' and date_str <= '2025-06-20'
        
        if show_output:
            print(f"\n{date_str}:")
            print(f"  策略狀態: 持倉={strategy.state.positions}, 基準價={strategy.state.base_price:.0f}")
            print(f"  今日數據: 收盤={close:.0f}, 開盤={open_price:.0f}")
        
        # 生成交易訊號
        signal = await strategy.on_bar(bar, indicators)
        
        # 執行交易（模擬回測引擎）
        if signal and signal.action != SignalAction.HOLD:
            action_str = signal.action.value
            success = position_manager.execute_trade(
                date=date,
                action=action_str,
                quantity=signal.quantity,
                price=signal.price,
                reason=signal.reason,
            )
            
            if success:
                # 更新策略狀態
                quantity_change = signal.quantity if signal.action == SignalAction.BUY else -signal.quantity
                strategy.state.update_position(quantity_change, signal.price, shares_per_position)
                
                if show_output:
                    print(f"  ➡️ 訊號: {action_str} | {signal.reason}")
                    print(f"  更新後: 持倉={strategy.state.positions}, 基準價={strategy.state.base_price:.0f}")
            else:
                if show_output:
                    print(f"  ❌ 交易失敗: {signal.reason}")

if __name__ == "__main__":
    asyncio.run(full_simulation())
