#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

# Try to parse lines 21090 onwards
lines = content.split('\n')
suffix = '\n'.join(lines[21089:])  # From line 21090 onwards (0-indexed)

try:
    import ast
    ast.parse(suffix)
    print("Lines 21090 onwards parse OK")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno} in suffix (actual line {e.lineno + 21089}): {e.msg}")
    # Show context
    suffix_lines = suffix.split('\n')
    start = max(0, e.lineno - 5)
    end = min(len(suffix_lines), e.lineno + 5)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        print(f"{marker} {i+1}: {suffix_lines[i][:80]}")