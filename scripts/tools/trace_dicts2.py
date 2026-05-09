#!/usr/bin/env python3

# Let me find where each language dict opens and closes

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all language dicts
langs = ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']

for lang in langs:
    # Find the line where 'lang': { appears
    for i, line in enumerate(lines):
        search_str = "'" + lang + "':"
        if search_str in line:
            print(f"{lang}: opens at line {i+1}")
            break

# Now trace bracket balance to find where things actually open/close
balance = 0
dict_stack = []  # (line_num, dict_name)

print("\nTracing dict open/close:")
for i, line in enumerate(lines[:21092]):
    old_balance = balance
    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    # If balance changed, something opened or closed
    if balance != old_balance:
        opens = line.count('{') - line.count('}')
        if opens > 0:
            # Something opened - try to identify what
            for lang in langs:
                search_str = "'" + lang + "':"
                if search_str in line:
                    dict_stack.append((i+1, lang))
                    print(f"  Line {i+1}: {lang} dict opens, balance now {balance}")
                    break
        elif opens < 0:
            # Something closed
            if dict_stack:
                closed = dict_stack.pop()
                print(f"  Line {i+1}: {closed[1]} dict closes, balance now {balance}")