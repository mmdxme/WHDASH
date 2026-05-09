#!/usr/bin/env python3
import ast

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Test 1: Does the prefix (lines 1-21089) parse alone?
prefix = ''.join(lines[:21089])
try:
    ast.parse(prefix)
    print("1. Prefix (lines 1-21089) parses OK")
except SyntaxError as e:
    print(f"1. Prefix FAILS: {e.msg}")

# Test 2: Can we parse a standalone ru dict?
ru_dict = "    'ru': {\n        'test': 'value'\n    }\n}"
try:
    ast.parse(ru_dict)
    print("2. Standalone ru dict parses OK")
except SyntaxError as e:
    print(f"2. Standalone ru dict FAILS: {e.msg}")

# Test 3: What about prefix + ru dict (without closing brace)?
test3 = prefix + "    'ru': {\n"
try:
    ast.parse(test3)
    print("3. Prefix + ru dict open parses OK")
except SyntaxError as e:
    print(f"3. Prefix + ru dict open FAILS: {e.msg}")

# Test 4: What if we take a smaller prefix?
for cutoff in [21000, 21050, 21070, 21080, 21085, 21088]:
    test = ''.join(lines[:cutoff]) + "    'ru': {\n"
    try:
        ast.parse(test)
        print(f"4. Cutoff {cutoff} + ru dict open: OK")
    except SyntaxError as e:
        print(f"4. Cutoff {cutoff} + ru dict open: FAIL - {e.msg}")
        break