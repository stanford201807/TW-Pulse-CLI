---
description: 建立新 Python 腳本的規範
---
# Python 腳本開發規範

在 Windows 環境下執行 Python 時，為避免 stdout 亂碼，建議在進入點加入：

```python
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```
