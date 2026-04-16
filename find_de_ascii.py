import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Convert to ASCII-safe representation for output
def ascii_safe(s):
    return ''.join(c if ord(c) < 128 else f'\\x{ord(c):02x}' for c in s)

# Find position of 'de': dict
de_match = re.search(r"\n    'de':\s*\{", content)
if de_match:
    pos = de_match.start()
    start = max(0, pos - 200)
    chunk = content[start:pos+50]
    ascii_chunk = ascii_safe(chunk)
    with open('C:/Users/sdads/WHDASH/de_boundary.txt', 'w', encoding='utf-8') as f:
        f.write(f"'de': dict starts at byte {pos}\n")
        f.write(f"Content before 'de':\n{ascii_chunk}\n\n")
        before_de = content[:pos]
        lines_before = before_de.split('\n')
        f.write(f"Lines before 'de': = {len(lines_before)}\n")
        f.write("Last 5 lines before 'de':\n")
        for i, l in enumerate(lines_before[-5:]):
            f.write(f"  {len(lines_before)-5+i+1}: {ascii_safe(l)}\n")
else:
    with open('C:/Users/sdads/WHDASH/de_boundary.txt', 'w', encoding='utf-8') as f:
        f.write("'de': dict not found\n")