"""在 venv 中測試 Pulse AI Client 完整流程"""
import subprocess
import sys

print("=" * 60)
print("測試 Pulse 完整調用流程（使用 venv）")
print("=" * 60)

# 測試腳本內容
test_script = """
import asyncio
import sys
sys.path.insert(0, '.')

from pulse.ai.client import AIClient
from pulse.core.config import settings

print("\\n[配置檢查]")
print(f"  預設模型: {settings.ai.default_model}")
print(f"  Gemini API Base: {settings.ai.gemini_api_base}")

async def test():
    print("\\n[建立 AI Client]")
    client = AIClient(model="gemini/gemini-3-flash")
    print(f"  模型: {client.model}")
    
    print("\\n[發送請求]")
    print("  ⚠️ 請監控反向代理日誌，確認是否收到請求...\\n")
    
    try:
        # 啟用 LiteLLM 詳細日誌
        import litellm
        litellm.set_verbose = True
        
        response = await client.chat(
            message="Say 'test' in one word",
            use_history=False
        )
        print(f"\\n✓ 調用成功！")
        print(f"  回應: {response}\\n")
        return True
    except Exception as e:
        print(f"\\n✗ 調用失敗: {e}\\n")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"""

# 儲存測試腳本
with open("test_venv_call.py", "w", encoding="utf-8") as f:
    f.write(test_script)

# 使用 venv 的 python 執行
print("\n執行測試...")
print("-" * 60)

try:
    result = subprocess.run(
        [".venv/Scripts/python.exe", "test_venv_call.py"],
        cwd=".",
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(result.stdout)
    if result.stderr:
        print("錯誤輸出:")
        print(result.stderr)
    
    print("-" * 60)
    
    if result.returncode == 0:
        print("\n✅ 測試成功！")
        print("請檢查反向代理監控是否收到請求。")
    else:
        print(f"\n❌ 測試失敗（退出碼：{result.returncode}）")
        
except subprocess.TimeoutExpired:
    print("\n⏱️ 測試超時（可能正在等待 API 回應）")
except Exception as e:
    print(f"\n❌ 執行錯誤: {e}")

print("\n" + "=" * 60)
