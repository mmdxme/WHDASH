#!/usr/bin/env python3

with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by \n to get lines as they would be in Python parsing
lines = raw.decode('utf-8').split('\n')

print(f"Total lines: {len(lines)}")

# Show context around where ru dict should start
print("\nLines 21085-21095:")
for i in range(21084, 21095):
    line = lines[i] if i < len(lines) else "OUT OF RANGE"
    print(f"  {i+1}: {repr(line[:60])}")