"""診斷加碼交易失敗原因"""

import asyncio
from datetime import datetime
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.base import SignalAction
from pulse.core.backtest.position import PositionManager

async def diagnose_trade_failure():
    """診斷交易失敗原因"""
    
    print("=" * 70)
    print("診斷加碼交易失敗原因")
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
    
    print(f"\n初始資金: NT$ {position_manager.cash:,.0f}")
    print(f"每份股數: {shares_per_position:,}")
    
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
        
        signal = await strategy.on_bar(bar, indicators)
        
        if signal and signal.action != SignalAction.HOLD:
            action_str = signal.action.value
            
            # 計算所需金額
            shares = signal.quantity * shares_per_position
            amount = signal.price * shares
            
            # 只在 2025-06-05 之後輸出
            if date_str >= '2025-06-04' and date_str <= '2025-06-15':
                print(f"\n{date_str} {action_str}:")
                print(f"  訊號: {signal.quantity}份 @ NT$ {signal.price:,.0f}")
                print(f"  所需金額: NT$ {amount:,.0f}")
                print(f"  可用現金: NT$ {position_manager.cash:,.0f}")
                print(f"  現金足夠: {amount <= position_manager.cash}")
            
            success = position_manager.execute_trade(
                date=date, action=action_str, quantity=signal.quantity,
                price=signal.price, reason=signal.reason,
            )
            
            if success:
                quantity_change = signal.quantity if signal.action == SignalAction.BUY else -signal.quantity
                strategy.state.update_position(quantity_change, signal.price, shares_per_position)
                
                if date_str >= '2025-06-04' and date_str <= '2025-06-15':
                    print(f"  ✅ 交易成功")
                    print(f"  剩餘現金: NT$ {position_manager.cash:,.0f}")
            else:
                if date_str >= '2025-06-04' and date_str <= '2025-06-15':
                    print(f"  ❌ 交易失敗")

if __name__ == "__main__":
    asyncio.run(diagnose_trade_failure())
