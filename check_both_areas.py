# Check around line 6820-6830 in translations.py
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Check lines 6820-6830
print("\nLines 6820-6830:")
for i in range(6819, 6830):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        print(f"Line {i+1} (indent={indent}): {repr(stripped[:100] if stripped else '')}")
    else:
        print(f"Line {i+1}: DOES NOT EXIST")

# Also look at lines 6575-6585 to find the Hindi dict closing
print("\nLines 6575-6585 (Hindi dict closing area):")
for i in range(6574, 6585):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        print(f"Line {i+1} (indent={indent}): {repr(stripped[:100] if stripped else '')}")
    else:
        print(f"Line {i+1}: DOES NOT EXIST")