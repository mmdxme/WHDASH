#!/usr/bin/env python3

# Complete rebuild of translations.py to fix all issues

# Strategy:
# 1. Read the original file to extract all language sections
# 2. But the problem is the file is corrupted...

# Instead, let me try a different approach:
# Create a brand new translations.py with the correct structure
# based on the knowledge that we need 8 language dicts

# First, let's check: what is the CURRENT state of the translations.py file?

# Actually, the best approach is to:
# 1. Replace the corrupted section with proper structure
# 2. Remove the problematic duplicate sections

# Let me try to find the exact boundaries of the problem

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The ar dict runs from line 14742 to some closing point around 21029
# After that, there's content that should be at 4-space indent (not 8)
# Then the ru dict starts at line 21091

# The fix: The content at 8-space indent (lines 21031 onwards) needs to be removed
# or moved to proper position

# Actually, let me check: what if the content from lines 21031 onwards is just
# the continuation of the ar dict at wrong indentation?

# Let me find: where does the ar dict content end?
# Search for a line that looks like it closes the ar dict

lines = content.split('\n')

# Find all lines that are just "    }," (4-space close)
closes = []
for i, line in enumerate(lines):
    if line.strip() == '},':
        indent = len(line) - len(line.lstrip())
        if indent == 4:
            closes.append((i+1, line))

print(f"Found {len(closes)} lines that are '    },'")
print(f"First few: {closes[:5]}")
print(f"Last few: {closes[-5:]}")

# The problem: lines 21029 is "    }," which closes ar dict
# But the content after that (21031 onwards at 8-space indent) should be removed
# because it's not part of any valid structure

# Actually, looking at the trace - the 8-space content is E-COMMERCE section
# which has no matching opening brace at 4-space

# Let me find where the actual problem is by checking for dict opens at 8-space
print("\n\nDict opens at 8-space indent in range 14742-22000:")
for i, line in enumerate(lines[14741:22000], start=14742):
    if ': {' in line:
        indent = len(line) - len(line.lstrip())
        if indent == 8:
            print(f"Line {i}: {repr(line[:60])}")