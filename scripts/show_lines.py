lines = open('quality_models.py').read().split('\n')
print(f'Total lines: {len(lines)}')
print('Lines 2680-2690:')
for i in range(2679, min(2690, len(lines))):
    print(f'{i+1}: {lines[i]!r}')