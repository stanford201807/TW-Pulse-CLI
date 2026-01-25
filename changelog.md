# Changelog

## [2026-01-25] - 回測報表計算邏輯修復 (Backtest Report Calculation Fix)

### 🐛 Bug 修復
- **資金份數計算邏輯**：修復 `trade_report.py` 中資金份數計算錯誤，從「持倉市值 / 每份金額」改為追蹤實際交易次數，確保買進+1份、減碼-1份、全數清倉歸零。
- **減碼股數計算**：修復 `farmer_planting.py` 中減碼使用固定股數問題，改為使用動態計算（`_calculate_buy_quantity()`），與加碼保持一致。
- **持倉最高價追蹤**：修復 `trade_report.py` 中波段最高價追蹤邏輯，僅在持倉期間追蹤最高價，清倉後自動重置為 0。
- **最大份數限制失效**：修復 `farmer_planting.py` 中加碼檢查邏輯錯誤，從檢查股數（10,000股）改為檢查份數（10份），新增 `position_count` 追蹤實際買進次數，防止超過 10 份限制。

### 🔧 影響範圍
- `pulse/reports/trade_report.py`：新增 `position_count` 變數追蹤份數，修正 `peak_price` 更新邏輯
- `pulse/core/strategies/farmer_planting.py`：新增 `position_count` 成員變數，修正減碼訊號的股數計算方式，修正加碼時的最大份數檢查，在所有買賣訊號點更新份數

### ✅ 驗證結果
- 資金份數正確顯示整數（1.0/10, 2.0/10, 3.0/10 等）
- 減碼交易正確減少 1 份（例：8.0/10 → 7.0/10）
- 清倉交易的持倉最高顯示為 `-`，清倉後重新開始追蹤
- 最大份數限制正確生效（最多加碼到 10.0/10，不會超過）

---

## [2026-01-25] - 策略邏輯修正：加入「站上年線」啟動機制

### 🚀 新增功能
- **站上年線啟動機制**：策略新增主要進場訊號，當價格從年線（MA200）下方站上年線時，自動買進第 1 份。
  - 觸發條件：前一日收盤 ≤ MA200 且今日收盤 > MA200
  - 此機制解決了 2022-2025 期間無交易的問題
  - 符合 h版農夫播種術原始規則

### 🔧 技術修改
- 新增狀態變數 `prev_close` 追蹤前一日收盤價
- 調整 RSI 抄底為輔助進場機制（空頭反彈用）
- 修改檔案：`pulse/core/strategies/farmer_planting.py`

### ✅ 測試結果
- 單元測試通過：站上年線正確觸發，年線上方不重複觸發

### 🐛 Bug 修復
- **prev_close 更新邏輯修正**：修復賣出條件觸發後 `prev_close` 未更新的問題。
  - 原問題：防禦機制/移動停利觸發時直接 return，跳過 `prev_close` 更新
  - 解決方案：將 `prev_close` 更新移到函數開頭，確保每次調用都會正確更新
  - 此修復解決了「賣出後無法站上年線」的問題

### ⚡ 功能改進
- **支持零股買進（固定金額模式）**：
  - 新增 `amount_per_position` 參數（每份 10 萬）
  - 修改 `PositionManager` 支持固定金額模式
  - 當 `shares_per_position=0` 時，自動以固定金額計算股數
  - 解決了股價過高導致現金不足無法加碼的問題

---

## [2026-01-25] - 繁體中文完整本地化與策略系統規劃 (Traditional Chinese Localization & Strategy System Planning)

### 🚀 新增功能與改進
- **策略模組系統架構設計**：規劃可擴充的策略模組系統，支援多種交易策略與回測功能。
  - 設計策略基礎類別 (`BaseStrategy`) 與註冊機制
  - 規劃首個策略「進階農夫播種術」，包含加減碼、停利停損、資金控管和回測功能
  - 設計回測引擎架構，支援 5 年歷史數據回測與績效分析
  - 規劃 CLI 命令介面：`/strategy` 主命令與子命令

### 🐛 Bug 修復
- **策略命令 TUI 顯示修復**：修復 `/strategy` 命令在 Textual TUI 中無法顯示輸出的問題。
  - **返回值修復**：將所有策略命令處理函數改為返回字符串，並修復 `pulse/cli/commands/registry.py` 中 `_cmd_strategy()` 的返回值處理
  - **Markdown 格式轉換**：將所有 Rich 標記（`[bold]`、`[cyan]`、`[red]` 等）轉換為標準 Markdown 格式，以支援 Textual 的 `Markdown` widget
  - **影響文件**：`pulse/cli/commands/strategy.py`、`pulse/cli/commands/registry.py`
  - **測試狀態**：✅ 所有自動化測試通過（5/5），手動測試確認輸出格式正確


### 🔧 優化與調整
- **完整繁體中文化**：將所有印尼語字串和錯誤訊息翻譯為繁體中文。
  - `pulse/core/smart_agent.py`：翻譯所有 AI 提示、錯誤訊息、系統提示和對話追蹤關鍵字
  - `pulse/core/agent.py`：翻譯意圖識別模式、工具方法錯誤訊息和代碼原因訊息
  - 更新台灣股市專用術語（台灣50、中型100、熱門股等）

- **Trading Plan 繁體中文化**：`pulse/core/trading_plan.py` 完整本地化。
  - 貨幣符號：Rp（印尼盾）→ NT$（新台幣）
  - 輸出格式：所有章節標題翻譯為繁體中文（進場、停利目標、停損、風險/報酬等）
  - 技術指標：翻譯 RSI、MACD、趨勢等指標說明
  - 執行策略：6 個步驟全部翻譯為繁體中文
  - 品質標籤：優秀/良好/合理/不佳

### 📝 文檔更新
- 新增策略系統完整架構文檔 (`strategy_system_plan.md`)
- 新增策略開發任務清單 (`strategy_task.md`)
- 新增 Trading Plan 本地化驗證導覽 (`trading_plan_walkthrough.md`)
- 更新語言修復驗證導覽 (`walkthrough.md`)

### 📂 檔案結構變更
- 新增 `.gitignore` 條目：`proxy/` 目錄

---

本文件記錄 TW-Pulse-CLI 專案的重要變更歷史。

---

## [2026-01-22] - AI 語言輸出全面修復 (Comprehensive AI Language Fix)

### 🐛 Bug 修復
- **聊天模式語言修復**：修復直接輸入股票代號（如 `2303`）或一般對話時，AI 仍使用印尼語回答的問題。修正 `CHAT_SYSTEM_PROMPT` 缺少語言設定的缺陷。
- **緩存導致的舊提示詞問題**：解決因 Python `__pycache__` 導致提示詞更新未即時生效的問題。

### 🔧 優化與調整
- **強化提示詞強度**：將所有系統提示詞升級為「絕對語言要求 (Absolute Language Requirement)」，明確禁止印尼語與簡體中文。
- **新增修復工具**：新增 `fix_language_issue.ps1` 腳本，提供一鍵清除緩存與驗證提示詞版本的功能。

## [2026-01-22] - 修正 AI 分析語言輸出 (Fix AI Analysis Language Output)

### 🐛 問題修正
- **強制繁體中文輸出**：修正 `/analyze` 命令 AI 回應可能使用印尼文或其他語言的問題，現在所有分析結果強制使用繁體中文輸出。

### 🔧 技術細節
- 修改 `pulse/ai/prompts.py`：
  - 在 `get_system_base()` 提示詞開頭加入明確的語言要求區塊，強制使用繁體中文
  - 修改 `format_analysis_request()` 方法，將分析請求改為繁體中文並明確要求繁體中文回答
  - 更新提示詞說明，從「英文或繁體中文」改為「繁體中文」
- 此修改確保所有分析類型（綜合、技術、基本面、法人）都使用繁體中文輸出

---

## [2026-01-22] - 新增 Gemini 3 模型與本地代理支援 (Gemini 3 Models & Local Proxy Support)

### 🚀 新增功能與改進
- **Gemini 3 模型支援**：新增 `gemini/gemini-3-flash` 與 `gemini/gemini-3-pro-high` 兩個模型選項，可透過 LiteLLM 框架調用最新的 Gemini 3 系列模型。
- **本地代理支援**：新增 `PULSE_AI__GEMINI_API_BASE` 環境變數設定，允許將 Gemini API 調用導向本地代理端點（例如 `http://127.0.0.1:8045`），提升開發測試靈活性。
- **AI 配置擴展**：在 `pulse/core/config.py` 中新增 `gemini_api_base` 設定欄位，支援自定義 Gemini API 端點。
- **AI 客戶端優化**：更新 `pulse/ai/client.py` 的 `chat()` 和 `chat_stream()` 方法，當使用 Gemini 模型且設定了自定義端點時，自動將請求路由到指定的本地代理。

### 📝 文檔更新
- 更新 `.env` 檔案範例，新增 `PULSE_AI__GEMINI_API_BASE` 環境變數的使用說明與範例。

### 🔧 技術細節
- 修改檔案：
  - `pulse/core/config.py`：擴展模型列表與 API 端點設定
  - `pulse/ai/client.py`：實作本地代理路由邏輯
  - `.env`：新增環境變數說明註解
  - `config/pulse.yaml`：同步新增 Gemini 3 模型定義與 API base 設定
- 所有變更向後相容，未設定環境變數時行為與原本完全一致。

> [!NOTE]
> **重要**：由於 `config/pulse.yaml` 會覆蓋 `config.py` 的預設配置，因此需要在兩個檔案中都新增模型定義。

---

## 版本說明
- 本專案目前處於開發階段，版本號為 `0.1.0`
- Changelog 條目按時間倒序排列（最新在上）
