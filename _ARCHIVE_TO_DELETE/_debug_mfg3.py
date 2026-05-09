import ast

with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the problem is earlier in the file
# Try parsing the first 50KB and see where it fails
try:
    ast.parse(content[:50000])
    print("First 50000 chars: OK")
except SyntaxError as e:
    print(f"First 50000 chars: Error at line {e.lineno}")

try:
    ast.parse(content[:60000])
    print("First 60000 chars: OK")
except SyntaxError as e:
    print(f"First 60000 chars: Error at line {e.lineno}")

try:
    ast.parse(content[:70000])
    print("First 70000 chars: OK")
except SyntaxError as e:
    print(f"First 70000 chars: Error at line {e.lineno}")

try:
    ast.parse(content)
    print("Full file: OK")
except SyntaxError as e:
    print(f"Full file: Error at line {e.lineno}")