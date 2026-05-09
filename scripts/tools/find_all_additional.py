with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all positions of # Additional keys
import re
positions = [m.start() for m in re.finditer(r'# Additional keys', content)]
print(f"Found # Additional keys at {len(positions)} positions:")
for i, pos in enumerate(positions):
    # Show next 100 chars
    context = content[pos:pos+150]
    print(f"  {i+1}. pos={pos}: {repr(context[:100])}")

# Find position of 'de': dict
de_pos = content.find("'de':")
print(f"\n'de': at position: {de_pos}")
print(f"Content around de: {repr(content[de_pos-50:de_pos+30])}")