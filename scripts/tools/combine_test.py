#!/usr/bin/env python3
import ast

# Read the first 21089 lines of translations.py
with open('translations.py', 'rb') as f:
    raw = f.read()

lines = raw.decode('utf-8').split('\n')

# Take first 21089 lines (which parse OK)
prefix = '\n'.join(lines[:21089])

# Add a properly formatted ru dict
suffix = """
    'ru': {
        # Test
        'test': 'Test value',
    },
}
"""

# Combine
test_content = prefix + suffix

try:
    ast.parse(test_content)
    print("Combined content parses OK!")
except SyntaxError as e:
    print(f"Combined content fails at line {e.lineno}: {e.msg}")
    # Show context
    all_lines = test_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(all_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        print(f"{marker} {i+1}: {all_lines[i][:80]}")