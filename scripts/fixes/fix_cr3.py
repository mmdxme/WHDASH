#!/usr/bin/env python3
import ast

# Let's take a different approach - write the fixed content directly
# and verify it

# Read original
with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by \n (LF only)
lf_lines = raw.split(b'\n')

# Find and remove standalone CR lines
# A standalone CR line would be just b'\r'
# But in \n splitting, CR would be part of the line if CRLF is used
# So let's see what we actually have

# Check for any lines containing only CR
cr_only = [i for i, line in enumerate(lf_lines) if line == b'\r']
print(f"Found {len(cr_only)} lines that are just CR")
print(f"CR-only indices: {cr_only[:10]}...")

# Actually, let's try to just reconstruct the file with proper line endings
# Replace any standalone CR with empty string
fixed_lines = []
for line in lf_lines:
    if line == b'\r':
        # Skip or replace with empty
        fixed_lines.append(b'')
    else:
        fixed_lines.append(line)

# Rejoin with \n
fixed = b'\n'.join(fixed_lines)

# Write fixed
with open('translations_fixed3.py', 'wb') as f:
    f.write(fixed)

# Check line count
print(f"Original lines: {len(lf_lines)}")
print(f"Fixed lines: {len(fixed_lines)}")

# Test parse
try:
    ast.parse(fixed.decode('utf-8'))
    print("Fixed content parses OK!")
except SyntaxError as e:
    print(f"Fixed content fails: {e.msg} at line {e.lineno}")