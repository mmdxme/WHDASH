# More precise binary search for first failure
import ast

with open('quality_models_backup.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
total_lines = len(lines)

def can_parse_up_to(line_num):
    snippet = '\n'.join(lines[:line_num])
    try:
        ast.parse(snippet)
        return True
    except SyntaxError as e:
        return False, e

# Binary search between 1300 and 1450
low, high = 1300, 1450
while high - low > 1:
    mid = (low + high) // 2
    result = can_parse_up_to(mid)
    if result is True:
        low = mid
    else:
        high = mid
    print(f'low={low}, high={high}, mid={mid}, can_parse={result}')

print(f'\nFailure is between lines {low} and {high}')

# Check what exact line causes failure
for line_num in range(low, high + 2):
    result = can_parse_up_to(line_num)
    print(f'Line {line_num}: {result}')