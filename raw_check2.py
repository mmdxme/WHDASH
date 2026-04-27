#!/usr/bin/env python3

with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by \n to get lines as they would be in Python parsing
lines = raw.decode('utf-8').split('\n')

output = []
output.append(f"Total lines: {len(lines)}")

# Show context around where ru dict should start
output.append("\nLines 21085-21095:")
for i in range(21084, 21095):
    line = lines[i] if i < len(lines) else "OUT OF RANGE"
    # Only show first 60 chars, replacing non-printable
    display_line = ''.join(c if ord(c) < 128 else '?' for c in line[:60])
    output.append(f"  {i+1}: '{display_line}'")

with open('raw_check_output.txt', 'w', encoding='ascii') as f:
    f.write('\n'.join(output))