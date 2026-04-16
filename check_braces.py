"""
Check for structural issues in translations.py by counting braces.
"""
with open('C:/Users/sdads/WHDASH/translations.py', 'rb') as f:
    data = f.read()

# Count opening and closing braces at depth 1 (inside TRANSLATIONS dict)
# Each language dict is at depth 1 inside TRANSLATIONS = {
depth = 0
lang_diffs = []

for i, byte in enumerate(data):
    if byte == ord('{'):
        depth += 1
    elif byte == ord('}'):
        depth -= 1
        if depth == 0:
            # This closes the TRANSLATIONS dict - we're at the end
            break
        if depth < 0:
            print(f"ERROR: Negative depth at byte {i}: {repr(data[max(0,i-20):i+20])}")
            break

# Find each language dict boundary by looking for the pattern:
# "    'xx': {" at depth 1 (after TRANSLATIONS = {)
# and the matching "    }" at the end of each dict

# Simpler approach: find all language dicts and check their boundaries
import re

# Find all language dict start positions
lang_pattern = rb"\n    '([a-z]{2})': \{"
for m in re.finditer(lang_pattern, data):
    lang = m.group(1).decode()
    pos = m.start()
    print(f"'{lang}' dict starts at byte {pos}")

# Check the last dict (de) closing
de_start = data.find(b"\n    'de': {")
print(f"\n'de': starts at byte {de_start}")

# The file should end with:
# closing of de dict
# closing of TRANSLATIONS dict
# ...
# Let's find where the TRANSLATIONS dict closes
last_brace = data.rfind(b"    }")
print(f"Last '    }' in file at byte {last_brace}")
print(f"Context: {repr(data[last_brace:last_brace+30])}")