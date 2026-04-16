import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
# Show lines 6820-6835
for i in range(6819, 6835):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else 0
        print(f"Line {i+1} (indent={indent}): {repr(stripped[:80] if stripped else '')}")