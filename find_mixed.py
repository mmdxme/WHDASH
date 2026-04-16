# Quick script to find the actual line causing the IndentationError
import ast

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Try to parse - will stop at first error
for i, line in enumerate(lines):
    stripped = line.rstrip('\n\r')
    # Check for mixed tabs and spaces
    if '\t' in stripped and '    ' in stripped:
        print(f"Line {i+1} has both tabs and spaces: {repr(stripped[:40])}")

# Also try AST parsing
print("\nTrying AST parse:")
try:
    with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print("AST parse OK")
except SyntaxError as e:
    print(f"SyntaxError: {e}")
    # Get the specific line
    if hasattr(e, 'lineno') and e.lineno:
        lineno = e.lineno
        print(f"Problem line {lineno}: {repr(lines[lineno-1])}")
        if lineno > 1:
            print(f"Previous line {lineno-1}: {repr(lines[lineno-2])}")