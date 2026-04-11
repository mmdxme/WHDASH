# Convert to LF line endings and test parse
with open('quality_models_backup.py', 'rb') as f:
    data = f.read()

# Replace CRLF with LF
data_lf = data.replace(b'\r\n', b'\n')

# Write to new file
with open('quality_models_lf.py', 'wb') as f:
    f.write(data_lf)

print('Converted to LF line endings')

# Now try parsing
import ast
with open('quality_models_lf.py', 'r') as f:
    content = f.read()

try:
    ast.parse(content)
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')