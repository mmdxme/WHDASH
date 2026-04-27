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

output = []
output.append(f"Bracket balance after line 21089: {open_brackets}")

# Find the line that closes fa/ar dict
output.append("\nLines 21085-21095:")
for i in range(21084, 21094):
    content = repr(lines[i])
    output.append(f"Line {i+1}: {content}")

with open('bracket_output.txt', 'w') as f:
    f.write('\n'.join(output))