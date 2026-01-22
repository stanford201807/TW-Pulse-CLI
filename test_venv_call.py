
import asyncio
import sys
sys.path.insert(0, '.')

from pulse.ai.client import AIClient
from pulse.core.config import settings

print("\n[配置檢查]")
print(f"  預設模型: {settings.ai.default_model}")
print(f"  Gemini API Base: {settings.ai.gemini_api_base}")

async def test():
    print("\n[建立 AI Client]")
    client = AIClient(model="gemini/gemini-3-flash")
    print(f"  模型: {client.model}")
    
    print("\n[發送請求]")
    print("  ⚠️ 請監控反向代理日誌，確認是否收到請求...\n")
    
    try:
        # 啟用 LiteLLM 詳細日誌
        import litellm
        litellm.set_verbose = True
        
        response = await client.chat(
            message="Say 'test' in one word",
            use_history=False
        )
        print(f"\n✓ 調用成功！")
        print(f"  回應: {response}\n")
        return True
    except Exception as e:
        print(f"\n✗ 調用失敗: {e}\n")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
