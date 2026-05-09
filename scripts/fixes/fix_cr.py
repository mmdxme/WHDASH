#!/usr/bin/env python3

# Fix the stray CR character on line 21090 in translations.py

with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by newlines
lines = raw.split(b'\n')

# Check line 21090 (index 21089) - it's just a CR character
print(f"Before fix - Line 21090: {repr(lines[21089])}")

# Fix: remove the standalone CR or replace with empty line
# The problem is line 21090 is just b'\r' (a standalone CR without LF)
# We should remove this line entirely (replace with nothing)

# Check if this is a lone CR
if lines[21089] == b'\r':
    print("Confirmed: Line 21090 is standalone CR, removing it")
    # Remove this line by filtering it out
    fixed_lines = [line for i, line in enumerate(lines) if i != 21089]
elif len(lines[21089]) == 1 and lines[21089][0] == 13:  # CR = 13
    print("Confirmed: Line 21090 is standalone CR (byte 13), removing it")
    fixed_lines = [line for i, line in enumerate(lines) if i != 21089]
else:
    print(f"Line 21090 is: {repr(lines[21089])}")
    print("This doesn't look like a standalone CR, investigating...")
    fixed_lines = lines

# Write back
fixed_content = b'\n'.join(fixed_lines)

with open('translations_fixed.py', 'wb') as f:
    f.write(fixed_content)

print(f"\nFixed file written to translations_fixed.py")
print(f"Original lines: {len(lines)}")
print(f"Fixed lines: {len(fixed_lines)}")

# Verify the fix
import ast
try:
    ast.parse(fixed_content.decode('utf-8'))
    print("Fixed content parses OK!")
except SyntaxError as e:
    print(f"Fixed content still fails: {e.msg} at line {e.lineno}")