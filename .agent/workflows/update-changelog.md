---
description: 更新 changelog.md 文檔，記錄專案變更歷史
---

# 更新 Changelog Workflow

當完成功能開發、修復 Bug 或進行重構後，使用此 workflow 更新 `changelog.md`。

## 工作流程步驟

### 1. 確認變更範圍
在更新 changelog 之前，先確認：
- 本次變更涉及哪些模組/檔案？
- 變更類型是什麼？（新增功能、Bug 修復、重構、優化）
- 是否有 Breaking Changes？

### 2. 格式規範
遵循以下格式新增 changelog 條目：

```markdown
## [YYYY-MM-DD] - 簡短標題 (英文關鍵字)

### 🚀 新增功能與改進
- **功能名稱**：簡要說明功能與實作方式。

### 🐛 Bug 修復
- 修復「問題描述」。

### 🔧 優化與調整
- 優化項目說明。

### ⚠️ Breaking Changes (如有)
- 說明不兼容的變更與遷移方式。
```

### 3. 常用 Emoji 標籤
| Emoji | 用途 |
|-------|------|
| 🚀 | 新增功能 |
| 🐛 | Bug 修復 |
| 🔧 | 優化調整 |
| 📂 | 檔案結構變更 |
| 🔄 | 重構 |
| ⚠️ | Breaking Changes |
| 📝 | 文檔更新 |

### 4. 更新位置
// turbo
新的條目應加在 `changelog.md` 的**最上方**（現有內容之前），按時間倒序排列。

### 5. 範例條目
```markdown
## [2026-01-14] - 命名衝突修復 (Module Conflict Fix)

### 🐛 Bug 修復
- 修復 `core/strategy.py` 與 `core/strategy/` 目錄的命名衝突問題。
- 將 `strategy.py` 重新命名為 `grid_strategy.py`。

### 🔧 優化與調整
- 新增 `core/strategy/__init__.py` 與 `core/strategy/optimizers/__init__.py`。
- 更新所有相關檔案的 import 路徑。
```

### 6. 完成後檢查
- [ ] 日期格式正確 (`[YYYY-MM-DD]`)
- [ ] 標題簡潔且包含英文關鍵字
- [ ] 分類正確（新增/修復/優化）
- [ ] 內容清晰易懂
