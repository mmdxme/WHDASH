#!/usr/bin/env python3

# Read raw bytes
with open('translations.py', 'rb') as f:
    raw = f.read()

# Split by newlines
lines = raw.split(b'\n')
print(f"Total lines: {len(lines)}")

# Check bytes around line 21089-21091
# Line 21089 is index 21088, line 21090 is index 21089, line 21091 is index 21090

for idx in range(21087, 21093):
    if idx < len(lines):
        line_bytes = lines[idx]
        # Show line number, length, and first 40 bytes as hex
        hex_preview = line_bytes[:60].hex() if len(line_bytes) > 0 else '(empty)'
        ascii_preview = ''.join(chr(b) if 32 <= b < 127 else '?' for b in line_bytes[:40])
        print(f"Line {idx+1}: {len(line_bytes)} bytes, hex={hex_preview[:60]}..., ascii='{ascii_preview}'")