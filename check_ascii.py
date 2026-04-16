# Check around line 6820-6830 in translations.py
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

lines_to_show = []

lines_to_show.append(f"Total lines: {len(lines)}")

# Check lines 6820-6830
lines_to_show.append("\nLines 6820-6830:")
for i in range(6819, 6830):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        # Only show ASCII-safe part
        safe = ''.join(c for c in (stripped[:100] if stripped else '') if ord(c) < 128)
        lines_to_show.append(f"Line {i+1} (indent={indent}): {safe}")
    else:
        lines_to_show.append(f"Line {i+1}: DOES NOT EXIST")

# Also look at lines 6575-6585
lines_to_show.append("\nLines 6575-6585 (Hindi dict closing area):")
for i in range(6574, 6585):
    if i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n\r')
        indent = len(stripped) - len(stripped.lstrip()) if stripped else -1
        safe = ''.join(c for c in (stripped[:100] if stripped else '') if ord(c) < 128)
        lines_to_show.append(f"Line {i+1} (indent={indent}): {safe}")
    else:
        lines_to_show.append(f"Line {i+1}: DOES NOT EXIST")

with open('C:/Users/sdads/WHDASH/both_areas.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write('\n'.join(lines_to_show))