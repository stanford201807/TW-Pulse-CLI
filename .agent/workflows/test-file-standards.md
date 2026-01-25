---
description: 測試文件建立規範
---

# 測試文件建立規範

## 基本原則

在建立任何測試文件時，必須遵循以下規範：

### 1. 檢查 tests 資料夾是否存在

在建立測試文件前，**必須先確認** `tests` 資料夾是否存在：

```powershell
# 檢查 tests 資料夾
Test-Path "d:\GitHub\TW-Pulse-CLI\tests"
```

如果不存在，則不應建立測試文件，或應先提醒使用者。

### 2. 測試文件位置規範

所有測試文件**必須建立於 `tests` 資料夾內**，不得建立於專案根目錄或其他位置。

**正確範例**：
```
✅ d:\GitHub\TW-Pulse-CLI\tests\test_backtest_output.py
✅ d:\GitHub\TW-Pulse-CLI\tests\test_cli\test_strategy_command.py
✅ d:\GitHub\TW-Pulse-CLI\tests\integration\test_api.py
```

**錯誤範例**：
```
❌ d:\GitHub\TW-Pulse-CLI\test_backtest_output.py          (根目錄)
❌ d:\GitHub\TW-Pulse-CLI\pulse\test_something.py          (業務邏輯資料夾內)
❌ d:\GitHub\TW-Pulse-CLI\tmp\test_temp.py                 (臨時資料夾)
```

### 3. 測試文件命名規範

測試文件必須遵循以下命名規範：

- **檔名格式**：`test_*.py` 或 `*_test.py`
- **類別名稱**：`Test*` 或 `*Test`
- **函數名稱**：`test_*`

範例：
```python
# 檔名: tests/test_strategy_backtest.py

class TestStrategyBacktest:
    """策略回測測試"""
    
    def test_farmer_strategy_backtest(self):
        """測試農夫策略回測"""
        pass
    
    def test_backtest_output_format(self):
        """測試回測輸出格式"""
        pass
```

### 4. 測試資料夾結構

建議的測試資料夾結構：

```
tests/
├── test_cli/               # CLI 相關測試
│   ├── test_commands.py
│   └── test_strategy_command.py
├── test_core/              # 核心邏輯測試
│   ├── test_strategies/
│   │   └── test_farmer_planting.py
│   └── test_backtest/
│       ├── test_engine.py
│       └── test_report.py
├── test_data/              # 數據處理測試
│   └── test_yfinance.py
└── integration/            # 整合測試
    └── test_end_to_end.py
```

### 5. 測試文件內容規範

每個測試文件應包含：

1. **模組文件字串（Docstring）**：說明測試目的
2. **必要的 import**：包含 pytest 或相關測試框架
3. **測試類別/函數**：明確的測試案例
4. **斷言（Assertions）**：清楚的驗證邏輯

範例：
```python
"""策略回測輸出測試

測試策略回測功能是否能正確輸出報告。
"""
import pytest
from pulse.core.backtest import BacktestEngine
from pulse.core.strategies import FarmerPlantingStrategy


class TestBacktestOutput:
    """回測輸出測試"""
    
    @pytest.mark.asyncio
    async def test_backtest_generates_report(self):
        """測試回測能產生報告"""
        strategy = FarmerPlantingStrategy()
        engine = BacktestEngine(strategy=strategy, ticker="2330.TW")
        
        report = await engine.run()
        
        assert report is not None
        assert report.total_return is not None
        assert len(report.trades) >= 0
```

## 執行規範

### 在建立測試文件前：

1. **檢查 tests 資料夾**
   ```python
   from pathlib import Path
   
   tests_dir = Path("d:/GitHub/TW-Pulse-CLI/tests")
   if not tests_dir.exists():
       print("❌ tests 資料夾不存在")
       # 詢問使用者或停止操作
   ```

2. **確認測試分類**
   - 單元測試 → `tests/test_*/`
   - 整合測試 → `tests/integration/`
   - CLI 測試 → `tests/test_cli/`

3. **使用正確路徑**
   ```python
   # 正確
   test_file = Path("d:/GitHub/TW-Pulse-CLI/tests/test_backtest_output.py")
   
   # 錯誤
   test_file = Path("d:/GitHub/TW-Pulse-CLI/test_backtest_output.py")
   ```

## 禁止事項

❌ **絕對不要**將測試文件建立於：
- 專案根目錄
- `pulse/` 業務邏輯資料夾內
- `.venv/` 虛擬環境資料夾內
- 任何非 `tests/` 的位置

❌ **絕對不要**建立沒有 `test_` 前綴的測試文件

❌ **絕對不要**在未確認 `tests` 資料夾存在的情況下建立測試文件

## 驗證步驟

建立測試文件後，應執行以下驗證：

```powershell
# 1. 確認文件位置正確
Test-Path "d:\GitHub\TW-Pulse-CLI\tests\test_*.py"

# 2. 執行測試
cd d:\GitHub\TW-Pulse-CLI
.venv\Scripts\python -m pytest tests/ -v

# 3. 檢查測試覆蓋率（選用）
.venv\Scripts\python -m pytest tests/ --cov=pulse --cov-report=term
```

## 參考資料

- [pytest 官方文檔](https://docs.pytest.org/)
- [Python 測試最佳實踐](https://docs.python-guide.org/writing/tests/)
