"""
Direct surgical fix for translations.py
Remove the problematic section and replace with proper structure.
"""

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Find the position of 'de': dict
de_pos = content.find("\n    'de': {")
if de_pos == -1:
    print("Could not find 'de':")
    exit(1)

# Find what comes just before 'de': - look at the last 300 chars before de_pos
before_de = content[de_pos-300:de_pos]
print(f"300 chars before 'de':")
print(repr(before_de))

# The issue might be in the closing of Hindi dict
# Look for "compact_mode...    }," pattern
compact_pos = content.find("'compact_mode':")
print(f"\ncompact_mode at: {compact_pos}")

# Find the last "    }" before 'de':
last_close_pos = content.rfind("    }", 0, de_pos)
print(f"Last '    }' before 'de': at: {last_close_pos}")
if last_close_pos >= 0:
    print(f"Context: {repr(content[last_close_pos:last_close_pos+30])}")

# Find any problematic characters before de:
# Look for tab characters
tab_pos = content.rfind("\t", 0, de_pos)
if tab_pos >= 0 and tab_pos > de_pos - 100:
    print(f"\nWARNING: Tab found at position {tab_pos}")
    print(f"Context: {repr(content[tab_pos-20:tab_pos+20])}")