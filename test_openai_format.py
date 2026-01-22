"""測試使用 OpenAI SDK 格式調用 Antigravity 反向代理"""
from openai import OpenAI

# 配置
client = OpenAI(
    base_url="http://127.0.0.1:8045/v1",
    api_key="sk-6d4331550a484aa18a8f9192b8781ddd"
)

print("=" * 60)
print("測試 OpenAI 兼容 API 格式")
print("=" * 60)

# 測試 gemini-3-flash
print("\n[測試 1] 使用 gemini-3-flash 模型...")
try:
    response = client.chat.completions.create(
        model="gemini-3-flash",
        messages=[{"role": "user", "content": "Say 'Hello' in one word"}]
    )
    print(f"✓ 調用成功")
    print(f"  模型: {response.model}")
    print(f"  回應: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ 調用失敗: {e}")

# 測試 gemini-3-pro-high
print("\n[測試 2] 使用 gemini-3-pro-high 模型...")
try:
    response = client.chat.completions.create(
        model="gemini-3-pro-high",
        messages=[{"role": "user", "content": "Say 'World' in one word"}]
    )
    print(f"✓ 調用成功")
    print(f"  模型: {response.model}")
    print(f"  回應: {response.choices[0].message.content}")
except Exception as e:
    print(f"✗ 調用失敗: {e}")

# 列出可用模型
print("\n[測試 3] 列出可用模型...")
try:
    models = client.models.list()
    print(f"✓ 獲取模型列表成功")
    print(f"  可用模型數量: {len(models.data)}")
    print(f"\n  前 10 個模型:")
    for i, model in enumerate(models.data[:10]):
        print(f"    {i+1}. {model.id}")
except Exception as e:
    print(f"✗ 獲取模型列表失敗: {e}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
