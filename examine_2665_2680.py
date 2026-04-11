# Read quality_models_lf_fixed.py and examine the tracking around line 2670
with open('quality_models_lf_fixed.py', 'rb') as f:
    data = f.read()

lines = data.split(b'\n')

# Check lines 2665-2680
for i in range(2664, 2680):
    if i < len(lines):
        line = lines[i]
        print(f'Line {i+1} ({len(line)} bytes): {line!r}')