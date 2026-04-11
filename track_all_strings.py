# Track ALL triple-quote strings (not just f"")
with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')
print(f'Total lines: {len(lines)}')

# Track open triple-quote strings
open_strings = []  # (line_num, type) where type is 'f' or 'plain'

for i, line in enumerate(lines):
    line_num = i + 1
    pos = 0
    while pos < len(line):
        # Check for f"""
        if line[pos:pos+4] == b'f"""':
            open_strings.append((line_num, 'f', pos))
            print(f'Line {line_num}: f""" at pos {pos} OPEN (total: {len(open_strings)})')
            pos += 4
        # Check for """
        elif line[pos:pos+3] == b'"""':
            if open_strings:
                closed = open_strings.pop()
                print(f'Line {line_num}: """ at pos {pos} CLOSES {closed} (total: {len(open_strings)})')
            else:
                print(f'Line {line_num}: """ at pos {pos} CLOSES NOTHING!')
            pos += 3
        else:
            pos += 1

print(f'\nFinal open_strings count: {len(open_strings)}')
if open_strings:
    print('Remaining open strings:')
    for item in open_strings[:10]:
        print(f'  {item}')