#!/usr/bin/env python3
import ast
import sys

try:
    with open('translations.py', 'r', encoding='utf-8') as f:
        content = f.read()
    ast.parse(content)
    print("translations.py parses OK")
except SyntaxError as e:
    print(f"FAIL: {e.msg} at line {e.lineno}")
    # Write error info to file
    lines = content.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 5)
    with open('parse_error_info.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error at line {e.lineno}: {e.msg}\n\n")
        f.write("Context:\n")
        for i in range(start, end):
            marker = '>>> ' if i == e.lineno - 1 else '    '
            f.write(f"{marker}{i+1}: {lines[i][:100]}\n")