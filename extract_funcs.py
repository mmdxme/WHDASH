# Extract get_quality_dashboard_stats and get_capa_summary_report functions and test parse
with open('quality_models_backup.py', 'r') as f:
    lines = f.readlines()

# Find get_quality_dashboard_stats
start_line = None
for i, line in enumerate(lines):
    if line.strip().startswith('def get_quality_dashboard_stats'):
        start_line = i
        break

if start_line:
    # Find where the function ends (next def or class)
    end_line = None
    for i in range(start_line + 1, len(lines)):
        if lines[i].startswith('def ') or lines[i].startswith('class ') or lines[i].startswith('# ='):
            end_line = i
            break
    if end_line is None:
        end_line = len(lines)

    func_text = ''.join(lines[start_line:end_line])
    print(f'get_quality_dashboard_stats: lines {start_line+1} to {end_line}')
    print(f'Length: {len(func_text)} chars')

    import ast
    try:
        ast.parse(func_text)
        print('Parse: SUCCESS')
    except SyntaxError as e:
        print(f'Parse: FAIL - {e}')
        print('First 20 lines of function:')
        for i, line in enumerate(func_text.split('\n')[:20]):
            print(f'  {i+1}: {line!r}')
