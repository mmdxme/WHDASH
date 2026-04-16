"""
Script to fix the indentation issue in translations.py
The issue is that the DE dictionary starts with incorrect indentation.
This script finds and repairs it.
"""

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find the line with "'de':" and check indentation
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        print(f"Found 'de': at line {i+1}")
        print(f"Line content: {repr(line)}")
        print(f"Indentation: {len(line) - len(line.lstrip())} spaces")
        # Print surrounding context
        for j in range(max(0, i-3), min(len(lines), i+5)):
            print(f"  {j+1}: {repr(lines[j])}")
        break

# Also find where hi section ends - look for pattern of closing braces
# Just before 'de' should be }, <blank>, 'de': {
for i, line in enumerate(lines):
    if "'de':" in line and line.strip().startswith("'de':"):
        # Check previous lines
        print(f"\nBefore 'de' at line {i+1}:")
        for j in range(i-5, i):
            print(f"  {j+1}: {repr(lines[j])}")