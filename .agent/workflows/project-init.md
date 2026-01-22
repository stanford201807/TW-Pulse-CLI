---
description: 初始化專案 Agent 規範 (包含自動檢查 workflows)
---

# 專案初始化規範 (Project Initialization)

本工作流程用於確保新專案或現有專案符合 Antigravity Agent 的開發標準。
特別是確保 **PowerShell** 與 **Python** 的編碼規範已被導入。

## 1. 檢查與建立 Workflows

執行此初始化時，需檢查以下必要的 Workflow 檔案是否存在。若不存在，必須建立之。

### A. PowerShell 規範 (`.agent/workflows/powershell-script.md`)

- **檢查**：是否存在 `.agent/workflows/powershell-script.md`
- **行動**：若不存在，請建立該檔案，內容必須包含 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8` 的 Golden Rule。
- **參考內容**：
  ```markdown
  ---
  description: 建立新 PowerShell 腳本的規範
  ---
  # PowerShell 腳本開發規範
  [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
  ```

### B. Python 規範 (`.agent/workflows/python-script.md`)

- **檢查**：是否存在 `.agent/workflows/python-script.md`
- **行動**：若不存在，請建立該檔案，內容必須包含 `sys.stdout` 編碼修復的指導。

## 2. 專案結構檢查

// turbo
檢查是否包含標準目錄結構 (視專案類型而定)：
- [ ] `.agent/workflows/`
- [ ] `.gemini/` (Artifacts 存放區)

## 3. 執行指令

若您是 Agent 且正在讀取此文件，請執行以下檢查：

1. 確保上述文件已就緒。
2. 檢查專案跟目錄 '*.ps1`，檢查是否已套用 UTF-8 編碼修正。