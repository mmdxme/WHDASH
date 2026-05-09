import ast

# Read file content
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Try to parse - using compile() which gives better error messages
try:
    compile(content, 'translations.py', 'exec')
    print("Syntax OK")
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}, offset {e.offset}")
    print(f"Message: {e.msg}")
    lines = content.split('\n')
    # Show the offending line
    if e.lineno:
        line = lines[e.lineno - 1]
        print(f"Offending line: {repr(line)}")
        # Check indent
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        print(f"Indent: {indent} spaces, {indent//4} tabs")
        print(f"Stripped: {repr(stripped[:60])}")
    # Show previous line for context
    if e.lineno and e.lineno > 1:
        prev = lines[e.lineno - 2]
        print(f"Previous line: {repr(prev)}")
        prev_stripped = prev.lstrip()
        prev_indent = len(prev) - len(prev_stripped)
        print(f"Previous indent: {prev_indent} spaces")