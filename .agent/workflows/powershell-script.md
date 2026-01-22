---
description: 建立新 PowerShell 腳本的規範
---
# PowerShell 腳本開發規範

## 🔧 編碼設定 (CRITICAL)

### 1. 腳本開頭必須包含編碼宣告

所有 PowerShell 腳本 **必須** 在開頭包含以下兩行：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

> [!IMPORTANT]
> 這兩行設定確保 PowerShell 輸出和管線處理繁體中文時不會亂碼。

### 2. 檔案儲存編碼必須為 UTF-8 with BOM

所有 `.ps1` 檔案 **必須** 以 `UTF-8 with BOM` 編碼儲存，否則會導致：
- 繁體中文變成亂碼（如 `蝔?撌脩???`）
- PowerShell 解析器錯誤（如 `字串遺漏結尾字元`）

## 🛠️ 編碼修正方法

### 方法 1：使用 PowerShell 命令修正現有檔案

如果發現腳本出現亂碼或解析錯誤，執行以下命令修正：

```powershell
$content = Get-Content -Path ".\your-script.ps1" -Raw -Encoding UTF8
[System.IO.File]::WriteAllText(".\your-script.ps1", $content, (New-Object System.Text.UTF8Encoding $true))
```

將 `your-script.ps1` 替換為實際檔案名稱。

### 方法 2：使用 VSCode 設定預設編碼

在 VSCode 中開啟設定（`settings.json`），加入：

```json
{
  "files.encoding": "utf8bom",
  "[powershell]": {
    "files.encoding": "utf8bom"
  }
}
```

### 方法 3：建立新檔案時直接使用正確編碼

使用 `write_to_file` 工具建立 PowerShell 腳本時，建立後必須執行編碼修正命令。

## ✅ 最佳實踐

1. **建立腳本後立即修正編碼**：每次建立新的 `.ps1` 檔案後，立即執行編碼修正命令
2. **驗證編碼**：執行腳本前先檢查是否有亂碼或解析錯誤
3. **統一編碼規範**：專案中所有 PowerShell 腳本使用相同編碼標準

## 🚨 常見問題排除

| 錯誤訊息 | 原因 | 解決方法 |
|---------|------|---------|
| `字串遺漏結尾字元` | 檔案編碼不是 UTF-8 BOM | 使用方法 1 修正編碼 |
| 中文顯示為亂碼 | 缺少編碼宣告或檔案編碼錯誤 | 加入編碼宣告 + 修正檔案編碼 |
| `ParserError` | 編碼問題導致解析失敗 | 重新儲存為 UTF-8 BOM |
