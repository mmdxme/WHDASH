#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

# Try to parse first 21089 lines
lines = content.split('\n')
prefix = '\n'.join(lines[:21089])

try:
    import ast
    ast.parse(prefix)
    print("First 21089 lines parse OK")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno} in prefix (actual line {e.lineno}): {e.msg}")
    # Show context
    prefix_lines = prefix.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(prefix_lines), e.lineno + 5)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        print(f"{marker} {i+1}: {prefix_lines[i][:80]}")