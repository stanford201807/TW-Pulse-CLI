"""診斷回測中「站上年線」邏輯是否正確觸發"""

import asyncio
from datetime import datetime, timedelta
from pulse.core.backtest.engine import BacktestEngine
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy

async def run_debug_backtest():
    """執行帶診斷的回測"""
    
    print("=" * 70)
    print("執行 2025-05-01 至 2025-07-01 的診斷回測")
    print("=" * 70)
    
    strategy = FarmerPlantingStrategy()
    
    engine = BacktestEngine(
        strategy=strategy,
        ticker="2330",
        start_date=datetime(2025, 5, 1),
        end_date=datetime(2025, 7, 1),
        initial_cash=1_000_000,
    )
    
    # 手動執行回測並輸出診斷資訊
    df = await engine.fetcher.fetch_history(
        engine.ticker, start=engine.start_date, end=engine.end_date
    )
    
    print(f"\n載入 {len(df)} 筆數據")
    
    indicators_df = await engine.analyzer.calculate_indicators(df)
    print(f"計算技術指標完成")
    
    # 檢查是否有 MA_200
    if 'MA_200' in indicators_df.columns:
        print(f"✅ MA_200 欄位存在")
        print(f"   MA_200 範圍: {indicators_df['MA_200'].min():.2f} ~ {indicators_df['MA_200'].max():.2f}")
    else:
        print(f"❌ MA_200 欄位不存在！")
        print(f"   可用欄位: {list(indicators_df.columns)}")
        return
    
    # 初始化策略
    await strategy.initialize(engine.ticker, engine.initial_cash, {})
    
    print(f"\n診斷每日狀態：")
    print("-" * 70)
    
    for i in range(len(indicators_df)):
        row = indicators_df.iloc[i]
        date = row.name
        close = row['close']
        ma200 = row.get('MA_200')
        
        # 準備數據
        bar = {
            "date": date,
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": close,
            "volume": row.get("volume", 0),
        }
        indicators = {
            "rsi_14": row.get("RSI_14"),
            "ma_200": ma200,
        }
        
        prev_close = strategy.prev_close
        positions = strategy.state.positions
        
        # 檢查站上年線條件
        condition_met = (
            positions == 0 and 
            ma200 is not None and 
            prev_close > 0 and 
            prev_close <= ma200 and 
            close > ma200
        )
        
        # 只輸出可能觸發的日期
        if condition_met or (positions == 0 and ma200 and prev_close > 0):
            status = "✅ 觸發" if condition_met else "❌ 不觸發"
            reason = ""
            if not condition_met:
                if positions != 0:
                    reason = f"持倉非0({positions})"
                elif prev_close <= 0:
                    reason = "prev_close未初始化"
                elif prev_close > ma200:
                    reason = f"前收{prev_close:.0f} > MA200{ma200:.0f}"
                elif close <= ma200:
                    reason = f"今收{close:.0f} <= MA200{ma200:.0f}"
            
            print(f"{date.date()} | 前收: {prev_close:.0f} | 今收: {close:.0f} | MA200: {ma200:.0f} | {status} {reason}")
        
        # 執行策略
        signal = await strategy.on_bar(bar, indicators)
        
        if signal:
            print(f"  ➡️ 訊號: {signal.action.value} | {signal.reason}")

if __name__ == "__main__":
    asyncio.run(run_debug_backtest())
