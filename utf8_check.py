#!/usr/bin/env python3
import ast

with open('translations.py', encoding='utf-8-sig') as f:  # utf-8-sig will handle BOM
    content = f.read()

lines = content.split('\n')

# Direct parse check - when ast.parse fails at line 21091,
# the "actual line 21091" should be 'ru': {
# but maybe the line numbering in the AST error is from a different perspective?

print("Checking if lines 21090, 21091, 21092 are what we expect:")
print(f"Line 21090 (index 21089): {repr(lines[21089])}")
print(f"Line 21091 (index 21090): {repr(lines[21090])}")
print(f"Line 21092 (index 21091): {repr(lines[21091])}")

# Try parsing a minimal example
test = "translations = {\n    'ru': {\n    }\n}"
try:
    ast.parse(test)
    print("\nMinimal test parses OK")
except SyntaxError as e:
    print(f"\nMinimal test fails: {e}")