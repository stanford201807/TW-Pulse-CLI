# 診斷報告：Pulse 未調用反向代理問題

## 問題描述

用戶反映：pulse 程式運行時，反向代理監控顯示**沒有收到任何請求**。

## 已完成的檢查

### ✅ 配置已正確設定

#### `.env` 檔案
```bash
GEMINI_API_KEY=sk-6d4331550a484aa18a8f9192b8781ddd
PULSE_AI__DEFAULT_MODEL=gemini/gemini-3-pro-high
PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045/v1
```

#### `config/pulse.yaml` 檔案
```yaml
ai:
  default_model: "gemini/gemini-3-flash"
  gemini_api_base: "http://127.0.0.1:8045/v1"
```

### ✅ 反向代理運行正常

使用 OpenAI SDK 直接測試：
- ✓ `gemini-3-flash` 調用成功
- ✓ `gemini-3-pro-high` 調用成功
- ✓ 68 個模型可用

### ✅ 代碼邏輯正確

`pulse/ai/client.py` 第 122-124 行：
```python
# If using Gemini with custom API base
if self.model.startswith("gemini/") and settings.ai.gemini_api_base:
    api_params["api_base"] = settings.ai.gemini_api_base
```

## 🔍 潛在問題分析

### 問題 1：pulse 程式未重啟

**最可能的原因**：pulse 程式在配置更新之前啟動，仍在使用舊配置。

**證據**：
- 用戶提到程式已運行 30 分鐘
- 配置更新在最近才完成

**解決方法**：
1. 停止 pulse 程式（Ctrl+C）
2. 重新啟動：`pulse`

### 問題 2：LiteLLM 可能不支援完整的 OpenAI 格式

LiteLLM 在調用 Gemini 時可能使用原生 Google API 格式而非 OpenAI 格式。

**檢查方法**：
在 `pulse/ai/client.py` 中添加日誌：

```python
# 在第 122 行之後添加
if self.model.startswith("gemini/") and settings.ai.gemini_api_base:
    api_params["api_base"] = settings.ai.gemini_api_base
    log.info(f"Using custom API base: {api_params['api_base']}")  # 添加此行
    log.info(f"API params: {api_params}")  # 添加此行
```

## 📝 建議的測試步驟

### 步驟 1：確認 pulse 已重啟

```powershell
# 停止目前的 pulse（如果正在運行）
# 按 Ctrl+C

# 重新啟動
pulse
```

### 步驟 2：啟用詳細日誌

修改 `.env` 檔案添加：
```bash
PULSE_DEBUG=true
```

### 步驟 3：監控日誌與反向代理

1. 在一個終端運行 pulse
2. 在另一個終端監控反向代理日誌
3. 在 pulse 中輸入測試訊息
4. 觀察反向代理是否收到請求

### 步驟 4：如果仍無請求

可能需要修改 LiteLLM 調用方式，改用直接 HTTP 請求或 OpenAI SDK。

## 🔧 備選方案

如果 LiteLLM 無法正確使用反向代理，可以考慮：

### 方案 A：修改為直接使用 OpenAI SDK

修改 `pulse/ai/client.py`，當檢測到 Gemini + custom api_base 時，改用 OpenAI SDK：

```python
if self.model.startswith("gemini/") and settings.ai.gemini_api_base:
    # 使用 OpenAI SDK 直接調用
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=settings.ai.gemini_api_base,
        api_key=os.environ.get("GEMINI_API_KEY")
    )
    # 使用 OpenAI 格式調用
    ...
```

### 方案 B：設定 LiteLLM 環境變數

嘗試設定 LiteLLM 特定的環境變數：

```bash
# 在 .env 中添加
LITELLM_PROXY=http://127.0.0.1:8045/v1
```

## ⏭️ 下一步行動

**立即執行**：
1. ✅ 停止 pulse 程式
2. ✅ 重新啟動 pulse
3. ✅ 在 pulse 中輸入測試訊息
4. ✅ 檢查反向代理日誌

如果仍沒有收到請求，需要添加更詳細的日誌來診斷 LiteLLM 的實際行為。

---

**診斷時間**: 2026-01-22 20:40  
**狀態**: 等待 pulse 重啟測試
