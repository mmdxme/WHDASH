#!/usr/bin/env python3

# Check: what dict is at 8-space indent around line 21031?

with open('translations_normalized.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Show lines around 21031 with indentation info
print("Lines around 21031:")
for i in range(21025, 21040):
    if i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip())
        ascii_content = ''.join(c if ord(c) < 128 else '?' for c in line[:60])
        print(f"Line {i+1}: indent={indent}, {ascii_content}")

# Also check: find what dict structure "e-commerce" is part of
print("\n\nSearching for 'e_commerce' or 'ecommerce' section headers:")
for i, line in enumerate(lines[:21092]):
    if 'E-COMMERCE' in line or 'ecommerce' in line.lower():
        indent = len(line) - len(line.lstrip())
        print(f"Line {i+1}: indent={indent}, {repr(line[:60])}")