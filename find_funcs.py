content = open('quality_models.py').read()

# Find function starts and f-strings
lines = content.split('\n')
for i, line in enumerate(lines):
    if line.strip().startswith('def '):
        print(f'Line {i+1}: {line.strip()[:80]}')
    if 'f"""' in line:
        print(f'  f""" at line {i+1}')