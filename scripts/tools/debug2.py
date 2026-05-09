#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# Check 21085 to 21095
print("Checking lines 21085-21095:")
for i in range(21084, 21095):
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    has_tabs = '\t' in line
    has_spaces = ' ' in line
    # Show char codes for first 20 chars
    first_chars = [ord(c) for c in line[:20] if c not in ' \t\n']
    print(f'{i+1}: indent={indent}, tabs={has_tabs}, spaces={has_spaces}, non-whitespace chars={first_chars[:5]}')

# Check if maybe there's an issue around 21089
print("\nDetailed check of line 21089-21092:")
for i in range(21088, 21092):
    line = lines[i]
    print(f"Line {i+1}:")
    print(f"  repr: {repr(line[:60])}")
    print(f"  len: {len(line)}")