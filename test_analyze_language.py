#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試 analyze 命令的語言設定診斷腳本"""

import sys
import os

# 設定正確的路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pulse.ai.prompts import StockAnalysisPrompts


def main():
    """檢查提示詞內容"""
    prompts = StockAnalysisPrompts()
    
    print("=== 檢查系統提示詞 ===\n")
    
    # 1. 檢查基礎提示詞
    base_prompt = prompts.get_system_base()
    print("1. 基礎系統提示詞 (get_system_base):")
    print("-" * 60)
    print(base_prompt[:500])
    print("...")
    print("-" * 60)
    print(f"包含 '繁體中文': {'✓' if '繁體中文' in base_prompt else '✗'}")
    print(f"包含 'Traditional Chinese': {'✓' if 'Traditional Chinese' in base_prompt else '✗'}")
    print(f"包含 'CRITICAL LANGUAGE REQUIREMENT': {'✓' if 'CRITICAL LANGUAGE REQUIREMENT' in base_prompt else '✗'}")
    print()
    
    # 2. 檢查綜合分析提示詞
    comprehensive_prompt = prompts.get_comprehensive_prompt()
    print("2. 綜合分析提示詞 (get_comprehensive_prompt):")
    print("-" * 60)
    print(f"提示詞長度: {len(comprehensive_prompt)} 字元")
    print(f"包含 '繁體中文': {'✓' if '繁體中文' in comprehensive_prompt else '✗'}")
    print(f"包含 'Traditional Chinese': {'✓' if 'Traditional Chinese' in comprehensive_prompt else '✗'}")
    print()
    
    # 3. 檢查格式化請求
    test_data = {
        "stock": {
            "ticker": "2330",
            "name": "台積電",
            "price": 1760.0
        }
    }
    
    formatted_request = prompts.format_analysis_request("2330", test_data)
    print("3. 格式化分析請求 (format_analysis_request):")
    print("-" * 60)
    print(formatted_request[:300])
    print("...")
    print("-" * 60)
    print(f"包含 '請使用繁體中文': {'✓' if '請使用繁體中文' in formatted_request else '✗'}")
    print()
    
    # 4. 檢查完整的系統提示詞
    print("4. 完整系統提示詞前500字元:")
    print("-" * 60)
    print(comprehensive_prompt[:500])
    print("...")
    print("-" * 60)
    print()
    
    # 5. 檢查是否有任何非UTF-8字元
    try:
        comprehensive_prompt.encode('utf-8')
        print("5. UTF-8 編碼檢查: ✓ 通過")
    except UnicodeEncodeError as e:
        print(f"5. UTF-8 編碼檢查: ✗ 失敗 - {e}")
    
    print("\n=== 診斷完成 ===")


if __name__ == "__main__":
    main()
