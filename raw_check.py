# Read the file and find exact byte content around problematic area
with open('C:/Users/sdads/WHDASH/translations.py', 'rb') as f:
    data = f.read()

# Find 'de': in the file
de_pos = data.find(b"'de':")
if de_pos == -1:
    print("'de': not found in file")
else:
    print(f"'de': found at byte position {de_pos}")
    # Show 200 bytes before and after
    start = max(0, de_pos - 200)
    end = min(len(data), de_pos + 300)
    print(f"Content around 'de': (bytes {start} to {end}):")
    print(data[start:end])
    print()
    # Show as hex
    print("As hex:")
    print(data[start:end].hex())
    print()
    # Show line by line
    lines_before = data[:de_pos].split(b'\n')
    print(f"Number of lines before 'de': = {len(lines_before)}")
    last_lines = lines_before[-5:]
    for i, line in enumerate(last_lines):
        print(f"  Line -5+{i}: {repr(line)}")