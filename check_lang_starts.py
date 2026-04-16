"""
Check the actual line structure around the Hindi dict end.
"""
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find all language dict start lines and their indent
lang_starts = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'en':") or stripped.startswith("'fa':") or stripped.startswith("'ar':") or stripped.startswith("'ru':") or stripped.startswith("'zh':") or stripped.startswith("'es':") or stripped.startswith("'hi':") or stripped.startswith("'de':"):
        indent = len(line) - len(line.lstrip())
        lang_starts.append((i+1, stripped[:30], indent))

print("Language dict starts:")
for lineno, text, indent in lang_starts:
    print(f"  Line {lineno}: indent={indent} {text}")

# Check the line before each language dict
print("\nLine before each language dict:")
for i, (lineno, text, indent) in enumerate(lang_starts):
    if lineno > 1:
        prev_line = lines[lineno-2]
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        print(f"  Before line {lineno} (prev indent={prev_indent}): {repr(prev_line.rstrip()[:60])}")