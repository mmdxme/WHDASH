import re

# Read the file
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and count dict entries
de_match = re.search(r"'de':\s*\{", content)
print(f"de dict starts at character: {de_match.start() if de_match else 'NOT FOUND'}")

# Show context around line 6586
lines = content.split('\n')
print(f"Total lines: {len(lines)}")
print("\nLines 6580-6590:")
for i in range(6579, 6590):
    print(f"{i+1}: {repr(lines[i])}")