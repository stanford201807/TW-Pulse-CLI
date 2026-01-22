"""測試 Antigravity 反向代理連接"""
import requests
import json

# 測試配置
API_KEY = "sk-6d4331550a484aa18a8f9192b8781ddd"
BASE_URL = "http://127.0.0.1:8045"

print("=" * 60)
print("測試 Antigravity 反向代理連接")
print("=" * 60)

# 測試 1: 檢查端點是否可訪問
print("\n[測試 1] 檢查端點是否可訪問...")
try:
    response = requests.get(f"{BASE_URL}/v1beta/models", timeout=5)
    print(f"✓ 端點可訪問")
    print(f"  HTTP 狀態碼: {response.status_code}")
    if response.status_code == 200:
        print(f"  回應預覽: {response.text[:200]}...")
    else:
        print(f"  錯誤回應: {response.text}")
except requests.exceptions.ConnectionError:
    print(f"✗ 無法連接到 {BASE_URL}")
    print(f"  請確認 Antigravity 反向代理服務正在運行")
    exit(1)
except Exception as e:
    print(f"✗ 發生錯誤: {e}")
    exit(1)

# 測試 2: 使用 google-generativeai SDK 測試
print("\n[測試 2] 使用 google-generativeai SDK 測試...")
try:
    import google.generativeai as genai
    
    genai.configure(
        api_key=API_KEY,
        transport='rest',
        client_options={'api_endpoint': BASE_URL}
    )
    
    model = genai.GenerativeModel('gemini-3-pro-high')
    response = model.generate_content("Say 'Hello' in one word")
    print(f"✓ Google GenAI SDK 調用成功")
    print(f"  回應: {response.text}")
except ImportError:
    print(f"⚠ google-generativeai 未安裝，跳過此測試")
    print(f"  提示: pip install google-generativeai")
except Exception as e:
    print(f"✗ Google GenAI SDK 調用失敗: {e}")

# 測試 3: 直接 HTTP 請求測試
print("\n[測試 3] 直接 HTTP POST 請求測試...")
try:
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    }
    
    payload = {
        "contents": [{
            "parts": [{"text": "Say 'Hello' in one word"}]
        }]
    }
    
    response = requests.post(
        f"{BASE_URL}/v1beta/models/gemini-3-pro-high:generateContent",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"  HTTP 狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✓ 直接 HTTP 調用成功")
        result = response.json()
        print(f"  回應: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}...")
    else:
        print(f"✗ 直接 HTTP 調用失敗")
        print(f"  錯誤: {response.text[:300]}")
        
except Exception as e:
    print(f"✗ 直接 HTTP 調用失敗: {e}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
