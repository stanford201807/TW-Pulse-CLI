# Pulse-CLI 改寫進度與待辦事項

> **最後更新**: 2026-01-14 09:15
> **整體進度**: 100% 完成 🎉

---

## 2026-01-14 更新摘要

### 本次修復 ✅

#### 1. 命令註冊修復
- [x] 移除已刪除的 `/bandar` 命令註冊
- [x] 新增缺失的命令註冊：
  - `/technical` (tech, ta) - 技術分析
  - `/fundamental` (fund, fa) - 基本面分析
  - `/institutional` (inst, flow, broker) - 法人動向
  - `/screen` (scan, filter) - 股票篩選
  - `/sector` (industry) - 產業分析
  - `/compare` (cmp, vs) - 股票比較
  - `/chart` (k, kline) - K線圖
  - `/forecast` (pred, predict) - 價格預測
  - `/taiex` (twii, index) - 大盤指數
  - `/plan` (trade) - 交易計劃
  - `/clear` (cls) - 清除聊天

#### 2. SAPTA BollingerBands 修復
- [x] 修復 `bb_squeeze.py` 的 ta 庫參數錯誤
- [x] 將 `window`/`window_dev` 改為 `n`/`ndev` (ta 0.5.25 相容)

#### 3. CLI 輸出繁體中文化
- [x] `/help` - 可用命令、說明、用法、別名
- [x] `/technical` - 技術分析標題、狀態翻譯 (超買/超賣/多頭/空頭)
- [x] `/fundamental` - 基本面分析、估值評分、類別名稱
- [x] `/institutional` - 法人動向 (已是中文)
- [x] `/sector` - 產業分析、漲跌幅前三
- [x] `/compare` - 股票比較、表頭翻譯
- [x] `/chart` - 圖表已儲存
- [x] `/forecast` - 價格預測、趨勢翻譯、支撐/壓力位
- [x] `/taiex` - 指數、漲跌、今日區間、52週區間
- [x] `/screen` - 錯誤訊息
- [x] `/analyze` - 錯誤訊息
- [x] `/models` - 模型切換訊息

#### 4. 輸出格式美化
- [x] `/forecast` - 表格式輸出 + emoji 圖示
- [x] `/taiex` - 表格式輸出
- [x] `/compare` - 表格式輸出

---

## 已完成部分 ✅

### 1. 數據層重構
- [x] `finmind_data.py` - FinMind 數據獲取完整實現 (850+ 行)
- [x] `stock_data_provider.py` - 統一數據層 (FinMind 優先 + yfinance 回退)
- [x] `yfinance.py` - 更新為台灣市場 (.TW 後綴, TAIEX/TPEX 指數)

### 2. 核心模組台灣化
- [x] 完成所有核心模組的台灣化改寫
- [x] 移除印尼 Stockbit 平台相關代碼

### 3. CLI 命令
- [x] 所有命令已註冊並測試通過
- [x] 輸出已中文化

### 4. 驗證測試
- [x] 所有命令測試通過

---

## 待完成部分 ⏳

### UI 輸出格式改善建議 (優先級: 高)

#### 1. 統一視覺風格
- [ ] 所有命令使用一致的表格框線樣式 (`═══`, `┌─┐`, `└─┘`)
- [ ] 統一標題格式：`═══ 命令名稱: 股票代碼 ═══`
- [ ] 統一使用 emoji 圖示增加可讀性

#### 2. 數據對齊
- [ ] 數字靠右對齊
- [ ] 文字靠左對齊
- [ ] 固定欄位寬度確保表格整齊

#### 3. 顏色編碼 (使用 Rich 庫)
- [ ] 🟢 綠色：正數、上漲、多頭訊號
- [ ] 🔴 紅色：負數、下跌、空頭訊號
- [ ] 🟡 黃色：中性、警告
- [ ] 安裝 `rich` 庫：`pip install rich`

#### 4. 視覺化進度條
- [ ] SAPTA 分數顯示進度條
- [ ] RSI 等指標顯示進度條
- [ ] 範例：`████████░░░░░░░░ 34/100`

#### 5. 分組與區塊
- [ ] 技術分析按類別分組 (趨勢指標、動能指標、支撐壓力)
- [ ] 基本面分析按類別分組 (估值、獲利、成長、股利)
- [ ] 使用視覺分隔線區分區塊

#### 6. 快速摘要區
- [ ] 在詳細數據前加入一行摘要
- [ ] 範例：`📊 2330 台積電 | NT$1,710 📈+1.18% | 多頭 | RSI超買`

#### 7. 優先改善的命令
| 優先級 | 命令 | 原因 |
|--------|------|------|
| 1 | `/technical` | 最常用，指標多，需要分組 |
| 2 | `/fundamental` | 類別分組需改善 |
| 3 | `/sapta` | 模組分數可加進度條 |
| 4 | `/screen` | 結果列表需表格化 |

#### 8. 建議的技術實作方案
| 方案 | 優點 | 缺點 | 建議 |
|------|------|------|------|
| **Rich 庫** | 顏色、表格、進度條完整支援 | 需要新增依賴 | ⭐ 推薦 |
| **Textual 內建** | 已有依賴，整合度高 | 功能較限制 | 備選 |
| **純 Unicode** | 無需新依賴 | 無顏色支援 | 簡單場景 |

---

### 未來規劃 (可選)

- [ ] 添加實時數據支持 (WebSocket 或輪詢)
- [ ] 添加自選股和投資組合追蹤功能
- [ ] 添加價格警報通知
- [ ] 添加更多 FinMind 數據源 (例如：庫藏股、增減資資料)
- [ ] 支持基本面選股條件

---

## 技術規格

| 項目 | 規格 |
|------|------|
| **股票代碼格式** | 4-6位數字 (2330, 2454, 2317) |
| **Yahoo Finance 後綴** | .TW |
| **貨幣** | NT$ (台幣) |
| **語言** | 繁體中文 + 英文 |
| **主要數據源** | FinMind |
| **備用數據源** | Yahoo Finance |
| **交易單位** | 1張=1000股 |
| **ta 庫版本** | 0.5.25 (FinMind 兼容性) |

---

## 命令快速參考

```bash
# 安裝依賴
pip install -e ".[dev]"

# 運行 CLI
python -m pulse.cli.app

# 運行測試
python -m pytest tests/test_core/test_data/test_yfinance.py -v
```

### 可用命令

| 命令 | 別名 | 說明 | 需要 AI |
|------|------|------|---------|
| `/help` | h, ? | 查看可用命令 | ❌ |
| `/technical` | tech, ta | 技術分析 | ❌ |
| `/fundamental` | fund, fa | 基本面分析 | ❌ |
| `/institutional` | inst, flow | 法人動向 | ❌ |
| `/sapta` | premarkup | SAPTA 綜合分析 | ❌ |
| `/chart` | k, kline | K線圖 | ❌ |
| `/forecast` | pred | 價格預測 | ❌ |
| `/compare` | cmp, vs | 股票比較 | ❌ |
| `/taiex` | twii, index | 大盤指數 | ❌ |
| `/sector` | industry | 產業分析 | ❌ |
| `/screen` | scan | 股票篩選 | ❌ |
| `/plan` | trade | 交易計劃 | ❌ |
| `/analyze` | a, stock | AI 綜合分析 | ✅ |
| `/models` | model, m | 切換 AI 模型 | ✅ |
| `/clear` | cls | 清除聊天 | ❌ |

---

**Pulse-CLI 台灣股票市場分析工具** 🇹🇼

```bash
# 快速開始
pip install -e ".[dev]"
python -m pulse.cli.app
/help
```
