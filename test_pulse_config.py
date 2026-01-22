"""測試 Pulse 的 LiteLLM 配置是否正確使用反向代理"""
import asyncio
import os
import sys

# 設定環境變數（模擬 .env 載入）
os.environ["GEMINI_API_KEY"] = "sk-6d4331550a484aa18a8f9192b8781ddd"
os.environ["PULSE_AI__DEFAULT_MODEL"] = "gemini/gemini-3-pro-high"
os.environ["PULSE_AI__GEMINI_API_BASE"] = "http://127.0.0.1:8045/v1"

# 加入專案路徑
sys.path.insert(0, '.')

print("=" * 60)
print("測試 Pulse AI Client 配置")
print("=" * 60)

# 測試 1: 檢查配置載入
print("\n[測試 1] 檢查配置載入...")
try:
    from pulse.core.config import settings
    print(f"✓ 配置載入成功")
    print(f"  默認模型: {settings.ai.default_model}")
    print(f"  Gemini API Base: {settings.ai.gemini_api_base}")
    print(f"  溫度: {settings.ai.temperature}")
except Exception as e:
    print(f"✗ 配置載入失敗: {e}")
    exit(1)

# 測試 2: 檢查 AIClient 初始化
print("\n[測試 2] 檢查 AIClient 初始化...")
try:
    from pulse.ai.client import AIClient
    client = AIClient()
    print(f"✓ AIClient 初始化成功")
    print(f"  當前模型: {client.model}")
    print(f"  溫度: {client.temperature}")
    print(f"  最大 tokens: {client.max_tokens}")
except Exception as e:
    print(f"✗ AIClient 初始化失敗: {e}")
    exit(1)

# 測試 3: 檢查實際 API 調用
print("\n[測試 3] 測試實際 API 調用...")
print("  注意：監控反向代理日誌，確認是否收到請求")

async def test_chat():
    try:
        # 啟用 LiteLLM 詳細日誌
        import litellm
        litellm.set_verbose = True
        
        response = await client.chat(
            message="Say 'test' in one word",
            use_history=False
        )
        print(f"✓ API 調用成功")
        print(f"  回應: {response}")
        return True
    except Exception as e:
        print(f"✗ API 調用失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

# 運行測試
print("\n開始調用...")
result = asyncio.run(test_chat())

print("\n" + "=" * 60)
if result:
    print("✅ 測試完成 - 請檢查反向代理日誌")
else:
    print("❌ 測試失敗 - API 調用未成功")
print("=" * 60)
