import ast

# Read file content
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Write output to file
with open('C:/Users/sdads/WHDASH/syntax_out.txt', 'w', encoding='utf-8', errors='replace') as out:
    try:
        compile(content, 'translations.py', 'exec')
        out.write("Syntax OK\n")
    except SyntaxError as e:
        out.write(f"SyntaxError at line {e.lineno}, offset {e.offset}\n")
        out.write(f"Message: {e.msg}\n")
        lines = content.split('\n')
        if e.lineno:
            line = lines[e.lineno - 1]
            out.write(f"Offending line: {repr(line)}\n")
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            out.write(f"Indent: {indent} spaces\n")
        if e.lineno and e.lineno > 1:
            prev = lines[e.lineno - 2]
            out.write(f"Previous line: {repr(prev)}\n")
            prev_stripped = prev.lstrip()
            prev_indent = len(prev) - len(prev_stripped)
            out.write(f"Previous indent: {prev_indent} spaces\n")

print("Check C:/Users/sdads/WHDASH/syntax_out.txt for results")