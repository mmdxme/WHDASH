"""
Re-add missing translations to translations.py properly.
This script finds the correct insertion points for each language.
"""
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find all language dict positions
lang_positions = {}
for i, line in enumerate(lines):
    stripped = line.strip()
    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if stripped.startswith(f"'{lang}':"):
            lang_positions[lang] = (i, len(line) - len(line.lstrip()))

print("Language dict positions:")
for lang, (lineno, indent) in lang_positions.items():
    print(f"  {lang}: line {lineno+1}, indent={indent}")

# For each language, find where its dict ends (the closing `},`)
# For a language at line N, its content is at indent 4 (8 spaces for nested)
# The closing brace should be at indent 4 as well

# Find the original Hindi section end (line 4439 + content ending before DE at 5080)
# For RU, ZH, ES, HI, DE - we need to insert before the closing `},` of each section

# Let's find the actual closing patterns
for lang in ['ru', 'zh', 'es', 'hi', 'de']:
    if lang in lang_positions:
        start_lineno = lang_positions[lang][0]
        # Search forward from start for the pattern of closing
        for i in range(start_lineno + 1, len(lines)):
            stripped = lines[i].strip()
            # Look for the "strategy" key which is typically near the end of each section
            if "'strategy':" in stripped:
                print(f"{lang}: 'strategy' at line {i+1}, indent={len(lines[i]) - len(lines[i].lstrip())}")
            # Look for section end markers
            if stripped == "}," and len(lines[i]) - len(lines[i].lstrip()) == 4:
                print(f"{lang}: potential closing at line {i+1}")
                break