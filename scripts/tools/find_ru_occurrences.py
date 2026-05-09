#!/usr/bin/env python3
import re

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

# Find ALL occurrences of 'ru': in the file
print("All occurrences of 'ru': in translations.py:")
for i, line in enumerate(content.split('\n')):
    if "'ru':" in line:
        print(f"Line {i+1}: {line.strip()[:60]}")

# Also search for potential issues - maybe there's a dict inside a dict that's malformed
# Look for patterns like "        'ru':" (8 spaces) which would be inside another dict

print("\n\nLooking for 'ru': with 8-space indent (could be inside a dict):")
for i, line in enumerate(content.split('\n')):
    if "'ru':" in line and line.startswith('        '):
        print(f"Line {i+1}: {line.strip()[:60]}")