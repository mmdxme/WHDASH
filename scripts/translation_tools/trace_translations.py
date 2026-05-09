#!/usr/bin/env python3

# Let's trace the bracket balance more carefully to find where TRANSLATIONS closes

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track bracket balance from the start
balance = 0
translations_open_line = None
translations_close_line = None

for i, line in enumerate(lines):
    old_balance = balance
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    # Check if this is where TRANSLATIONS = { is
    if "'ru':" in line and balance == 1:
        translations_open_line = i + 1

    # Check if this is where TRANSLATIONS closes (balance goes back to 0)
    if balance == 0 and old_balance == 1:
        translations_close_line = i + 1

print(f"TRANSLATIONS dict opens at line: {translations_open_line}")
print(f"TRANSLATIONS dict closes at line: {translations_close_line}")

# If translations never closes, then when we reach line 21091, balance should still be > 0
# But earlier we saw balance is 0 at line 21089

# Let me trace more carefully around the closing area
print("\nBracket balance trace around lines 21085-21100:")
balance = 0
for i in range(21084, 21100):
    line = lines[i]
    old_balance = balance
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    print(f"Line {i+1}: balance went from {old_balance} to {balance}, {repr(line[:50])[:60]}")