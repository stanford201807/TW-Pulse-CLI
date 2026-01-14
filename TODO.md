# Pulse-CLI 台灣股票分析工具

> **最後更新**: 2026-01-14
> **整體進度**: 核心功能 100% 完成

---

## 專案概述

**Pulse-CLI** 是一個台灣股票市場分析的命令列工具 (TUI)，提供技術分析、基本面分析、法人動向、SAPTA 預測引擎等功能。

### 技術架構
```
pulse/
├── cli/           # Textual TUI 介面
├── core/
│   ├── analysis/  # 技術分析、基本面、法人動向
│   ├── data/      # FinMind + Yahoo Finance 數據層
│   ├── sapta/     # SAPTA 預測引擎 (6個模組 + ML)
│   └── screener/  # 股票篩選器
└── utils/         # 格式化輸出工具
```

### 數據來源
| 來源 | 用途 | 備註 |
|------|------|------|
| **FinMind** | 法人動向、融資融券 | 主要來源，有 API 配額限制 |
| **Yahoo Finance** | 股價、技術指標 | 備援來源，無限制 |

---

## 可用命令

| 命令 | 別名 | 說明 |
|------|------|------|
| `/help` | h, ? | 查看可用命令 |
| `/technical` | tech, ta | 技術分析 (RSI, MACD, BB) |
| `/fundamental` | fund, fa | 基本面分析 (PE, ROE, 殖利率) |
| `/institutional` | inst, flow | 法人動向 (需 FinMind API) |
| `/sapta` | premarkup | SAPTA 綜合預測分析 |
| `/screen` | scan | 股票篩選 (超買/超賣/突破) |
| `/chart` | k, kline | K線圖 (輸出 PNG) |
| `/forecast` | pred | 價格預測 |
| `/compare` | cmp, vs | 多檔股票比較 |
| `/taiex` | twii, index | 大盤指數資訊 |
| `/sector` | industry | 產業分析 |
| `/plan` | trade | 交易計劃生成 |
| `/clear` | cls | 清除聊天 |
| `/exit` | quit, q | 退出程式 |

---

## 2026-01-14 更新記錄

### 修復項目
- [x] 命令註冊修復 (11個命令)
- [x] SAPTA BollingerBands ta 庫參數修復 (`n`/`ndev`)
- [x] CLI 輸出繁體中文化
- [x] Windows emoji 相容性 (fallback 機制)
- [x] 循環導入警告修復 (`__init__.py` lazy import)

### 新增功能
- [x] `/exit` 退出指令 (別名: quit, q)
- [x] 股票篩選器使用 constants.py 股票清單
- [x] 簡潔條列式輸出格式 (取代表格)

### 股票篩選器 Universe
| 參數 | 股票數 | 說明 |
|------|--------|------|
| `--universe=tw50` | 50 檔 | 台灣50成分股 |
| `--universe=midcap` | 29 檔 | 中型股 |
| `--universe=popular` | 76 檔 | 熱門股 |
| `--universe=all` | 102 檔 | 全部 |

---

## 已知限制

1. **FinMind API 配額**: 免費版有請求上限，法人動向功能可能受限
2. **AI 分析功能**: 需要本地 AI 服務 (localhost:8317)

---

## 快速開始

```bash
# 安裝
pip install -e ".[dev]"

# 運行
python -m pulse.cli.app

# 常用命令
/help              # 查看說明
/technical 2330    # 台積電技術分析
/sapta 2330        # SAPTA 分析
/screen oversold   # 篩選超賣股
/exit              # 退出
```

---

## 未來規劃 (可選)

- [ ] 實時數據支持 (WebSocket)
- [ ] 自選股追蹤功能
- [ ] 價格警報通知
- [ ] 更多 FinMind 數據源

---

**Pulse-CLI 台灣股票市場分析工具** 🇹🇼
