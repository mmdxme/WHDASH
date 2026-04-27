#!/usr/bin/env python3

# Let's try to create a minimal reproduction case

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Take the first 21089 lines
prefix = ''.join(lines[:21089])

# Now try adding just the 'ru' line with different formatting
tests = [
    ("With 4-space indent (proper)", "    'ru': {\n"),
    ("With tab indent", "\t'ru': {\n"),
    ("With 8-space indent", "        'ru': {\n"),
    ("No indent", "'ru': {\n"),
    ("With 2-space indent", "  'ru': {\n"),
]

for name, suffix in tests:
    test = prefix + suffix + "    }\n"
    try:
        import ast
        ast.parse(test)
        print(f"{name}: OK")
    except SyntaxError as e:
        print(f"{name}: FAIL - {e.msg}")

# Also test: what if we add a comment before 'ru'?
print("\nTesting with comment before 'ru':")
for name, prefix_mod in [
    ("No extra newline", prefix + "    # Comment\n    'ru': {\n"),
    ("With extra newline", prefix + "\n    # Comment\n    'ru': {\n"),
]:
    test = prefix_mod + "    }\n"
    try:
        import ast
        ast.parse(test)
        print(f"{name}: OK")
    except SyntaxError as e:
        print(f"{name}: FAIL - {e.msg}")