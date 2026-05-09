#!/usr/bin/env python3

# Read the file and check for problematic CR patterns

with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by different patterns to understand the structure
# First, split by \r\n (Windows line endings)
crlf_lines = raw.split(b'\r\n')
print(f"Lines split by CRLF: {len(crlf_lines)}")

# Find any lines that are just \r (standalone CR)
standalone_cr = []
for i, line in enumerate(crlf_lines):
    if line == b'\r' or line == b'':
        standalone_cr.append(i)

print(f"\nFound {len(standalone_cr)} empty or CR-only lines:")
print(f"Indices: {standalone_cr[:20]}...")

# Check the context around the problem area (around line 21090)
print("\nContext around line 21090 in CRLF split:")
for i in range(21085, 21095):
    if i < len(crlf_lines):
        line = crlf_lines[i]
        print(f"  Index {i} (line {i+1}): {repr(line[:40])}")

# Now try to fix by removing all standalone CR lines
fixed_lines = [line for i, line in enumerate(crlf_lines) if line != b'\r']
print(f"\nAfter removing standalone CR lines: {len(fixed_lines)} lines")

# Write fixed
fixed_content = b'\r\n'.join(fixed_lines)
with open('translations_fixed2.py', 'wb') as f:
    f.write(fixed_content)

# Verify
import ast
try:
    ast.parse(fixed_content.decode('utf-8'))
    print("Fixed content parses OK!")
except SyntaxError as e:
    print(f"Fixed content still fails: {e.msg} at line {e.lineno}")