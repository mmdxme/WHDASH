content = open('quality_models.py').read()

# Count various patterns - using single quotes for the count
f3_count = content.count('f' + chr(34) * 3)
q3_count = content.count(chr(34) * 3)

print(f'f triple-quote: {f3_count}')
print(f'triple-quote: {q3_count}')

# Look for lines 2694-2725 to see the context
lines = content.split(chr(10))
for i in range(2694, min(2725, len(lines))):
    print(f'{i+1}: {repr(lines[i][:100])}')