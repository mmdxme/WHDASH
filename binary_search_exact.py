# Fresh approach: binary search for exact failure point in quality_models_lf_fixed.py
import ast

with open('quality_models_lf_fixed.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
total = len(lines)

def can_parse(up_to):
    snippet = '\n'.join(lines[:up_to])
    try:
        ast.parse(snippet)
        return True
    except SyntaxError as e:
        return e

# Binary search
low, high = 0, total
while high - low > 1:
    mid = (low + high) // 2
    result = can_parse(mid)
    if result is True:
        low = mid
    else:
        high = mid
    print(f'low={low}, high={high}, mid={mid}, ok={result is True}')

print(f'\nFailure between lines {low} and {high}')
print(f'Line {low}: {lines[low-1]!r}')
print(f'Line {high}: {lines[high-1]!r}')