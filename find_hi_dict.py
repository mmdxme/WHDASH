# Find 'hi': dict start in translations.py
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find 'hi': start
hi_match = re.search(r"\n    'hi':\s*\{", content)
if hi_match:
    print(f"'hi': found at position {hi_match.start()}")
else:
    # Check if it's there with different indentation
    hi_match2 = re.search(r"'hi':\s*\{", content)
    if hi_match2:
        print(f"'hi': found at position {hi_match2.start()} with pattern: {repr(content[hi_match2.start():hi_match2.start()+30])}")
    else:
        print("'hi': NOT FOUND in file at all")

# Check for any hi-related dict markers
for m in re.finditer(r"'hi':", content):
    print(f"'hi': at {m.start()}: {repr(content[m.start():m.start()+30])}")