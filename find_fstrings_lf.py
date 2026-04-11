# The issue might be with how my tracking script interprets the bytes
# Let me verify by actually trying to identify the exact f""" patterns

with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')

# Find all f""" occurrences
print('All f""" occurrences:')
for i, line in enumerate(lines):
    if b'f"""' in line:
        print(f'Line {i+1}: {line!r}')