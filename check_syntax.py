import py_compile
import sys
try:
    py_compile.compile('C:/Users/sdads/WHDASH/translations.py', doraise=True)
    print('Syntax OK')
except py_compile.PyCompileError as e:
    # Print just the error message
    print(str(e))
    # Try to get line content
    with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Line mentioned in error
    import re
    m = re.search(r'line (\d+)', str(e))
    if m:
        lineno = int(m.group(1))
        print(f'Line {lineno}: {repr(lines[lineno-1])}')
        print(f'Line {lineno-1}: {repr(lines[lineno-2])}')