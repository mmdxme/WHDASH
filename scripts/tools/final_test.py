#!/usr/bin/env python3
import sys

# First test: can we even parse the original file?
print("=== Testing original translations.py ===")
try:
    import ast
    with open('translations.py', 'r', encoding='utf-8') as f:
        content = f.read()
    ast.parse(content)
    print("Original parses OK")
except Exception as e:
    print(f"Original FAILS: {type(e).__name__}: {e}")

# Second test: take a fixed number of lines, add proper suffix
print("\n=== Testing with proper ru dict suffix ===")
try:
    with open('translations.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Take first 21089 lines (0-indexed: 0-21088, which is lines 1-21089)
    prefix_lines = lines[:21089]
    prefix = ''.join(prefix_lines)

    # Add proper suffix
    suffix = """
    'ru': {
        # Navigation
        'app_name': 'Corporate Center',
    },
}
"""

    test_content = prefix + suffix

    import ast
    ast.parse(test_content)
    print("Combined parses OK!")
except Exception as e:
    print(f"Combined FAILS: {type(e).__name__}: {e}")

# Third test: just try to parse lines[:21089] alone
print("\n=== Testing prefix only ===")
try:
    with open('translations.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    prefix = ''.join(lines[:21089])
    import ast
    ast.parse(prefix)
    print("Prefix parses OK")
except Exception as e:
    print(f"Prefix FAILS: {type(e).__name__}: {e}")