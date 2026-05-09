# Proper string tracking - opens and closes
with open('quality_models_lf.py', 'r') as f:
    lines = f.readlines()

stack = []  # (line_num, type) where type is 'f' or ''

for i, line in enumerate(lines):
    line_num = i + 1
    j = 0
    while j < len(line):
        # Look for f""" or """
        if line[j:j+3] == 'f"""':
            stack.append((line_num, 'f'))
            j += 3
        elif line[j:j+3] == '"""':
            if stack:
                stack.pop()
            else:
                print(f'WARNING: Close at line {line_num} with empty stack')
            j += 3
        else:
            j += 1

print(f'Remaining unclosed: {len(stack)}')
if stack:
    print('First 10 unclosed:')
    for item in stack[:10]:
        print(f'  {item}')