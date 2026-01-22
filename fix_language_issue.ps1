# Pulse 語言問題快速修復腳本
# 用途：清除緩存並驗證提示詞版本

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Pulse 語言問題快速修復工具" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 清除 Python 緩存
Write-Host "[1/3] 清除 Python 緩存..." -ForegroundColor Yellow
$cacheCount = 0
Get-ChildItem -Path "pulse" -Filter "__pycache__" -Recurse -Directory | ForEach-Object {
    $cacheCount++
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "  已刪除: $($_.FullName)" -ForegroundColor Gray
}

if ($cacheCount -eq 0) {
    Write-Host "  沒有找到緩存目錄" -ForegroundColor Gray
} else {
    Write-Host "  已清除 $cacheCount 個緩存目錄" -ForegroundColor Green
}
Write-Host ""

# 步驟 2: 驗證提示詞版本
Write-Host "[2/3] 驗證提示詞版本..." -ForegroundColor Yellow
Write-Host "  正在檢查 pulse/ai/prompts.py..." -ForegroundColor Gray

$promptsFile = "pulse\ai\prompts.py"
$content = Get-Content $promptsFile -Raw -Encoding UTF8

$checks = @{
    "新版語言要求 (絕對語言要求)" = $content -match "絕對語言要求"
    "繁體中文指令" = $content -match "你「必須」且「只能」使用繁體中文回答"
    "禁止印尼語說明" = $content -match "印尼語"
    "Emoji 強調" = $content -match "🚨"
    "結尾提醒" = $content -match "🔴 再次提醒"
}

$allPassed = $true
foreach ($check in $checks.GetEnumerator()) {
    if ($check.Value) {
        Write-Host "  [OK] $($check.Key)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $($check.Key)" -ForegroundColor Red
        $allPassed = $false
    }
}
Write-Host ""

# 步驟 3: 測試 AI 回應
Write-Host "[3/3] 測試 AI 回應語言..." -ForegroundColor Yellow
Write-Host "  執行測試腳本..." -ForegroundColor Gray

try {
    $testResult = & ".\.venv\Scripts\python.exe" "test_ai_language_response.py" 2>&1
    $testOutput = $testResult -join "`n"
    
    if ($testOutput -match "\[SUCCESS\]") {
        Write-Host "  [SUCCESS] AI 正確使用繁體中文" -ForegroundColor Green
    } elseif ($testOutput -match "\[FAILED\]") {
        Write-Host "  [FAILED] AI 仍使用印尼語" -ForegroundColor Red
    } else {
        Write-Host "  [WARNING] 測試結果不明確" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] 測試腳本執行失敗: $_" -ForegroundColor Red
}
Write-Host ""

# 總結
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "修復摘要" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host ""
    Write-Host "✓ 提示詞版本: 最新" -ForegroundColor Green
    Write-Host "✓ Python 緩存: 已清除" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步驟：" -ForegroundColor Yellow
    Write-Host "1. 如果 Pulse 正在運行，請重新啟動應用程式" -ForegroundColor White
    Write-Host "2. 在 Pulse 中執行: /clear" -ForegroundColor White
    Write-Host "3. 測試命令: /analyze 2303" -ForegroundColor White
    Write-Host ""
    Write-Host "預期結果：應該輸出繁體中文分析" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "✗ 發現問題：提示詞文件可能未正確更新" -ForegroundColor Red
    Write-Host ""
    Write-Host "建議動作：" -ForegroundColor Yellow
    Write-Host "1. 確認 pulse/ai/prompts.py 文件已儲存" -ForegroundColor White
    Write-Host "2. 重新執行此腳本" -ForegroundColor White
}

Write-Host ""
Write-Host "詳細診斷報告：印尼語問題完整診斷報告.md" -ForegroundColor Gray
Write-Host "============================================" -ForegroundColor Cyan
