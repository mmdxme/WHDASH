# Try ast.dump to see what Python's AST sees
import ast

with open('quality_models_lf_fixed.py', 'r') as f:
    content = f.read()

# Try parsing to a Code object
try:
    code = ast.parse(content, mode='exec')
    print('Parse succeeded')
except SyntaxError as e:
    print(f'SyntaxError: {e}')
    # Try partial parse up to the error line
    lines = content.split('\n')
    for i in range(len(lines), max(0, len(lines) - 50), -1):
        try:
            snippet = '\n'.join(lines[:i])
            ast.parse(snippet)
            print(f'Partial parse up to line {i-1}: SUCCESS')
            print(f'Line {i}: {lines[i-1]!r}')
            print(f'Line {i+1}: {lines[i]!r if i < len(lines) else "EOF"}')
            break
        except SyntaxError:
            continue