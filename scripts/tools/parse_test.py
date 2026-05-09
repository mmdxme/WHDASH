#!/usr/bin/env python3
import ast

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# Test: does lines 1-21089 parse on its own?
prefix = ''.join(lines[:21089])
try:
    ast.parse(prefix)
    print("Lines 1-21089 parse OK")
except SyntaxError as e:
    print(f"Lines 1-21089 FAIL: {e.msg} at line {e.lineno}")

# Test: does the original translations.py content parse?
full_content = ''.join(lines)
try:
    ast.parse(full_content)
    print("Full file parses OK")
except SyntaxError as e:
    print(f"Full file FAIL: {e.msg} at line {e.lineno}")
    # Show context around error line
    full_lines = full_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(full_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        line_content = full_lines[i].encode('ascii', errors='replace').decode('ascii')
        print(f"{marker} {i+1}: {line_content[:80]}")