#!/usr/bin/env python3

# Full bracket trace to find where the problem starts

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track bracket balance line by line
balance = 0
min_balance = 0
min_line = 0
problems = []

for i, line in enumerate(lines[:21089]):
    old_balance = balance
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    if balance < min_balance:
        min_balance = balance
        min_line = i + 1

    # If balance goes negative, that's a problem
    if balance < 0:
        problems.append((i+1, balance, line.strip()[:50]))

print(f"Minimum balance: {min_balance} at line {min_line}")

if problems:
    print(f"\nFound {len(problems)} negative balance points:")
    for ln, bal, text in problems[:20]:
        print(f"  Line {ln}: balance={bal}, {text}")

# Show bracket balance at key language boundaries
boundaries = [
    ('en dict', 7, 8),
    ('fa dict', 8184, 8185),
    ('ar dict', 14739, 14740),
    ('ru dict', 21088, 21089),  # Before ru dict
]

for name, check_line, close_line in boundaries:
    b = 0
    for i in range(check_line):
        for c in lines[i]:
            if c == '{':
                b += 1
            elif c == '}':
                b -= 1
    print(f"\n{name} - bracket balance at line {check_line}: {b}")

# What if we try to parse just up to line 21089 (before the empty line)?
test_content = ''.join(lines[:21089])
import ast
try:
    ast.parse(test_content)
    print("\nPrefix (lines 1-21089) parses OK")
except SyntaxError as e:
    print(f"\nPrefix (lines 1-21089) FAILS: {e.msg} at line {e.lineno}")