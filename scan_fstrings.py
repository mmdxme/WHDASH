# Find ALL occurrences of """ outside of strings
# We need to track string boundaries

with open('quality_models_backup.py', 'r') as f:
    content = f.read()

# Split by lines and analyze
lines = content.split('\n')

in_fstring = False
fstring_start = None
print('Scanning for f""" and """ pairs:')
for i, line in enumerate(lines):
    # Count triple quotes in this line
    f3_count = line.count('"""')
    f3_with_f = line.count('f"""')

    if f3_with_f > 0:
        print(f'Line {i+1}: f""" found ({f3_with_f} times), in_fstring={in_fstring}')
        if not in_fstring:
            in_fstring = True
            fstring_start = i + 1
    elif '"""' in line and in_fstring:
        print(f'Line {i+1}: """ found, closing f-string that started at line {fstring_start}')
        in_fstring = False
        fstring_start = None

if in_fstring:
    print(f'WARNING: f-string started at line {fstring_start} was never closed!')