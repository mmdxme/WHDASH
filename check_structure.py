# Show lines 6583-6600 in translations.py to understand the structure
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

data = []
data.append(f"Total lines: {len(lines)}")

# Show 6580-6600 to understand structure
data.append("\nLines 6580-6600:")
for i in range(6579, 6600):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        data.append(f"Line {i+1} (indent={indent}): {repr(stripped[:80] if stripped else '')}")
    else:
        data.append(f"Line {i+1}: DOES NOT EXIST")

# Find where Hindi dict ends and DE dict starts
data.append("\n\nSearching for structure:")
for i, line in enumerate(lines):
    stripped = line.strip()
    # Look for pattern: closing of dict followed by language start
    if stripped == "}," and i < 100:
        data.append(f"Line {i+1}: {repr(stripped)}")

with open('C:/Users/sdads/WHDASH/structure.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write('\n'.join(data))