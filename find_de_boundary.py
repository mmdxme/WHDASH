# Find the exact structure around the Hindi dict end
import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find position of 'de': dict
de_match = re.search(r"\n    'de':\s*\{", content)
if de_match:
    pos = de_match.start()
    print(f"'de': dict starts at byte {pos}")
    # Show 200 bytes before
    start = max(0, pos - 200)
    chunk = content[start:pos+50]
    print(f"Content before 'de': (200 bytes before to 50 after):")
    print(repr(chunk))
    print()
    
    # Count lines before de:
    before_de = content[:pos]
    line_count = before_de.count('\n')
    print(f"Lines before 'de': = {line_count}")
    
    # Show last few lines before de
    lines_before = before_de.split('\n')
    print(f"\nLast 5 lines before 'de':")
    for i, l in enumerate(lines_before[-5:]):
        print(f"  {len(lines_before)-5+i+1}: {repr(l)}")