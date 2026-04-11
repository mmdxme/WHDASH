with open('quality_models_backup.py', 'r') as f:
    content = f.read()

# Find and remove the get_supplier_quality_report function
import re

# Pattern to match the function including its docstring and body
pattern = r'\ndef get_supplier_quality_report\(.*?\n(?=\n\ndef |\n\n# |\Z)'

# Check if the pattern exists
if re.search(pattern, content, re.DOTALL):
    print('Found get_supplier_quality_report')
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
else:
    print('Pattern not found, trying simpler approach')
    # Split at the function definition
    lines = content.split('\n')
    func_start = None
    for i, line in enumerate(lines):
        if line.startswith('def get_supplier_quality_report'):
            func_start = i
            break
    if func_start:
        print(f'Function starts at line {func_start + 1}')
        # Find the end (next function or end of file)
        func_end = None
        for i in range(func_start + 1, len(lines)):
            if lines[i].startswith('def ') or lines[i].startswith('# ='):
                func_end = i
                break
        print(f'Function end at line {func_end + 1 if func_end else "EOF"}')
        # Remove the function
        new_lines = lines[:func_start] + lines[func_end:]
        new_content = '\n'.join(new_lines)
    else:
        print('Could not find function')
        new_content = content

with open('quality_models.py', 'w') as f:
    f.write(new_content)

print('Done - removed function')

# Test parse
import ast
try:
    ast.parse(new_content)
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')
