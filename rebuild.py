#!/usr/bin/env python3

# Rebuild translations.py properly

with open('translations.py', 'rb') as f:
    raw = f.read()

# Decode
content = raw.decode('utf-8', errors='replace')

# The structure is TRANSLATIONS = { 'en': {...}, 'fa': {...}, 'ar': {...}, 'ru': {...}, 'zh': {...}, 'es': {...}, 'hi': {...}, 'de': {...} }
# Find all the language dict starts
import re

# Find the start of each language dict
lang_starts = []
for m in re.finditer(r"^\s+'([a-z]{2})':\s*\{", content, re.MULTILINE):
    line_num = content[:m.start()].count('\n') + 1
    lang_starts.append((line_num, m.group(1)))

print(f"Found language dicts at lines: {lang_starts}")

# Now let's understand the structure:
# Line 1-7: header ("""...)
# Line 8: 'en': {
# ...
# The issue seems to be that around line 21090, something is wrong

# Let me try a different approach: read the file and normalize ALL line endings to \n
# Then write it back

normalized = content.replace('\r\n', '\n').replace('\r', '')

with open('translations_normalized.py', 'wb') as f:
    f.write(normalized.encode('utf-8'))

# Check it
import ast
try:
    ast.parse(normalized)
    print("Normalized file parses OK!")
except SyntaxError as e:
    print(f"Normalized file still fails: {e.msg} at line {e.lineno}")
    # Show context
    lines = normalized.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 3)
    print("\nContext:")
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        line_text = lines[i][:80].encode('ascii', errors='replace').decode()
        print(f"{marker} {i+1}: {line_text}")