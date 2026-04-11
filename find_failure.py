# Incremental parsing test
import ast

with open('quality_models.py', 'r') as f:
    lines = f.readlines()

total_lines = len(lines)
print(f'Total lines: {total_lines}')

# Find first failing line using binary search
def find_first_failure(low, high):
    if high - low <= 1:
        return high
    mid = (low + high) // 2
    snippet = ''.join(lines[:mid])
    try:
        ast.parse(snippet)
        return find_first_failure(mid, high)
    except SyntaxError as e:
        return find_first_failure(low, mid)

# Start binary search
failure_point = find_first_failure(1, total_lines)
print(f'First failure at line: {failure_point}')
print(f'Lines around failure:')
for i in range(max(0, failure_point - 3), min(total_lines, failure_point + 2)):
    print(f'{i+1}: {lines[i][:80]!r}')