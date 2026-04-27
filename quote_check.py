#!/usr/bin/env python3

# Very careful quote count analysis around the boundary

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check quote balance in the last 10 lines before ru dict
print("Quote analysis for lines 21080-21090:")
running_balance = 0
for i in range(21080, 21091):
    line = lines[i]
    # Count single quotes (but be careful about escaped quotes)
    opens = line.count("'")
    # Actually, just count odd/even position quotes
    # A more reliable way: count how many pairs
    in_string = False
    string_starts = []
    for j, c in enumerate(line):
        if c == "'" and (j == 0 or line[j-1] != '\\'):
            if not in_string:
                in_string = True
                string_starts.append(j)
            else:
                in_string = False

    print(f"Line {i+1}: {opens} quotes, ends_in_string={in_string}")

# Let's also check the actual bytes around line 21089-21092
print("\n=== Byte analysis ===")
with open('translations_normalized.py', 'rb') as f:
    raw = f.read()

raw_lines = raw.split(b'\n')
print(f"Total raw lines: {len(raw_lines)}")

# Check line 21088-21092
for i in range(21087, 21092):
    line = raw_lines[i]
    print(f"Raw line {i+1}: {repr(line[:50])}")