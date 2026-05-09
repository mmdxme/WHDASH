# Create a fresh quality_models.py from scratch by copying and fixing
import shutil

# Copy backup to quality_models.py
shutil.copy('quality_models_backup.py', 'quality_models.py')
print('Copied backup to quality_models.py')

# Now fix the strftime issue - the %Y-%m in f-strings needs to be escaped
with open('quality_models.py', 'r') as f:
    content = f.read()

# The issue is strftime('%Y-%m', ...) inside f-strings
# The %Y and %m are being interpreted as format specifiers
# We need to escape them as %%Y and %%m

# Fix the strftime patterns
content = content.replace("strftime('%Y-%m'", "strftime('%%Y-%%m'")

# Write back
with open('quality_models.py', 'w') as f:
    f.write(content)

print('Applied strftime fix')

# Test parse
import ast
try:
    ast.parse(open('quality_models.py').read())
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')