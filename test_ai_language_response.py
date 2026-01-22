#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試 AI 實際回應的語言"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定正確的路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pulse.ai.client import AIClient
from pulse.ai.prompts import StockAnalysisPrompts


async def test_ai_language():
    """測試 AI 回應語言"""
    
    # 設定 stdout 編碼為 UTF-8
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=== 測試 AI 回應語言 ===\n")
    
    # 初始化 AI 客戶端
    client = AIClient()
    current_model = client.get_current_model()
    print(f"使用模型: {current_model['name']} ({current_model['id']})\n")
    
    # 準備測試數據
    test_ticker = "2330"
    test_data = {
        "stock": {
            "ticker": "2330",
            "name": "台積電",
            "price": 1760.0,
            "change": 20.0,
            "change_percent": 1.15,
            "volume": 50000000,
            "market_cap": 45000000000000
        },
        "technical": {
            "rsi": 71.1,
            "macd": 70.26,
            "sma_20": 1659.0,
            "sma_50": 1529.8,
            "signal": "overbought"
        },
        "fundamental": {
            "pe_ratio": 25.3,
            "eps": 69.5,
            "roe": 45.1,
            "profit_margin": 45.1
        }
    }
    
    print("正在呼叫 AI 進行分析...\n")
    print("-" * 80)
    
    try:
        # 使用 analyze_stock 方法
        response = await client.analyze_stock(
            ticker=test_ticker,
            data=test_data,
            analysis_type="comprehensive"
        )
        
        print("AI 回應:")
        print("=" * 80)
        print(response)
        print("=" * 80)
        print()
        
        # 檢查回應語言
        print("語言檢查:")
        print("-" * 80)
        
        # 檢查是否包含印尼語關鍵字
        indonesian_keywords = ["menunjukkan", "ditutup", "pada", "harga", "saat ini", "dengan", "yang", "namun", "peringatan"]
        found_indonesian = [kw for kw in indonesian_keywords if kw.lower() in response.lower()]
        
        # 檢查是否包含繁體中文關鍵字
        chinese_keywords = ["台積電", "股票", "分析", "技術", "指標", "建議", "趨勢", "支撐", "壓力"]
        found_chinese = [kw for kw in chinese_keywords if kw in response]
        
        if found_indonesian:
            print(f"[X] 發現印尼語關鍵字: {found_indonesian}")
        else:
            print("[OK] 未發現印尼語關鍵字")
            
        if found_chinese:
            print(f"[OK] 發現繁體中文關鍵字: {found_chinese}")
        else:
            print("[X] 未發現繁體中文關鍵字")
        
        print("-" * 80)
        
        # 判斷語言
        if found_chinese and not found_indonesian:
            print("\n[SUCCESS] 測試通過：AI 正確使用繁體中文回答")
            return True
        elif found_indonesian:
            print("\n[FAILED] 測試失敗：AI 使用了印尼語")
            return False
        else:
            print("\n[WARNING] 測試結果不明確：請人工檢查")
            return None
            
    except Exception as e:
        print(f"[ERROR] 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_ai_language())
    sys.exit(0 if result else 1)
