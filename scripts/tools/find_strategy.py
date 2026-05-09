"""
Add translations for zh, es, hi, de - inserting before 'strategy' key in each section.
"""
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First, restore from git to get clean state
import subprocess
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find all language dict start lines
lang_positions = {}
for i, line in enumerate(lines):
    stripped = line.strip()
    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if stripped.startswith(f"'{lang}':"):
            lang_positions[lang] = (i, len(line) - len(line.lstrip()))

print("Language dict positions:")
for lang, (lineno, indent) in lang_positions.items():
    print(f"  {lang}: line {lineno+1}")

# Find 'strategy' line for each language
for lang in ['ru', 'zh', 'es', 'hi', 'de']:
    for i, line in enumerate(lines):
        if "'strategy':" in line:
            # Check this is in the right range for the language
            start = lang_positions[lang][0]
            if start < i < start + 900:  # Within reasonable distance
                print(f"{lang}: 'strategy' at line {i+1}")
                break