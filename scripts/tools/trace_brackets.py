#!/usr/bin/env python3

# Let's trace bracket balance line by line to find where the unclosed { appears

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track bracket balance
balance = 0
min_balance = 0
min_balance_line = 0

for i, line in enumerate(lines[:21089]):
    # Count opens and closes in this line
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    if balance < min_balance:
        min_balance = balance
        min_balance_line = i + 1

print(f"Minimum bracket balance: {min_balance} at line {min_balance_line}")

# Also show bracket balance at key points
for test_line in [8185, 14740, 14741, 21088, 21089]:
    b = 0
    for i in range(test_line):
        for c in lines[i]:
            if c == '{':
                b += 1
            elif c == '}':
                b -= 1
    print(f"Bracket balance at line {test_line}: {b}")

# Also check: is there a { without a matching } before line 21089?
# Let's find any line with unclosed brackets
print("\nLooking for problematic lines...")
open_count = 0
for i in range(21089):
    line = lines[i]
    line_opens = line.count('{')
    line_closes = line.count('}')
    if line_closes > line_opens:
        open_count -= (line_closes - line_opens)
    else:
        open_count += (line_opens - line_closes)

print(f"Open bracket count before line 21089: {open_count}")