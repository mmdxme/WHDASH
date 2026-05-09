#!/usr/bin/env python3

# Simple fix: remove lines 21031-21090 (the malformed 8-space section)

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep lines 1-21030 (0-indexed: 0-21029)
# Skip lines 21031-21090 (0-indexed: 21030-21089) - the malformed section
# Keep lines 21091 onwards (0-indexed: 21090+)

fixed_lines = lines[:21030] + lines[21090:]

# Write fixed file
with open('translations_fixed_v6.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

# Verify
import ast
try:
    ast.parse(''.join(fixed_lines))
    print("Fixed content parses OK!")
    print(f"Original lines: {len(lines)}")
    print(f"Fixed lines: {len(fixed_lines)}")
except SyntaxError as e:
    print(f"Fixed content FAILS: {e.msg} at line {e.lineno}")