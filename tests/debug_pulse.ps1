$ErrorActionPreference = "Stop"

# 設定編碼為 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🔄 Starting Pulse in DEBUG mode..." -ForegroundColor Cyan

# 確認虛擬環境存在
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "❌ Virtual environment not found at .venv\Scripts\python.exe"
    exit 1
}

# 強制使用虛擬環境的 Python 啟動模組
# 這確保了我們修改的代碼（包含日誌功能）一定會被執行
& ".\.venv\Scripts\python.exe" -m pulse.cli.app

Write-Host "`n✅ Pulse process exited." -ForegroundColor Green
Write-Host "📂 Please check logs/pulse.log for output." -ForegroundColor Yellow
