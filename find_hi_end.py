import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Find the line number for 'de': dict start
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        print(f"'de': at line {i+1}")
        # Check what's around it
        print(f"Line {i}: {repr(lines[i])}")
        print(f"Line {i-1}: {repr(lines[i-1])}")
        print(f"Line {i-2}: {repr(lines[i-2])}")
        print(f"Line {i-3}: {repr(lines[i-3])}")
        print(f"Line {i-4}: {repr(lines[i-4])}")
        print(f"Line {i-5}: {repr(lines[i-5])}")
        break

# Also find where hi dict ends
for i, line in enumerate(lines):
    if i > 5000 and i < 6000 and "'de':" in line and line.strip().startswith("'de':"):
        print(f"\nLines around hi dict end (line {i+1}):")
        for j in range(i-10, i):
            print(f"  {j+1}: {repr(lines[j])}")
        break