# Fresh rebuild: copy backup and fix known issues
import shutil

# Start fresh from backup
shutil.copy('quality_models_backup.py', 'quality_models_fixed.py')

with open('quality_models_fixed.py', 'r') as f:
    content = f.read()

# Known issues to fix:
# 1. strftime('%Y-%m' inside f-strings needs escaping to %%Y-%%m
# 2. The CRLF line endings

# Step 1: Fix strftime
content = content.replace("strftime('%Y-%m'", "strftime('%%Y-%%m'")

# Step 2: Fix line endings (already done in previous version)
# Skip this step for now

# Save
with open('quality_models_fixed.py', 'w') as f:
    f.write(content)

# Test parse
import ast
try:
    ast.parse(content)
    print('Initial parse: SUCCESS')
except SyntaxError as e:
    print(f'Initial parse: FAIL - {e}')

# Now identify and fix problematic functions
# The issue is in multi-line f-strings with {where_sql} interpolation
# They have CRLF endings which confuses Python

# Convert to just use standard string formatting instead of f-strings for these
# Pattern: db.execute(f"""... WHERE {where_sql} ..."""", params)
# Should become: db.execute("""... WHERE %s ...""" % where_sql, params)

# This is too complex to fix manually. Let's try a simpler approach:
# Just delete the problematic functions and re-add clean versions

import re

# Find get_supplier_quality_report and check its structure
match = re.search(r'(\ndef get_supplier_quality_report.*?)((?=\n\ndef |\n\n# |\Z))', content, re.DOTALL)
if match:
    print(f'Found get_supplier_quality_report at position {match.start()}')
    func = match.group(0)
    print(f'Function length: {len(func)}')
    print(f'First 200 chars: {func[:200]!r}')