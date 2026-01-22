---
description: 腳本開發規範 (PowerShell & Python)
---

# 腳本開發規範 (Windows 環境)

建立新的腳本時，請遵循以下規範以確保在 Windows 系統下的相容性與編碼正確。

## 1. PowerShell 腳本 (.ps1)

### 解決編碼與亂碼問題 (Golden Rule)
PowerShell 預設使用 Big5 (CP950) 編碼，但現代應用程式多為 UTF-8。

**規範：** 所有 `.ps1` 腳本的**第一行有效程式碼**必須設定主控台輸出編碼為 UTF-8。

```powershell
# 1. 設定主控台輸出編碼為 UTF-8 (避免亂碼與錯誤處理異常)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 建議：使用 try-catch block 處理錯誤
try {
    # 範例指令
    Get-NetTCPConnection -LocalPort 3000 -ErrorAction Stop
} catch {
    Write-Host "⚠️ 發生錯誤: $_" -ForegroundColor Yellow
}
```

---

## 2. Python 腳本 (.py)

### Windows 終端編碼修復 (必要)
如果腳本會輸出 Unicode 字元（如表情符號 ✓ ❌ ⚠️），必須在開頭加入編碼修復。

**規範：** 在所有 `import` 之前，或在腳本初始化階段呼叫編碼修復。

```python
import io
import sys

# 修復 Windows 終端編碼
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 或者使用專案內部的工具 (如有)
# from utils.console_encoding import fix_windows_encoding
# fix_windows_encoding()
```

---

## 3. 檢查清單

- [ ] **PowerShell**: 是否已加入 `[Console]::OutputEncoding`？
- [ ] **Python**: 是否已在任何 `print()` 之前加入編碼修復？
- [ ] **編碼**: 檔案是否存檔為 **UTF-8** 編碼？
