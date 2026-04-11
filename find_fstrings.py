import ast
import re
content = open('quality_models.py').read()
# Find all f-strings with triple quotes
pattern = 'f"""'
count = content.count(pattern)
print(f'f""" count: {count}')

# Find positions
pos = 0
while True:
    pos = content.find(pattern, pos)
    if pos == -1:
        break
    line_num = content[:pos].count('\n') + 1
    print(f'f""" at line {line_num}, pos {pos}')
    pos += 1

# Also check for any remaining f-strings
f_count = content.count('f"')
print(f'f" count: {f_count}')
