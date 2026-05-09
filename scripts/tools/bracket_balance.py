#!/usr/bin/env python3

# Check bracket balance in the prefix more carefully

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Get the prefix (lines 1-21089, which is index 0-21088)
lines = content.split('\n')
prefix = '\n'.join(lines[:21089])

# Count brackets in prefix
open_curly = 0
open_bracket = 0
open_paren = 0

for c in prefix:
    if c == '{':
        open_curly += 1
    elif c == '}':
        open_curly -= 1
    elif c == '[':
        open_bracket += 1
    elif c == ']':
        open_bracket -= 1
    elif c == '(':
        open_paren += 1
    elif c == ')':
        open_paren -= 1

print(f"Bracket balance after line 21089:")
print(f"  Curly braces: {open_curly} (positive = unclosed)")
print(f"  Square brackets: {open_bracket} (positive = unclosed)")
print(f"  Parentheses: {open_paren} (positive = unclosed)")

# Now let's try a binary search to find where the issue is
# Test parsing lines 1-N for increasing N
import ast

def can_parse(n):
    test = '\n'.join(lines[:n])
    try:
        ast.parse(test)
        return True
    except:
        return False

# Binary search for the failure point
low = 21080
high = 21095
while low < high:
    mid = (low + high) // 2
    if can_parse(mid):
        low = mid + 1
    else:
        high = mid

print(f"\nFirst line that fails: {low}")
print(f"Lines around failure point:")
for i in range(max(0, low-3), min(len(lines), low+3)):
    print(f"  {i+1}: {repr(lines[i][:60])}")