with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(6578, 6595):
    print(f'{i+1}: {repr(lines[i])}')