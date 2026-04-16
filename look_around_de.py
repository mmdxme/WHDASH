with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Look around position 261870 (where 'de': starts)
start = max(0, 261850 - 200)
end = min(len(content), 261950)
with open('C:/Users/sdads/WHDASH/de_context.txt', 'w', encoding='utf-8') as out:
    out.write(f"Around 'de': (position 261870):\n")
    out.write(repr(content[start:end]))