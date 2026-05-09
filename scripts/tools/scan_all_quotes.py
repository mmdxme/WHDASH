# Scan ALL triple-quote occurrences in sequence
with open('quality_models_backup.py', 'r') as f:
    lines = f.readlines()

print('All triple-quote (""" or \'\'\') occurrences:')
for i, line in enumerate(lines):
    if '"""' in line:
        # Check if it's part of f"""
        prefix = ''
        if 'f"""' in line:
            prefix = ' [f"""'
        elif i > 0 and 'f"""' in lines[i-1]:
            prefix = ' [continuation?]'
        print(f'Line {i+1}:{prefix} {line.rstrip()[:80]}')