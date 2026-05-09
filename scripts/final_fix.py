# Final approach: manually verify each f""" and """ pair in the backup
# and create a properly working file

import shutil

# Copy backup
shutil.copy('quality_models_backup.py', 'quality_models.py')

# Convert CRLF to LF
with open('quality_models.py', 'rb') as f:
    content = f.read()

content = content.replace(b'\r\n', b'\n')

# The strftime issue: inside f-strings, %Y and %m are format specifiers
# They need to be escaped as %%Y and %%m
# However, this replacement also affects regular strings, which is fine
# because %% in a regular string is just % which is fine

content = content.replace("strftime('%Y-%m'".encode(), "strftime('%%Y-%%m'".encode())

# Now the problem is there's still a syntax error
# Let me check by trying to parse incrementally

# Save as LF version
with open('quality_models_lf.py', 'wb') as f:
    f.write(content)

# Test parse
import ast
try:
    ast.parse(content.decode('utf-8'))
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')
    # The error is at line 2718
    # Let me check what's happening there
    lines = content.decode('utf-8').split('\n')
    print(f'Line 2718: {lines[2717]!r}')
    print(f'Line 2719: {lines[2718]!r}')