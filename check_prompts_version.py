#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""檢查 Pulse 是否已載入最新的提示詞"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pulse.ai.prompts import StockAnalysisPrompts


def main():
    """檢查提示詞版本"""
    
    # 設定 stdout 編碼為 UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("Pulse 提示詞版本檢查")
    print("=" * 80)
    print()
    
    prompts = StockAnalysisPrompts()
    
    # 獲取系統提示詞
    system_prompt = prompts.get_system_base()
    
    # 檢查關鍵字
    checks = {
        "舊版語言要求 (CRITICAL LANGUAGE REQUIREMENT)": "CRITICAL LANGUAGE REQUIREMENT" in system_prompt,
        "新版語言要求 (絕對語言要求)": "絕對語言要求" in system_prompt,
        "強化版中文指令 (你「必須」且「只能」使用繁體中文回答)": "你「必須」且「只能」使用繁體中文回答" in system_prompt,
        "禁止印尼語明確說明": "印尼語" in system_prompt,
        "Emoji 強調符號 (🚨)": "🚨" in system_prompt,
        "結尾再次提醒 (🔴 再次提醒)": "🔴 再次提醒" in system_prompt,
    }
    
    print("提示詞檢查結果:")
    print("-" * 80)
    
    all_passed = True
    for check_name, check_result in checks.items():
        status = "[OK]" if check_result else "[FAIL]"
        print(f"{status} {check_name}")
        if not check_result:
            all_passed = False
    
    print("-" * 80)
    print()
    
    if all_passed:
        print("[SUCCESS] ✓ Pulse 已載入最新版本的提示詞")
        print()
        print("如果仍然出現印尼語，可能的原因：")
        print("1. Pulse 主程式未重啟（需要重新啟動 pulse 應用程式）")
        print("2. AI 模型的隨機性導致偶爾忽略指令")
        print("3. 反向代理可能修改了提示詞")
        print()
        print("建議動作：")
        print("- 重新啟動 Pulse 應用程式")
        print("- 執行 'pulse /clear' 清除對話歷史")
        print("- 再次測試 '/analyze 2303' 命令")
    else:
        print("[FAIL] ✗ Pulse 使用的是舊版提示詞")
        print()
        print("請執行以下動作：")
        print("1. 確認 pulse/ai/prompts.py 文件已儲存")
        print("2. 重新啟動 Pulse 應用程式")
        print("3. 再次執行此診斷腳本")
    
    print()
    print("=" * 80)
    print("系統提示詞前 500 字元預覽：")
    print("=" * 80)
    print(system_prompt[:500])
    print("...")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
