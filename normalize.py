#!/usr/bin/env python3
import ast

# Let's try normalizing ALL line endings to just LF and see if that helps

with open('translations.py', 'rb') as f:
    raw = f.read()

# Replace all CRLF (\r\n) with just LF (\n)
# Then also handle any standalone CR
normalized = raw.replace(b'\r\n', b'\n').replace(b'\r', b'')

# Write the normalized version
with open('translations_normalized.py', 'wb') as f:
    f.write(normalized)

print(f"Original size: {len(raw)} bytes")
print(f"Normalized size: {len(normalized)} bytes")

# Count lines
orig_lines = raw.count(b'\n')
norm_lines = normalized.count(b'\n')
print(f"Original line count (by LF): {orig_lines}")
print(f"Normalized line count: {norm_lines}")

# Try to parse
try:
    ast.parse(normalized.decode('utf-8'))
    print("Normalized content parses OK!")
except SyntaxError as e:
    print(f"Normalized content fails: {e.msg} at line {e.linno if hasattr(e, 'lineno') else 'unknown'}")