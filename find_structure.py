with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line number of "'de':"
de_lineno = None
hi_end_lineno = None
for i, line in enumerate(lines):
    if "'de':" in line:
        de_lineno = i + 1
    # Look for the end of hi dict - the line just before "'de':" with closing brace
    if de_lineno is not None and i == de_lineno - 2:
        print(f"Line {i+1} (before 'de'): {repr(line)}")
    if "'hi':" in line and "{" in line:
        print(f"Line {i+1} (hi start): {repr(line)}")

# Find the structure around de
print(f"\nAround 'de' (line {de_lineno}):")
for i in range(de_lineno - 5, de_lineno + 3):
    print(f"  {i+1}: {repr(lines[i])}")