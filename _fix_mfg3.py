with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Convert all triple single quotes to triple double quotes for SQL strings
# Pattern: ''' to """
# But only for actual SQL strings in conn.execute('''...''')

# Strategy: Find all ''' that are used as string delimiters and replace with """
# We can identify these because they're inside conn.execute, db.execute, etc.

# Simple replacement: replace all ''' with """ except in cases where it would break
# Actually, let's be more targeted: find SQL strings

lines = content.split('\n')
new_lines = []
i = 0
changes = 0
while i < len(lines):
    line = lines[i]
    # Check if this line has triple quotes
    if "'''" in line:
        # Count how many
        count = line.count("'''")
        if count == 1:
            # Check if it opens or closes
            stripped = line.lstrip()
            if stripped.startswith("'''"):
                # Opening - replace with """
                new_line = line.replace("'''", '"""', 1)
                if new_line != line:
                    changes += 1
                    print(f"Line {i+1} (open): {line.strip()[:50]} -> {new_line.strip()[:50]}")
                line = new_line
            elif stripped.endswith("'''"):
                # Closing - replace with """
                new_line = line.replace("'''", '"""', 1)
                if new_line != line:
                    changes += 1
                    print(f"Line {i+1} (close): {line.strip()[:50]} -> {new_line.strip()[:50]}")
                line = new_line
            else:
                # Contains ''' in the middle - might be both open and close on different lines
                # This is complex, skip for now
                pass
        elif count == 2:
            # Both opening and closing on same line
            new_line = line.replace("'''", '"""')
            if new_line != line:
                changes += 1
                print(f"Line {i+1} (both): {line.strip()[:50]} -> {new_line.strip()[:50]}")
            line = new_line
    new_lines.append(line)
    i += 1

print(f"\nTotal changes: {changes}")
print(f"New file length: {len(''.join(new_lines))}")

# Write back
with open('manufacturing_routes.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))