import ast

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print("Parse OK - no syntax errors")
except IndentationError as e:
    print(f"IndentationError: {e}")
    if hasattr(e, 'lineno'):
        print(f"Error at line {e.lineno}")
        lines = content.split('\n')
        # Show the problem line and context
        for i in range(max(0, e.lineno - 10), min(len(lines), e.lineno + 3)):
            print(f"  {i+1}: {repr(lines[i])}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")