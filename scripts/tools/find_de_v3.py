with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

out = []
out.append(f"Total lines: {len(lines)}")

# Find 'de': in lines
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        out.append(f"Found 'de': at line {i+1}")
        indent = len(line) - len(line.lstrip())
        out.append(f"Indent: {indent} spaces")
        for j in range(i-5, i+3):
            if j >= 0 and j < len(lines):
                out.append(f"  {j+1}: {repr(lines[j].rstrip())}")
        break

# Show lines 6578-6585 (the Hindi section closing)
out.append("\nLines 6578-6585:")
for i in range(6577, 6585):
    if i < len(lines):
        out.append(f"  {i+1}: {repr(lines[i].rstrip())}")

with open('C:/Users/sdads/WHDASH/de_real.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))