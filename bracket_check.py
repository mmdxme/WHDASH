#!/usr/bin/env python3
import ast

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# What if the issue is that line 21089 "}," is NOT actually closing the fa/ar dict?
# Let me check what the last few lines of the prefix look like more carefully

prefix = ''.join(lines[:21089])

# Try to find where the issue might be by checking bracket balance
open_brackets = 0
for i, line in enumerate(lines[:21089]):
    for c in line:
        if c == '{':
            open_brackets += 1
        elif c == '}':
            open_brackets -= 1

print(f"Bracket balance after line 21089: {open_brackets}")

# If brackets are unbalanced, which direction?
if open_brackets > 0:
    print(f"WARNING: {open_brackets} unclosed opening brackets!")
elif open_brackets < 0:
    print(f"WARNING: {abs(open_brackets)} more closing brackets than opening!")

# Let's also check: where does the fa/ar dict actually end?
# Find the line that closes fa/ar dict
for i in range(21080, 21095):
    print(f"Line {i+1}: {repr(lines[i])}")