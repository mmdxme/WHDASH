#!/usr/bin/env python3

# Find where each language dict starts and ends
with open('translations.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

langs = ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']
for lang in langs:
    for i, line in enumerate(lines):
        search = "'" + lang + "':"
        if search in line and '{' in line:
            print(f'{lang} starts at line {i+1}')
            break