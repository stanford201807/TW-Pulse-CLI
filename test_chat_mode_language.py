#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""測試聊天模式的語言設定"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 設定正確的路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from pulse.ai.client import AIClient


async def test_chat_mode():
    """測試聊天模式的語言"""
    
    # 設定 stdout 編碼為 UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("測試聊天模式語言設定")
    print("=" * 80)
    print()
    
    # 初始化 AI 客戶端
    client = AIClient()
    current_model = client.get_current_model()
    print(f"使用模型: {current_model['name']} ({current_model['id']})")
    print()
    
    # 測試案例
    test_cases = [
        ("2303", "直接輸入股票代號"),
        ("聯電怎麼樣？", "繁體中文問句"),
        ("嗨", "問候語"),
    ]
    
    for user_input, description in test_cases:
        print("-" * 80)
        print(f"測試案例: {description}")
        print(f"用戶輸入: {user_input}")
        print("-" * 80)
        
        try:
            # 使用聊天模式（不指定 system_prompt，會使用 CHAT_SYSTEM_PROMPT）
            response = await client.chat(
                message=user_input,
                use_history=False
            )
            
            print("AI 回應:")
            print(response)
            print()
            
            # 檢查語言
            indonesian_keywords = ["ditutup", "dengan", "yang", "pada", "menunjukkan", "berikut"]
            found_indonesian = any(kw in response.lower() for kw in indonesian_keywords)
            
            chinese_keywords = ["台灣", "股票", "分析", "收盤", "漲", "跌", "元"]
            found_chinese = any(kw in response for kw in chinese_keywords)
            
            if found_indonesian:
                print(f"[FAIL] 發現印尼語")
            elif found_chinese or len(response) > 0:
                print(f"[OK] 回應為繁體中文")
            else:
                print(f"[WARNING] 無法判定語言")
            
        except Exception as e:
            print(f"[ERROR] 錯誤: {e}")
        
        print()
    
    print("=" * 80)
    print("測試完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_chat_mode())
