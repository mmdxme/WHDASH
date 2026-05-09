#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# Check bracket balance carefully
open_brackets = 0
for i, line in enumerate(lines[:21089]):
    for c in line:
        if c == '{':
            open_brackets += 1
        elif c == '}':
            open_brackets -= 1

print(f"Bracket balance after line 21089: {open_brackets}")
print(f"Line 21089 ends with: {repr(lines[21088])}")
print(f"Line 21090 (empty/blank): {repr(lines[21089])}")