#!/usr/bin/env python3
import ast

# Create test files with different line counts and see which one fails

test1 = """x = {
    'fa': {
        'key': 'value',
    },
}

y = {
    'ru': {
        'key': 'value',
    },
}
"""

test2 = """x = {
    'fa': {
        'key': 'value',
    },
}

    'ru': {
        'key': 'value',
    },
}
"""

test3 = """x = {
    'fa': {
        'key': 'value',
    },
}
    'ru': {
        'key': 'value',
    },
}
"""

for name, content in [("test1", test1), ("test2", test2), ("test3", test3)]:
    try:
        ast.parse(content)
        print(f"{name}: parses OK")
    except SyntaxError as e:
        print(f"{name}: FAIL - {e.msg} at line {e.lineno}")