#!/usr/bin/env python3
import ast

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Binary search to find where it breaks
def can_parse_up_to(line_num):
    try:
        prefix = '\n'.join(lines[:line_num])
        ast.parse(prefix)
        return True
    except SyntaxError:
        return False

# Test some key points
test_points = [8000, 10000, 12000, 14000, 14700, 14739, 14740, 14741, 20000, 21089]
for tp in test_points:
    result = can_parse_up_to(tp)
    print(f"Lines 1-{tp}: {'OK' if result else 'FAIL'}")