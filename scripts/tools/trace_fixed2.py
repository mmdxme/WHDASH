#!/usr/bin/env python3

# Let me trace the exact dict structure in the fixed file

with open('translations_fixed_v4.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find where dicts open and close around line 21090
output = []
output.append("Looking for dict opens/closes around lines 21085-21100:")

balance = 0
for i in range(21084, 21102):
    if i >= len(lines):
        break
    line = lines[i]
    old_balance = balance

    opens = line.count('{')
    closes = line.count('}')

    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    is_lang = None
    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if f"'{lang}':" in line:
            is_lang = lang
            break

    ascii_line = ''.join(c if ord(c) < 128 else '?' for c in line[:50])
    output.append(f"Line {i+1}: bal {old_balance}->{balance}, op={opens}, cl={closes}, {ascii_line}, lang={is_lang}")

with open('trace_fixed_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))