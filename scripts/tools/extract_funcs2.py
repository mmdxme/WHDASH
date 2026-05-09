# Find get_capa_summary_report and get_supplier_quality_report functions and test parse
with open('quality_models_backup.py', 'r') as f:
    lines = f.readlines()

# Find get_capa_summary_report
for i, line in enumerate(lines):
    if line.strip().startswith('def get_capa_summary_report'):
        start_capa = i
        print(f'get_capa_summary_report starts at line {i+1}')
        break

for i, line in enumerate(lines):
    if line.strip().startswith('def get_supplier_quality_report'):
        start_supplier = i
        print(f'get_supplier_quality_report starts at line {i+1}')
        break

# Extract both functions together
func_text = ''.join(lines[start_capa:])
print(f'Total length: {len(func_text)} chars')

import ast
try:
    ast.parse(func_text)
    print('Parse: SUCCESS')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')
