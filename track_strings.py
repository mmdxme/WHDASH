# Track triple-quoted strings (both f""" and """) in LF version
with open('quality_models_lf.py', 'r') as f:
    lines = f.readlines()

stack = []  # (line_num, type) where type is 'f' or ''

for i, line in enumerate(lines):
    line_num = i + 1
    # Count f""" and """
    f_count = line.count('f"""')
    plain_count = line.count('"""') - f_count  # remaining """ that aren't f"""

    for _ in range(f_count):
        stack.append((line_num, 'f'))
    for _ in range(plain_count):
        stack.append((line_num, ''))

    # Print all opens and closes
    if f_count > 0 or plain_count > 0:
        opens = []
        if f_count > 0:
            opens.append(f'f"""')
        if plain_count > 0:
            opens.append(f'"""')
        print(f'Line {line_num}: opens={opens}, stack_depth={len(stack)}')

print('\nFinal stack:')
for item in stack:
    print(f'  {item}')
print(f'\nTotal unclosed: {len(stack)}')