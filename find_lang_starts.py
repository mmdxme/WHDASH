# Find line numbers in translations.py
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find all language dict starts
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'en':") or stripped.startswith("'fa':") or stripped.startswith("'ar':") or stripped.startswith("'ru':") or stripped.startswith("'zh':") or stripped.startswith("'es':") or stripped.startswith("'hi':") or stripped.startswith("'de':"):
        indent = len(line) - len(line.lstrip())
        print(f"Line {i+1}: indent={indent} spaces: {repr(stripped[:50])}")