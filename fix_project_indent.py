#!/usr/bin/env python3

# Fix the project translations indentation - they need to be at 4-space indent (8 spaces total)

with open('translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The project translations were inserted at 8-space indent but they should be at 4-space
# So we need to change 8 leading spaces to 4 leading spaces in the project section

# Find the project section start and fix indentation
lines = content.split('\n')

# Find where project management section starts
proj_start = None
for i, line in enumerate(lines):
    if '# Project Management' in line:
        proj_start = i
        break

if proj_start:
    print(f"Project section starts at line {proj_start + 1}")

# Fix: change 8-space indent to 4-space indent in project section
fixed_lines = []
in_project_section = False
for i, line in enumerate(lines):
    if '# Project Management' in line:
        in_project_section = True

    if in_project_section:
        # Fix indentation
        if line.startswith('        '):  # 8 spaces
            fixed_lines.append(line[4:])  # Remove 4 spaces
        elif line.strip() == '},' and len(line) - len(line.lstrip()) == 4:
            # This is the English dict close, keep as is
            fixed_lines.append(line)
            in_project_section = False
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

fixed_content = '\n'.join(fixed_lines)

# Write back
with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

# Verify
import ast
try:
    ast.parse(fixed_content)
    print("Fixed translations.py parses OK!")
except SyntaxError as e:
    print(f"Fixed translations.py FAILS: {e.msg} at line {e.lineno}")