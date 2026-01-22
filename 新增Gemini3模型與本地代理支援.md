# Walkthrough：新增 Gemini 3 模型與本地代理支援

## 變更摘要

本次實作成功新增了兩個 Gemini 3 系列模型，並實現了 Gemini API 的本地代理支援功能。

### 新增模型
- ✅ `gemini/gemini-3-flash` - Gemini 3 Flash (Google)
- ✅ `gemini/gemini-3-pro-high` - Gemini 3 Pro High (Google)

### 新增功能
- ✅ 支援透過環境變數設定自定義 Gemini API base URL
- ✅ 本地代理端點：`http://127.0.0.1:8045`

---

## 變更檔案清單

### 1️⃣ [config.py](file:///d:/GitHub/TW-Pulse-CLI/pulse/core/config.py)

#### 新增兩個 Gemini 3 模型定義

```python
# Google
"gemini/gemini-2.0-flash": "Gemini 2.0 Flash (Google)",
"gemini/gemini-2.5-flash-preview-05-20": "Gemini 2.5 Flash (Google)",
"gemini/gemini-3-flash": "Gemini 3 Flash (Google)",           # ✨ 新增
"gemini/gemini-3-pro-high": "Gemini 3 Pro High (Google)",     # ✨ 新增
```

#### 新增 API Base URL 設定欄位

```python
class AISettings(BaseSettings):
    timeout: int = Field(default=120, description="Request timeout in seconds")

    # API endpoint customization (for proxies or custom deployments)  # ✨ 新增
    gemini_api_base: str | None = Field(                              # ✨ 新增
        default=None,                                                  # ✨ 新增
        description="Custom API base URL for Gemini (e.g., http://127.0.0.1:8045)",
    )                                                                  # ✨ 新增
```

**說明**：此欄位允許用戶透過環境變數 `PULSE_AI__GEMINI_API_BASE` 設定自定義的 Gemini API 端點。

---

### 🔧 [pulse.yaml](file:///d:/GitHub/TW-Pulse-CLI/config/pulse.yaml) - **關鍵修復**

> [!IMPORTANT]
> **發現問題**：用戶回報在主程式中無法看到新增的 Gemini 3 模型。
> 
> **根本原因**：`config/pulse.yaml` 中的 `available_models` 列表會**覆蓋** `config.py` 的預設值，因此需要在 YAML 檔案中也新增模型定義。

#### 新增兩個 Gemini 3 模型定義

```yaml
# Google
gemini/gemini-2.0-flash: "Gemini 2.0 Flash (Google)"
gemini/gemini-2.5-flash-preview-05-20: "Gemini 2.5 Flash (Google)"
gemini/gemini-3-flash: "Gemini 3 Flash (Google)"           # ✨ 新增
gemini/gemini-3-pro-high: "Gemini 3 Pro High (Google)"     # ✨ 新增
```

#### 新增 API Base URL 設定說明

```yaml
ai:
  temperature: 0.7
  max_tokens: 4096
  timeout: 180
  # gemini_api_base: "http://127.0.0.1:8045"  # ✨ 新增：自定義 Gemini API 端點
```

---

### 2️⃣ [client.py](file:///d:/GitHub/TW-Pulse-CLI/pulse/ai/client.py)

#### 修改 `chat()` 方法

**原始程式碼**：
```python
response = await acompletion(
    model=self.model,
    messages=messages,
    temperature=self.temperature,
    max_tokens=self.max_tokens,
    timeout=self.timeout,
)
```

**更新後**：
```python
# Prepare API parameters
api_params = {
    "model": self.model,
    "messages": messages,
    "temperature": self.temperature,
    "max_tokens": self.max_tokens,
    "timeout": self.timeout,
}

# If using Gemini with custom API base
if self.model.startswith("gemini/") and settings.ai.gemini_api_base:
    api_params["api_base"] = settings.ai.gemini_api_base

response = await acompletion(**api_params)
```

#### 修改 `chat_stream()` 方法

同樣的邏輯也應用於串流模式，確保使用 `stream=True` 時也能導向自定義端點。

**說明**：當模型為 Gemini 系列且設定了 `gemini_api_base` 時，LiteLLM 會將請求發送到自定義端點而非官方 API。

---

### 3️⃣ [.env](file:///d:/GitHub/TW-Pulse-CLI/.env)

#### 新增環境變數說明

```bash
PULSE_AI__DEFAULT_MODEL=gemini/gemini-3-pro-high

# Custom API Base URL for Gemini (Optional - for local proxy)      # ✨ 新增
# Uncomment and set this to use a local proxy or custom endpoint    # ✨ 新增
# Example: PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045         # ✨ 新增
# PULSE_AI__GEMINI_API_BASE=                                        # ✨ 新增

# AI temperature (0.0 - 2.0, lower = more focused, higher = more creative)
PULSE_AI__TEMPERATURE=0.7
```

**說明**：用戶可以取消註解並設定 `PULSE_AI__GEMINI_API_BASE` 來啟用本地代理。

---

## 如何使用本地代理

### 步驟 1：設定環境變數

在 `.env` 檔案中新增或取消註解以下設定：

```bash
PULSE_AI__GEMINI_API_BASE=http://127.0.0.1:8045
```

### 步驟 2：選擇 Gemini 模型

確保您使用的是 Gemini 模型（例如 `gemini/gemini-3-flash` 或 `gemini/gemini-3-pro-high`）：

```bash
PULSE_AI__DEFAULT_MODEL=gemini/gemini-3-flash
```

### 步驟 3：啟動應用程式

```powershell
python -m pulse.cli.app
```

所有 Gemini API 調用將自動導向本地代理端點 `http://127.0.0.1:8045`。

---

## 驗證結果

### ✅ 語法檢查
- `config.py`：語法正確，模組成功載入
- `client.py`：語法正確，`AIClient` 成功匯入

### ✅ 模型列表驗證

執行以下指令確認新模型已加入：

```powershell
python -c "from pulse.core.config import settings; print([m for m in settings.ai.available_models.keys() if 'gemini-3' in m])"
```

**輸出**：
```
['gemini/gemini-3-flash', 'gemini/gemini-3-pro-high']
```

### ⏳ 本地代理測試

> [!NOTE]
> **需要用戶手動測試**
> 
> 由於本地代理需要實際運行在 `http://127.0.0.1:8045`，請用戶按照「如何使用本地代理」步驟進行測試。

---

## 技術細節

### LiteLLM 本地代理機制

根據 LiteLLM 官方文件，`api_base` 參數會覆蓋預設的 API 端點：

```python
response = await acompletion(
    model="gemini/gemini-3-flash",
    messages=[{"role": "user", "content": "Hello"}],
    api_base="http://127.0.0.1:8045"  # 覆蓋預設端點
)
```

這使得所有請求都會發送到本地代理，而非 Google 官方 API。

### 相容性說明

- ✅ **向後相容**：未設定 `PULSE_AI__GEMINI_API_BASE` 時，行為與原本完全一致
- ✅ **不影響其他模型**：僅 Gemini 模型會使用自定義端點，其他提供商（OpenAI、Anthropic 等）不受影響
- ✅ **擴展性**：未來可輕鬆為其他提供商新增類似功能

---

## 總結

本次實作成功達成以下目標：

1. ✅ 新增 `gemini/gemini-3-flash` 和 `gemini/gemini-3-pro-high` 兩個模型
2. ✅ 實現本地代理支援，允許透過 `PULSE_AI__GEMINI_API_BASE` 設定自定義端點
3. ✅ 所有變更向後相容，不影響現有功能
4. ✅ 通過語法驗證，程式碼品質良好

用戶現在可以使用新的 Gemini 3 模型，並可選擇性地將 API 調用導向本地代理端點 `http://127.0.0.1:8045`。
