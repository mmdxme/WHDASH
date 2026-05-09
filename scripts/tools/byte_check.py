#!/usr/bin/env python3

with open('translations.py', 'rb') as f:
    raw = f.read()

# Find the byte position where line 21091 starts
lines = raw.decode('utf-8').split('\n')

# Line 21091 is index 21090
target_line = lines[21090] if len(lines) > 21090 else "NOT FOUND"

# Calculate byte positions
byte_pos = 0
for i in range(21090):
    byte_pos += len(lines[i].encode('utf-8')) + 1  # +1 for newline

print(f"Line 21091 starts at byte position: {byte_pos}")
print(f"Line content: {repr(target_line[:80])}")

# Show the raw bytes around that position
print(f"\nRaw bytes around that position (50 bytes before to 50 after):")
start = max(0, byte_pos - 50)
end = min(len(raw), byte_pos + 100)
print(f"Bytes {start}-{end}:")
print(raw[start:end])

# Also check: is the line actually "    'ru': {" or something else?
# Maybe there's hidden Unicode like zero-width space?
print(f"\nCharacter analysis of line 21091:")
for i, c in enumerate(target_line[:20]):
    print(f"  {i}: ord={ord(c)}, char='{c}'")