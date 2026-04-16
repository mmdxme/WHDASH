import codecs
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('C:/Users/sdads/WHDASH/lines_output.txt', 'w', encoding='utf-8') as out:
    for i in range(6578, 6595):
        out.write(f'{i+1}: {repr(lines[i])}\n')