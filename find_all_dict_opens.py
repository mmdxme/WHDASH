#!/usr/bin/env python3

# Find all dict opens at 4-space indent in range 14742-21089
# These should all be language dicts at the TRANSLATIONS top level

with open('translations_fixed_v4.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

output = []
output.append("Dict opens at 4-space indent in range 14742-21089:")

for i in range(14741, 21089):  # 0-indexed: 14742-21089
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    if indent == 4 and ': {' in line:
        ascii_line = ''.join(c if ord(c) < 128 else '?' for c in line[:60])
        output.append(f"Line {i+1}: {ascii_line}")

with open('dict_opens_4space.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

# Also count dict opens at 8-space indent in this range
output2 = []
output2.append("Dict opens at 8-space indent in range 14742-21089:")

for i in range(14741, 21089):
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    if indent == 8 and ': {' in line:
        ascii_line = ''.join(c if ord(c) < 128 else '?' for c in line[:60])
        output2.append(f"Line {i+1}: {ascii_line}")

with open('dict_opens_8space.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output2))