# Binary search for exact failure point
import ast

with open('quality_models_lf.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
total = len(lines)

def can_parse(up_to):
    snippet = '\n'.join(lines[:up_to])
    try:
        ast.parse(snippet)
        return True
    except SyntaxError:
        return False

# Binary search
low = 0
high = total
while high - low > 1:
    mid = (low + high) // 2
    if can_parse(mid):
        low = mid
    else:
        high = mid

print(f'Failure is between lines {low} and {high}')
print(f'Last good line {low}: {lines[low-1] if low > 0 else "NONE"}')
print(f'First bad line {high}: {lines[high-1] if high > 0 else "NONE"}')