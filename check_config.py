import ast
import sys

# 讀取 config.py
with open('pulse/core/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析 AST
tree = ast.parse(content)

# 尋找 AISettings 類別
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == 'AISettings':
        # 尋找 available_models 欄位
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name) and item.target.id == 'available_models':
                    # 取得 Field 呼叫
                    if isinstance(item.value, ast.Call):
                        for keyword in item.value.keywords:
                            if keyword.arg == 'default' and isinstance(keyword.value, ast.Dict):
                                print(f"找到 available_models 字典，共 {len(keyword.value.keys)} 個鍵:")
                                for i, (k, v) in enumerate(zip(keyword.value.keys, keyword.value.values)):
                                    if isinstance(k, ast.Constant) and 'gemini' in k.value.lower():
                                        print(f"  {i+1}. {k.value}: {v.value if isinstance(v, ast.Constant) else '???'}")
