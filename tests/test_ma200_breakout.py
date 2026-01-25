"""測試站上年線啟動機制

驗證修改後的策略是否正確觸發「站上年線」買進訊號
"""

import asyncio
from datetime import datetime
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.base import SignalAction

async def test_ma200_breakout():
    """測試站上年線啟動機制"""
    
    print("=" * 60)
    print("測試「站上年線啟動」機制")
    print("=" * 60)
    
    # 建立策略實例
    strategy = FarmerPlantingStrategy()
    await strategy.initialize("2330", 1_000_000, {})
    
    # 模擬 MA200 = 500
    ma200 = 500.0
    
    # === 測試 1：價格在年線下方 ===
    print("\n測試 1: 價格在年線下方（收盤 490）")
    bar1 = {
        "date": datetime(2023, 1, 10),
        "open": 485,
        "high": 495,
        "low": 480,
        "close": 490,
        "volume": 10000
    }
    indicators1 = {"rsi_14": 50, "ma_200": ma200}
    
    signal1 = await strategy.on_bar(bar1, indicators1)
    print(f"  prev_close 更新為: {strategy.prev_close}")
    print(f"  訊號: {signal1}")
    
    # === 測試 2：價格站上年線（觸發買進） ===
    print("\n測試 2: 價格站上年線（收盤 510）")
    bar2 = {
        "date": datetime(2023, 1, 11),
        "open": 495,
        "high": 515,
        "low": 490,
        "close": 510,
        "volume": 15000
    }
    indicators2 = {"rsi_14": 55, "ma_200": ma200}
    
    signal2 = await strategy.on_bar(bar2, indicators2)
    print(f"  prev_close: {strategy.prev_close}")
    
    if signal2:
        print(f"  ✅ 訊號觸發: {signal2.action.value}")
        print(f"  原因: {signal2.reason}")
    else:
        print(f"  ❌ 未觸發訊號")
    
    # === 測試 3：已在年線上方（不應重複觸發） ===
    print("\n測試 3: 持續在年線上方（收盤 520）")
    # 重置策略（模擬已持倉的情況）
    strategy2 = FarmerPlantingStrategy()
    await strategy2.initialize("2330", 1_000_000, {})
    strategy2.prev_close = 510  # 前一日已在年線上
    
    bar3 = {
        "date": datetime(2023, 1, 12),
        "open": 512,
        "high": 525,
        "low": 508,
        "close": 520,
        "volume": 12000
    }
    indicators3 = {"rsi_14": 60, "ma_200": ma200}
    
    signal3 = await strategy2.on_bar(bar3, indicators3)
    print(f"  前一日收盤: 510 (已 > MA200)")
    print(f"  今日收盤: 520")
    
    if signal3:
        print(f"  ❌ 錯誤：不應該再次觸發站上年線訊號")
    else:
        print(f"  ✅ 正確：未重複觸發訊號")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ma200_breakout())
