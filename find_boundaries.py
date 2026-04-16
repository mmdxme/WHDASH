import re

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all language dict starts and ends
pattern = r"    '([a-z]{2})':\s*\{"
matches = list(re.finditer(pattern, content))
print(f"Found {len(matches)} language dicts:")
for m in matches:
    print(f"  '{m.group(1)}' at position {m.start()}")

# Find the DE dict specifically
de_start = content.find("'de':")
if de_start >= 0:
    # Find the matching closing brace for DE dict
    # It's a dict inside a dict, so we look for }, <newline> }
    # The DE dict starts with "    'de': {" (4 spaces indent)
    # It ends at the matching }
    
    # Let's find where DE dict ends by looking for the structure
    # The file ends with "    }" then "}" (end of TRANSLATIONS)
    
    # Find the last occurrence of the closing pattern
    # After DE dict, the file ends with helper functions
    last_brace = content.rfind("    }", de_start)
    print(f"\nLast '    }}' after 'de': at position {last_brace}")
    print(f"Context: {repr(content[last_brace:last_brace+20])}")