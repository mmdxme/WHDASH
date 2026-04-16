"""
Fix the translations.py indentation issue by reconstructing the Hindi and German sections properly.
"""

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find 'de': dict start
de_start = content.find("\n    'de': {")
if de_start == -1:
    print("Could not find 'de': dict start")
    exit(1)

# Find the position just before 'de': - we need to ensure the Hindi dict is properly closed
# The last content before 'de': should be the closing of the previous dict

# Let's look at what's right before 'de':
before_de = content[:de_start]
# Get last 200 chars
last_chunk = before_de[-200:]
print(f"Last 200 chars before 'de':")
print(repr(last_chunk))

# Check the line structure
lines_before = before_de.split('\n')
print(f"\nLast 5 lines before 'de':")
for line in lines_before[-5:]:
    print(repr(line))

# The structure should be:
# - Hindi dict keys...
# - compact_mode entry...
# - "    }," closing Hindi dict
# - blank line (optional)
# - "    'de': {" start German dict

# If the closing is missing or wrong, we need to fix it