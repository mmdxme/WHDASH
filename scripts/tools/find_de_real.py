with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find 'de': at line 6827
# Show lines 6820-6840
print("\nLines 6820-6840 (where 'de': is reported):")
for i in range(6819, 6840):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else 0
        print(f"Line {i+1} (indent={indent}): {repr(stripped[:80] if stripped else '')}")

# Find the actual position of 'de': in the file
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        print(f"\nFound 'de': at line {i+1} with indent {len(line) - len(line.lstrip())}")
        # Show context
        for j in range(i-5, i+3):
            if j >= 0 and j < len(lines):
                print(f"  {j+1}: {repr(lines[j].rstrip())}")
        break