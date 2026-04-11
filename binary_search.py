# Test by binary search - find the smallest prefix that fails to parse
import ast

with open('quality_models_backup.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

lines = content.split('\n')
total_lines = len(lines)

print(f'Total lines: {total_lines}')

# Binary search for the failure point
def can_parse_up_to(line_num):
    snippet = '\n'.join(lines[:line_num])
    try:
        ast.parse(snippet)
        return True
    except SyntaxError:
        return False

# Test around the middle
mid = total_lines // 2
print(f'Line {mid}: {can_parse_up_to(mid)}')

# The failure is at line 2612 (reported at 2602)
# Let's check around 1400-1500 where we know get_inspections is
for test_line in [1389, 1390, 1400, 1450, 1460, 1470, 1500]:
    print(f'Line {test_line}: {can_parse_up_to(test_line)}')