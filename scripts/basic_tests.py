#!/usr/bin/env python3
import ast

# Very basic tests
tests = [
    ("Dict literal", "{'ru': {}}"),
    ("Dict literal with newline", "{\n    'ru': {\n    }\n}"),
    ("Dict literal with closing", "    'ru': {\n    }\n"),
    ("Simple dict", "x = {'ru': {}}"),
    ("Indented dict", "    {'ru': {}}"),
    ("Indented dict 2", "    'ru': {}"),
    ("Indented dict 3", "    'ru': {\n    }"),
    ("Indented dict 4", "    'ru': {\n        'key': 'value'\n    }"),
    ("Just the ru line", "    'ru': {"),
]

for name, code in tests:
    try:
        ast.parse(code)
        print(f"OK: {name}: {repr(code[:40])}")
    except SyntaxError as e:
        print(f"FAIL: {name}: {e.msg}")