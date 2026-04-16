import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count the nesting level of TRANSLATIONS dict
# The structure is: TRANSLATIONS = { 'en': {...}, 'fa': {...}, ... }
# Each language dict is at depth 1 within TRANSLATIONS

# Find all positions where a language dict starts with 4 spaces indent
# Format: "    'xx': {" means depth 1, depth 0 would be 0 spaces
pattern = r"\n    '([a-z]{2})': \{"

matches = list(re.finditer(pattern, content))
print(f"Found {len(matches)} language dict starts:")
for m in matches:
    lang = m.group(1)
    pos = m.start()
    print(f"  '{lang}' at position {pos}")

# Check if there's an extra language dict that shouldn't be there
# The EN dict starts the file, and after DE dict the file should end
# If there's a 5th dict (like 'hi' with 5 spaces), it would cause this error

# Let's look for 5-space indent 'xx': patterns
pattern5 = r"\n      '([a-z]{2})': \{"
matches5 = list(re.finditer(pattern5, content))
if matches5:
    print(f"\nFound {len(matches5)} language dict starts with 6 spaces (WRONG):")
    for m in matches5:
        print(f"  '{m.group(1)}' at position {m.start()}")
        print(f"    context: {repr(content[m.start():m.start()+50])}")