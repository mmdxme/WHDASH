with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('C:/Users/sdads/WHDASH/out.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines):
        out.write(f"{i+1}: {line}\n")

print("Done")