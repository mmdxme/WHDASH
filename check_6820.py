# Check what's at lines 6820-6840
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines in file: {len(lines)}")

# Check lines around 6820-6840
print("\nLines 6820-6840:")
for i in range(6819, 6840):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        print(f"Line {i+1} (indent={indent}): {repr(stripped[:100])}")
    else:
        print(f"Line {i+1}: DOES NOT EXIST")