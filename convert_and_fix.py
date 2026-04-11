# Convert quality_models to LF and test
import shutil
import ast

# Copy backup to quality_models_lf_fixed.py
shutil.copy('quality_models_backup.py', 'quality_models_lf_fixed.py')

# Read and convert to LF
with open('quality_models_lf_fixed.py', 'rb') as f:
    content = f.read()

# Convert CRLF to LF
content = content.replace(b'\r\n', b'\n')

# Fix strftime patterns
content = content.replace("strftime('%Y-%m'".encode(), "strftime('%%Y-%%m'".encode())

# Write back
with open('quality_models_lf_fixed.py', 'wb') as f:
    f.write(content)

print('Converted to LF and fixed strftime')

# Test parse
try:
    with open('quality_models_lf_fixed.py', 'r') as f:
        ast.parse(f.read())
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')