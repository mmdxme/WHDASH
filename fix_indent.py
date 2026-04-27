#!/usr/bin/env python3

# Fix the indentation issue in translations.py

# The problem is that after line 21029 (ar dict close with 4-space indent),
# the E-commerce section (lines 21031 onwards) has 8-space indent instead of 4-space
# This causes the parser to think we're inside a nested dict, not at the TRANSLATIONS top level

# Fix: change 8-space indent to 4-space in the section between ar dict close and ru dict start

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines to fix: 21031 to 21090 (0-indexed: 21030 to 21089)
# These should be at 4-space indent, not 8-space

fixed_lines = []
for i, line in enumerate(lines):
    # Lines 21031-21090 (0-indexed: 21030-21089)
    if 21030 <= i <= 21089:
        # Change 8-space indent to 4-space
        if line.startswith('        '):  # 8 spaces
            fixed_lines.append(line[4:])  # Remove first 4 spaces
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write fixed file
with open('translations_fixed_v4.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

# Verify
import ast
try:
    ast.parse(''.join(fixed_lines))
    print("SUCCESS: Fixed content parses OK!")
except SyntaxError as e:
    print(f"Still fails: {e.msg} at line {e.lineno}")
    # Show context
    all_lines = ''.join(fixed_lines).split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(all_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        print(f"{marker} {i+1}: {repr(all_lines[i][:80])}")