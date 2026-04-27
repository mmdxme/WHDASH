#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# Create a test file with lines 1-21089 + properly formatted ru dict
test_content = ''.join(lines[:21090]) + "\n    'ru': {\n        # Test\n    }\n}\n"

try:
    import ast
    ast.parse(test_content)
    print("Test content parses OK!")
except SyntaxError as e:
    print(f"Test content fails at line {e.lineno}: {e.msg}")
    print("Content ending:")
    print(repr(test_content[-200:]))