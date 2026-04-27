#!/usr/bin/env python3

# Read translations.py and carefully fix the line ending issue

with open('translations.py', 'rb') as f:
    raw = f.read()

# The problem is line 21090 is a standalone CR
# This means the file has mixed line endings:
# - Most lines end with CRLF (\r\n)
# - But one line (21090) ends with just CR (\r) followed by LF

# Let's detect this by finding positions where \n is preceded by \r vs not
content = raw.decode('utf-8', errors='replace')

# Find all positions of \n
newline_positions = [i for i, c in enumerate(content) if c == '\n']

# Check if any \n is NOT preceded by \r
problem_positions = []
for i, pos in enumerate(newline_positions):
    if pos > 0 and content[pos-1] == '\r':
        # This newline is CRLF - OK
        pass
    else:
        # This newline is just LF - but is there a CR before it that's orphaned?
        # Actually, check if the previous character is a standalone CR
        if pos > 0 and content[pos-1] == '\r':
            pass  # CRLF
        else:
            # Check if there's a CR a few chars back that's not followed by LF
            problem_positions.append((i, pos))

print(f"Total newlines: {len(newline_positions)}")
print(f"Problem positions (just LF without preceding CR): {len(problem_positions)}")

# Let's just normalize ALL line endings to LF
normalized = raw.replace(b'\r\n', b'\n').replace(b'\r', b'')

# But wait - we might be removing CR from strings that contain CR
# So instead, let's just remove the specific problem line (line 21090 which is just CR)
lines = raw.split(b'\n')
print(f"Lines after split by LF: {len(lines)}")

# Find lines that are just \r
cr_only_indices = [i for i, line in enumerate(lines) if line == b'\r']
print(f"CR-only lines: {len(cr_only_indices)}")

# Remove those
fixed_lines = [line for i, line in enumerate(lines) if line != b'\r']
fixed = b'\n'.join(fixed_lines)

# Write
with open('translations_normalized.py', 'wb') as f:
    f.write(fixed)

# Verify
try:
    import ast
    ast.parse(fixed.decode('utf-8'))
    print("Fixed content parses OK!")
except SyntaxError as e:
    print(f"Fixed content fails: {e.msg} at line {e.lineno}")