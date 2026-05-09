# Track f-string state with line numbers
with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')
print(f'Total lines: {len(lines)}')

# Track open f-strings
open_fstrings = []  # (line_num, byte_offset)

for i, line in enumerate(lines):
    line_num = i + 1
    pos = 0
    while pos < len(line):
        # Check for f"""
        if line[pos:pos+4] == b'f"""':
            open_fstrings.append((line_num, pos))
            print(f'Line {line_num}: f""" at pos {pos} (total open: {len(open_fstrings)})')
            pos += 4
        # Check for """
        elif line[pos:pos+3] == b'"""':
            if open_fstrings:
                closed = open_fstrings.pop()
                print(f'Line {line_num}: """ at pos {pos} closes f""" from line {closed[0]} (total open: {len(open_fstrings)})')
            else:
                print(f'Line {line_num}: """ at pos {pos} with NO OPEN f"""!')
            pos += 3
        else:
            pos += 1

print(f'\nFinal open_fstrings count: {len(open_fstrings)}')
if open_fstrings:
    print('Remaining open f-strings:')
    for item in open_fstrings:
        print(f'  Line {item[0]}, pos {item[1]}')