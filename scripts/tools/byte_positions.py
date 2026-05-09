#!/usr/bin/env python3

with open('translations.py', 'rb') as f:
    raw = f.read()

# Calculate exact byte position of line 21090 start (before ru dict)
lines = raw.decode('utf-8').split('\n')

# Calculate byte position for start of each line
byte_positions = [0]
for line in lines:
    byte_positions.append(byte_positions[-1] + len(line.encode('utf-8')) + 1)

print(f"Total lines: {len(lines)}")
print(f"Byte position of line 21090 start (index 21089): {byte_positions[21089]}")
print(f"Byte position of line 21091 start (index 21090): {byte_positions[21090]}")
print(f"Byte position of line 21092 start (index 21091): {byte_positions[21091]}")

# Show raw bytes at line 21089 and 21090 boundary
print(f"\nRaw bytes at position {byte_positions[21089]} (start of line 21090):")
start = byte_positions[21089]
end = byte_positions[21092]
print(f"Bytes {start}: {raw[start:end]}")

# Check exactly what's at the transition from fa dict to ru dict
# The fa dict should end at line 21089 "    },"
# So bytes around that point should be interesting
print(f"\n\n=== Checking fa dict closing ===")
fa_close_pos = byte_positions[21089] - 5  # 5 bytes before end of line 21089
print(f"Bytes around end of line 21089 (position {fa_close_pos}):")
print(raw[fa_close_pos:fa_close_pos+50])