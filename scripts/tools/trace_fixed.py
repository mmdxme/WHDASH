#!/usr/bin/env python3

# Let me trace the exact dict structure in the fixed file

with open('translations_fixed_v4.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find where dicts open and close around line 21090
print("Looking for dict opens/closes around lines 21085-21100:")

balance = 0
for i in range(21084, 21102):
    if i >= len(lines):
        break
    line = lines[i]
    old_balance = balance

    # Check for dict structure in this line
    opens = line.count('{')
    closes = line.count('}')

    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    # Check if this is a language dict start
    is_lang = None
    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if f"'{lang}':" in line:
            is_lang = lang
            break

    print(f"Line {i+1}: balance {old_balance}->{balance}, opens={opens}, closes={closes}, {repr(line[:50])[:60]}, lang={is_lang}")