#!/usr/bin/env python3

# Final check: what exactly is at line 21029?

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 21025-21035 (1-indexed)
print("Lines 21025-21035:")
for i in range(21024, 21035):
    line = lines[i]
    ascii_line = ''.join(c if ord(c) < 128 else '?' for c in line[:80])
    print(f"Line {i+1}: {ascii_line}")

# Also check: what dict closes at line 21029?
# The balance goes from 2 to 1 at line 21029
# That means there were 2 opens and 1 close - something opened at this line

# Actually, wait - the balance trace said "Line 21029: ar dict CLOSED"
# But balance AFTER line 21029 (before line 21030) is 1
# Then balance goes to 0 at some point

# Let me check: when is the ar dict actually closing?
print("\n\nBracket balance around ar dict close:")
balance = 0
for i in range(21024, 21035):
    line = lines[i]
    old_balance = balance
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1
    print(f"Line {i+1}: {old_balance} -> {balance}, {repr(line[:40])[:60]}")