with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Convert all triple single quotes to triple double quotes
# Only for actual triple quote sequences, not for things like '''
# We need to be careful: only convert ''' that are used as string delimiters

# Strategy: Find ''' that are NOT inside single quotes and NOT part of escaped sequences
# Actually, let's just convert all ''' that appear as line content (not in code)

# First, let's see the actual problematic area
# Based on earlier analysis, line 1649 has: data = conn.execute('''
# and line 1655 has: ''').fetchall()

# These need to be changed to """

# Let's count what we need to change
# We know the problem is at line 1655, which references the opening at line 1649

# Let's just manually fix the known problematic function
lines = content.split('\n')

# Find api_stats function
for i, line in enumerate(lines):
    if 'def api_stats' in line:
        print(f"api_stats at line {i+1}")
        for j in range(i, min(i+20, len(lines))):
            print(f"  {j+1}: {lines[j]}")
        print()
    if 'def api_orders' in line:
        print(f"api_orders at line {i+1}")
        for j in range(i, min(i+20, len(lines))):
            print(f"  {j+1}: {lines[j]}")
        break