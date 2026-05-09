with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count current state
print(f"File length: {len(content)} characters")
print(f"Triple single quotes: {content.count(chr(39)+chr(39)+chr(39))}")

# Find all triple single quotes that are NOT inside double-quoted strings
# This is tricky, but let's try a different approach:
# Convert all triple single quotes to triple double quotes
# But only for actual string delimiters, not for things like ''' inside strings

# Let's use a simple regex replacement for conn.execute('''...''')
# Find pattern: conn.execute('''...''')
import re

# Simple approach: replace ''' at start of line (with indentation) with """
# and ''' at end of line (with closing parens) with """
# This should fix most SQL queries

# First let's see the problematic pattern
lines = content.split('\n')
problematic = []
for i, line in enumerate(lines):
    if "'''" in line:
        # Check if this opens or closes a triple quote
        stripped = line.lstrip()
        if stripped.startswith("'''"):
            problematic.append((i+1, 'open', line))
        elif stripped.endswith("'''"):
            problematic.append((i+1, 'close', line))
        elif "'''" in line and line.count("'''") == 2:
            problematic.append((i+1, 'both', line))

print(f"\nFound {len(problematic)} lines with '''")
for p in problematic[-20:]:
    print(f"  Line {p[0]}: {p[1]} - {p[2][:60]}")