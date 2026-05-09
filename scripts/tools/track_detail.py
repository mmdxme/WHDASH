# Re-do tracking more carefully
with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')

open_strings = []
last_action = None

for i, line in enumerate(lines):
    line_num = i + 1
    pos = 0
    while pos < len(line):
        if line[pos:pos+4] == b'f"""':
            open_strings.append((line_num, pos, 'f'))
            last_action = ('open', line_num, pos, 'f')
            pos += 4
        elif line[pos:pos+3] == b'"""':
            if open_strings:
                closed = open_strings.pop()
                last_action = ('close', line_num, pos, closed)
            else:
                last_action = ('close_nothing', line_num, pos)
            pos += 3
        else:
            pos += 1

    if line_num >= 2700 and line_num <= 2720:
        print(f'Line {line_num}: last_action={last_action}, open_strings={len(open_strings)}')