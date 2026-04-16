with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

data = []
data.append(f"Total lines: {len(lines)}")

# Find 'de': in lines
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        data.append(f"Found 'de': at line {i+1}")
        indent = len(line) - len(line.lstrip())
        data.append(f"Indent: {indent} spaces")
        for j in range(i-5, i+3):
            if j >= 0 and j < len(lines):
                data.append(f"  {j+1}: {repr(lines[j].rstrip())}")
        break

# Show lines 6578-6585
data.append("Lines 6578-6585:")
for i in range(6577, 6585):
    if i < len(lines):
        data.append(f"  {i+1}: {repr(lines[i].rstrip())}")

with open('C:/Users/sdads/WHDASH/debug.txt', 'w', encoding='utf-8', errors='replace') as f:
    f.write('\n'.join(data))