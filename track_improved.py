# Improved tracking - on each line, count opens and closes properly
with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')

open_fstrings = []  # stack of open f-strings

for i, line in enumerate(lines):
    line_num = i + 1
    j = 0
    while j < len(line):
        if j + 4 <= len(line) and line[j:j+4] == b'f"""':
            # This could be opening or closing
            if open_fstrings and open_fstrings[-1][0] == line_num - 1:
                # Previous line had unclosed f"""
                open_fstrings.pop()
                print(f'Line {line_num}: f""" at pos {j} CONTINUES from line {open_fstrings[-1][0] if open_fstrings else "none"}')
            else:
                open_fstrings.append((line_num, j))
                print(f'Line {line_num}: f""" at pos {j} OPENS (stack: {len(open_fstrings)})')
            j += 4
        elif j + 3 <= len(line) and line[j:j+3] == b'"""':
            if open_fstrings:
                closed = open_fstrings.pop()
                print(f'Line {line_num}: """ at pos {j} CLOSES line {closed[0]} (stack: {len(open_fstrings)})')
            else:
                print(f'Line {line_num}: """ at pos {j} CLOSES NOTHING!')
            j += 3
        else:
            j += 1

    if line_num >= 2700 and line_num <= 2720:
        print(f'Line {line_num}: open_fstrings stack size = {len(open_fstrings)}')