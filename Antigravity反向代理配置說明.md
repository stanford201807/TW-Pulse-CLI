# Antigravity 反向代理配置說明

本文檔說明如何配置 TW-Pulse-CLI 以使用 Antigravity 反向代理來調用 Gemini 模型。

## 配置概述

Antigravity 反向代理提供了一個本地端點來訪問 Gemini 模型，配置資訊如下：

- **端點 URL**: `http://127.0.0.1:8045`
- **API Key**: `sk-6d4331550a484aa18a8f9192b8781ddd`
- **可用模型**: `gemini-3-pro-high`, `gemini-3-flash` 等

## `.env` 配置

已在 `.env` 檔案中設定以下環境變數：

```bash
# Gemini API Key (由 Antigravity 提供)
GEMINI_API_KEY=sk-6d4331550a484aa18a8f9192b8781ddd

# 預設使用 Gemini 3 Pro High 模型
PULSE_AI__DEFAULT_MODEL=gemini/gemini-3-pro-high

# 本地代理端點 (LiteLLM 使用)
PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045

# 本地代理端點 (Google GenAI SDK 使用)
GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:8045
```

## 工作原理

1. **TW-Pulse-CLI** 使用 **LiteLLM** 框架來統一管理多個 AI 提供商
2. 當選擇 Gemini 模型時，`pulse/ai/client.py` 會檢查是否設定了 `gemini_api_base`
3. 如果有設定，所有 Gemini API 調用會導向 `http://127.0.0.1:8045` 而非 Google 官方 API
4. Antigravity 反向代理接收請求並轉發給實際的 Gemini API

## 使用步驟

### 1. 確認 Antigravity 反向代理正在運行

確保 Antigravity 反向代理服務正在 `http://127.0.0.1:8045` 上運行。

### 2. 驗證配置

檢查 `.env` 檔案中的配置是否正確：

```bash
cat .env | grep GEMINI
```

應該看到：
```
GEMINI_API_KEY=sk-6d4331550a484aa18a8f9192b8781ddd
PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045
GOOGLE_GEMINI_BASE_URL=http://127.0.0.1:8045
```

### 3. 重啟 Pulse 程式

停止並重新啟動 pulse 程式以載入新的環境變數：

```powershell
# 按 Ctrl+C 停止目前的 pulse
# 然後重新啟動
pulse
```

### 4. 測試連接

在 pulse 中輸入簡單的訊息測試 Gemini 模型是否正常工作：

```
> 測試一下
```

如果配置正確，應該能正常收到 AI 回應。

## 原生 Google GenAI SDK 範例

如果要直接使用 `google-generativeai` 庫（不透過 LiteLLM），可以使用以下程式碼：

```python
# 需要安裝: pip install google-generativeai
import google.generativeai as genai

# 使用 Antigravity 代理地址
genai.configure(
    api_key="sk-6d4331550a484aa18a8f9192b8781ddd",
    transport='rest',
    client_options={'api_endpoint': 'http://127.0.0.1:8045'}
)

model = genai.GenerativeModel('gemini-3-pro-high')
response = model.generate_content("Hello")
print(response.text)
```

## 故障排除

### 錯誤：認證失敗

**原因**：未設定 `PULSE_AI__GEMINI_API_BASE` 環境變數，程式嘗試連接 Google 官方 API 但使用了本地代理的 API Key。

**解決方法**：
1. 確認 `.env` 中已設定 `PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045`
2. 重新啟動 pulse 程式

### 錯誤：無法連線到伺服器

**原因**：Antigravity 反向代理服務未運行或端點錯誤。

**解決方法**：
1. 確認 Antigravity 反向代理正在運行
2. 檢查端點 URL 是否為 `http://127.0.0.1:8045`
3. 嘗試使用瀏覽器或 curl 測試端點：
   ```bash
   curl http://127.0.0.1:8045/v1beta/models
   ```

### 模型列表中看不到 Gemini 3 模型

**原因**：未同步更新 `config/pulse.yaml` 檔案。

**解決方法**：已在之前的步驟中修復，確認 `config/pulse.yaml` 包含 Gemini 3 模型定義。

## 技術架構

```
使用者輸入
    ↓
TW-Pulse-CLI (pulse/ai/client.py)
    ↓
LiteLLM (使用 api_base 參數)
    ↓
http://127.0.0.1:8045 (Antigravity 反向代理)
    ↓
Google Gemini API
```

## 注意事項

1. **API Key 格式**：Antigravity 提供的 API Key 格式為 `sk-` 開頭，不同於 Google 官方的 API Key
2. **模型名稱**：在 LiteLLM 中使用 `gemini/gemini-3-pro-high`，在原生 SDK 中使用 `gemini-3-pro-high`
3. **環境變數優先級**：`.env` 檔案中的配置會被讀取並覆蓋 `config.py` 和 `config/pulse.yaml` 的預設值
