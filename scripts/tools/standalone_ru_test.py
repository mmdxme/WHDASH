#!/usr/bin/env python3
import ast

# Test: can I parse a standalone ru dict at the top level?

# Try 1: Just the ru dict
test1 = """
    'ru': {
        'test': 'value',
    },
}
"""
try:
    ast.parse(test1)
    print("1. Just ru dict: OK")
except SyntaxError as e:
    print(f"1. Just ru dict: FAIL - {e.msg}")

# Try 2: TRANSLATIONS dict with just ru
test2 = """
TRANSLATIONS = {
    'ru': {
        'test': 'value',
    },
}
"""
try:
    ast.parse(test2)
    print("2. TRANSLATIONS with just ru: OK")
except SyntaxError as e:
    print(f"2. TRANSLATIONS with just ru: FAIL - {e.msg}")

# Try 3: Copy what works for fa dict
# fa dict starts at line 8186 with "    'fa': {"
# After fa dict closes at line 14740, there's "    },\n" then blank line then "    'ar': {"

# What if I create a test with multiple dicts that mimics this structure?
test3 = """
TRANSLATIONS = {
    'en': {
        'key': 'value',
    },

    'ru': {
        'test': 'value',
    },
}
"""
try:
    ast.parse(test3)
    print("3. Two dicts (en and ru): OK")
except SyntaxError as e:
    print(f"3. Two dicts (en and ru): FAIL - {e.msg}")

# Try 4: What if there's something special about the content just before ru dict?
# Check: is the prefix content (lines 21080-21089) somehow malformed?

# Let me try to create the exact transition from fa dict close to ru dict start
with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 21085-21089 in the file
print("\n=== Exact content of lines 21085-21092 ===")
for i in range(21084, 21092):
    print(f"Line {i+1}: {repr(lines[i])}")