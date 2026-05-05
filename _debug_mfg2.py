with open('manufacturing_routes.py', 'rb') as f:
    content = f.read()

# Find the opening """ on line 1740
lines = content.split(b'\r\n')

# Line 1740 is index 1739, which starts with: order = conn.execute("""
# The """ starts at position where this line begins plus the offset

# Calculate byte position of line 1740
byte_pos = 0
for i in range(1739):
    byte_pos += len(lines[i]) + 2  # +2 for \r\n

print(f"Line 1740 starts at byte {byte_pos}")
print(f"Line 1740: {lines[1739]}")

# The """ is at position byte_pos + 19 (19 chars of indentation + "order = conn.execute(")
triple_pos = byte_pos + 19
print(f"Triple quote at byte {triple_pos}")
print(f"Context: {content[triple_pos-5:triple_pos+10]}")
print(f"Triple quote hex: {content[triple_pos:triple_pos+3].hex()}")

print()

# Check the closing """ on line 1746
byte_pos_1746 = 0
for i in range(1745):
    byte_pos_1746 += len(lines[i]) + 2

print(f"Line 1746 starts at byte {byte_pos_1746}")
print(f"Line 1746: {lines[1745]}")

# The """ is at the beginning (4 spaces of indent)
print(f"First 5 bytes: {lines[1745][:5].hex()}")