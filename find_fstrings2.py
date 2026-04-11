# Find all f-strings with triple quotes and their line numbers
with open('quality_models.py', 'r') as f:
    lines = f.readlines()

# Track f-string triple quotes
fstring_stack = []  # (line_num, is_end)
results = []

for i, line in enumerate(lines):
    # Check for f""" start
    if 'f"""' in line:
        fstring_stack.append((i+1, 'start'))
    # Check for """ that might be end of f-string
    elif '"""' in line and fstring_stack:
        # Check if this closes the most recent unclosed f"""
        fstring_stack.pop()

print('Functions with f-strings:')
current_func = None
for i, line in enumerate(lines):
    if line.strip().startswith('def '):
        current_func = (i+1, line.strip())
    if 'f"""' in line:
        print(f'  Line {i+1}: f""" in function {current_func}')

print('\nAll f""" occurrences:')
for i, line in enumerate(lines):
    if 'f"""' in line:
        print(f'  Line {i+1}: {line.strip()[:80]}')
