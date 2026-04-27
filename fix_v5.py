#!/usr/bin/env python3

# Very simple fix: just remove all lines from 21031 onwards that are at 8-space indent
# These are the malformed e-commerce content that shouldn't be there

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep: lines 1-21030 (0-indexed: 0-21029)
# Remove: lines that have 8-space indent starting at line 21031 (0-indexed: 21030)

# Find where the 8-space indent starts
problem_start = None
for i in range(21029, min(21040, len(lines))):
    line = lines[i]
    if line.startswith('        '):  # 8 spaces
        problem_start = i
        break

print(f"Problem section starts at line {problem_start + 1 if problem_start else 'unknown'}")

# Find where it ends (should be before ru dict at line 21091)
problem_end = None
for i in range(problem_start if problem_start else 21030, 21091):
    if i >= len(lines):
        break
    line = lines[i]
    # Check if this line is at 8-space indent but is NOT a comment or continuation
    if line.startswith('        ') and not line.strip().startswith('#'):
        # Could be content to remove
        pass

# Actually, let's just remove lines 21030-21089 (the malformed section)
# and add a proper ru dict

# Get lines 1-21029 (through the ar dict close)
prefix_lines = lines[:21029]  # 0-indexed, lines 1-21029

# Add a blank line
prefix = ''.join(prefix_lines) + '\n'

# Now we need to add the ru dict properly
# The ru dict should start at line 21091 in the original, content from lines 21091-27780

# But actually - the original file has the ru dict at 4-space indent starting at line 21091
# The problem is the section BEFORE it (lines 21030-21090) is malformed

# Let me just replace lines 21030-21090 with a proper blank line and ru dict start

# Get the actual ru dict content from original
# The ru dict starts at line 21091 with "    'ru': {"

# Actually, let me just reconstruct: take prefix + proper ru dict

# The proper ru dict content (from the original file, starting at line 21091)
# Lines 21091-27780 (0-indexed: 21090-27779) contain the ru dict
ru_content = ''.join(lines[21090:27780])  # This includes lines 21091 to 27780

# Combine
fixed = prefix + ru_content

# Write to file
with open('translations_fixed_v5.py', 'w', encoding='utf-8') as f:
    f.write(fixed)

# Verify
import ast
try:
    ast.parse(fixed)
    print("Fixed content parses OK!")
except SyntaxError as e:
    print(f"Fixed content FAILS: {e.msg} at line {e.lineno}")
    # Show context
    all_lines = fixed.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(all_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        ascii_line = ''.join(c if ord(c) < 128 else '?' for c in all_lines[i][:80])
        print(f"{marker} {i+1}: {ascii_line}")