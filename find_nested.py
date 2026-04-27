#!/usr/bin/env python3
import re

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find all occurrences of 'ru' as a key (looking for patterns like "'ru':" at various indent levels)
ru_pattern = re.compile(r"^(\s*)'ru':")

for i, line in enumerate(lines):
    m = ru_pattern.match(line)
    if m:
        indent = len(m.group(1))
        print(f"Line {i+1}, indent={indent}: {line.strip()[:60]}")

# Now find all dict opens at indent 8 that don't close properly before line 21091
print("\n\nLooking for potential unclosed dicts before line 21091...")
open_dicts = []  # stack of (line_num, dict_name, indent)
for i, line in enumerate(lines[:21089]):
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())

    # Check for dict open (key: {)
    if ': {' in line or '={' in line:
        # Try to extract dict name
        if "'" in line:
            # This is a dict-like structure
            pass

    # Check for dict close (line with just } or },)
    if stripped == '}' or stripped == '},':
        if indent == 4:
            # This might close a language dict
            pass
        elif indent == 8:
            # This would close something inside a language dict
            pass