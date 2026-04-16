"""
Extract the exact bytes around the 'de': dict start to understand the indentation issue.
"""
with open('C:/Users/sdads/WHDASH/translations.py', 'rb') as f:
    data = f.read()

# Find 'de': bytes
de_bytes = b"'de':"
de_pos = data.find(de_bytes)
if de_pos == -1:
    print("'de': not found")
    exit(1)

print(f"'de': found at byte position {de_pos}")

# Show 50 bytes before and after
start = max(0, de_pos - 50)
end = min(len(data), de_pos + 100)
chunk = data[start:end]

print(f"\n50 bytes before 'de':")
print(f"  {repr(chunk[:50])}")
print(f"  as hex: {chunk[:50].hex()}")

print(f"\n100 bytes around 'de':")
print(f"  {repr(chunk)}")
print(f"  as hex: {chunk.hex()}")

# Check what the previous line looks like
# Find the start of the line containing 'de':
line_start = data.rfind(b'\n', 0, de_pos)
if line_start >= 0:
    prev_line_start = data.rfind(b'\n', 0, line_start)
    if prev_line_start >= 0:
        prev_line = data[prev_line_start+1:line_start]
        print(f"\nPrevious line: {repr(prev_line)}")
        print(f"Previous line hex: {prev_line.hex()}")
        print(f"Previous line starts with {len(prev_line) - len(prev_line.lstrip())} whitespace chars")
        leading = prev_line[:len(prev_line) - len(prev_line.lstrip())]
        print(f"Leading bytes: {leading}")
        print(f"Leading as hex: {leading.hex()}")