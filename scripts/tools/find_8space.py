#!/usr/bin/env python3

with open('translations_normalized.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find all lines with 8-space indent that look like dict starts in range 14742-21029
print("Looking for dict openings at 8-space indent in range 14742-21029:")

for i in range(14741, 21029):  # 0-indexed: 14742-21029
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    if indent == 8 and ': {' in line:
        ascii_content = ''.join(c if ord(c) < 128 else '?' for c in line[:80])
        print(f"Line {i+1}: {ascii_content}")