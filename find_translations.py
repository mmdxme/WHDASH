#!/usr/bin/env python3

# Find the TRANSLATIONS = { line

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where TRANSLATIONS = { is
for i, line in enumerate(lines):
    if 'TRANSLATIONS' in line and '=' in line:
        print(f"Line {i+1}: {repr(line[:80])}")