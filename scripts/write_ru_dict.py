#!/usr/bin/env python3

# Let me try creating a properly working version

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check if the file has BOM
with open('translations_normalized.py', 'rb') as f:
    first_bytes = f.read(3)
    has_bom = first_bytes == b'\\xef\\xbb\\xbf'
    print(f"Has UTF-8 BOM: {has_bom}")

# Let's try a simple approach: rewrite the last part of the file properly
# Find the ar dict close (line 21089, index 21088)
# Then add proper ru dict

# First, create a prefix that definitely works
prefix = ''.join(lines[:21089])
print(f"Prefix length: {len(prefix)} chars")

# Add a properly formatted ru dict
# The ru dict structure should mirror the other language dicts
ru_dict = """
    'ru': {
        # Navigation
        'app_name': 'Corporate Center',
        'app_subtitle': 'Warehouse Management System',
        'search_placeholder': 'Search in menu...',
        'hub_intelligence': 'Hub Intelligence',
    },
"""
print(f"ru_dict length: {len(ru_dict)} chars")

# Combine
full_content = prefix + ru_dict + "}\n"

# Write to test file
with open('test_ru_dict.py', 'w', encoding='utf-8') as f:
    f.write(full_content)

# Try to parse
import ast
try:
    ast.parse(full_content)
    print("Combined content parses OK!")
except SyntaxError as e:
    print(f"Combined content FAILS: {e.msg} at line {e.lineno}")
    # Show context
    all_lines = full_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(all_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        line_text = all_lines[i][:60]
        print(f"{marker} {i+1}: {line_text}")