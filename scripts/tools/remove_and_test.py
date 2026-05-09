# Read quality_models_lf_fixed.py and remove problematic functions,
# then test if what remains parses

import re
import ast

with open('quality_models_lf_fixed.py', 'r') as f:
    content = f.read()

# Remove get_supplier_quality_report
pattern = r'\ndef get_supplier_quality_report\(.*?\n(?=\n\ndef |\n\n# |\Z)'
content = re.sub(pattern, '\n\n# get_supplier_quality_report removed\n\n', content, flags=re.DOTALL)

# Write to test file
with open('quality_models_no_supplier.py', 'w') as f:
    f.write(content)

# Test parse
try:
    ast.parse(content)
    print('Parse SUCCESS')
except SyntaxError as e:
    print(f'Parse FAIL: {e}')