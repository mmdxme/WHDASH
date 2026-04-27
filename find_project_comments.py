#!/usr/bin/env python3

with open('translations.py', encoding='utf-8') as f:
    lines = f.readlines()

# Find all '# Project Management' comments
for i, line in enumerate(lines):
    if '# Project Management' in line:
        print(f'Line {i+1}: {line.strip()[:60]}')