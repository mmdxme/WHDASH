# Search for 'hi' language dict in translations.py
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find all instances of 'hi': followed by anything
for m in re.finditer(r"'hi':", content):
    pos = m.start()
    # Show context
    start = max(0, pos - 50)
    end = min(len(content), pos + 100)
    print(f"Position {pos}: {repr(content[start:end])}")
    print()