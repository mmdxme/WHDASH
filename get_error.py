"""
Get the EXACT error location from Python's compile()
"""
import traceback

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

try:
    compile(content, 'translations.py', 'exec')
    print("No syntax error")
except SyntaxError as e:
    print(f"SyntaxError:")
    print(f"  lineno: {e.lineno}")
    print(f"  offset: {e.offset}")
    print(f"  msg: {e.msg}")
    print(f"  filename: {e.filename}")
    
    lines = content.split('\n')
    if e.lineno:
        line = lines[e.lineno - 1]
        print(f"\nProblem line ({e.lineno}): {repr(line)}")
        print(f"Line length: {len(line)}")
        print(f"First char ord: {ord(line[0]) if line else 'empty'}")
        # Check for tabs vs spaces
        if line:
            leading = len(line) - len(line.lstrip(' \t'))
            spaces = len(line) - len(line.lstrip())
            tabs = len(line) - len(line.lstrip('\t'))
            print(f"Leading spaces: {spaces}")
            print(f"Leading tabs: {tabs}")
            print(f"Leading whitespace (combined): {leading}")