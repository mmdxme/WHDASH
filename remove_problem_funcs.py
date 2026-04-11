# Remove problematic functions and test import
import re

with open('quality_models_backup.py', 'r') as f:
    content = f.read()

# Find and remove get_supplier_quality_report
# Also find get_ncr_summary_report and get_capa_summary_report
pattern = r'\ndef get_supplier_quality_report\(.*?\n(?=\n\ndef |\n\n# |\Z)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

pattern2 = r'\ndef get_ncr_summary_report\(.*?\n(?=\n\ndef |\n\n# |\Z)'
content = re.sub(pattern2, '', content, flags=re.DOTALL)

pattern3 = r'\ndef get_capa_summary_report\(.*?\n(?=\n\ndef |\n\n# |\Z)'
content = re.sub(pattern3, '', content, flags=re.DOTALL)

# Write to test file
with open('quality_models_test.py', 'w') as f:
    f.write(content)

# Test parse
import ast
try:
    ast.parse(content)
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')