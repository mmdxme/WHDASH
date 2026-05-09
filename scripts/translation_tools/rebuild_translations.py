#!/usr/bin/env python3

# Rebuild translations.py properly
# The issue is that after ar dict closes at line 21029, there's malformed content
# at 8-space indent that should not be there

# Fix strategy:
# 1. Keep lines 1-21029 (through the ar dict close)
# 2. Skip lines 21030-21089 (the malformed section)
# 3. Add proper ru dict structure
# 4. Add remaining language dicts

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Get the working prefix (lines 1-21029, 0-indexed: 0-21028)
# This includes: up through ar dict's last content line, then "    },\n" at line 21029
prefix = ''.join(lines[:21029])  # Up to and including the ar dict close

# Add blank line
prefix += '\n'

# Add properly formatted ru dict
ru_dict = """    'ru': {
        # Navigation
        'app_name': 'Корпоративный центр',
        'app_subtitle': 'Система управления складом',
        'search_placeholder': 'Поиск в меню...',
        'hub_intelligence': 'Интеллектуальный центр',
        'sales': 'Продажи',
        'logistics': 'Логистика',
        'warehouse': 'Склад',
        'procurement': 'Снабжение',
        'accounting': 'Бухгалтерия',
        'reports': 'Отчёты',
        'google_workspace': 'Google Workspace',
        'email_management': 'Управление почтой',
        'issue_tracker': 'Отслеживание проблем',
        'task_center': 'Центр задач',
        'administration': 'Администрирование',
        'settings': 'Настройки',
        'profile': 'Профиль',
        'logout': 'Выход',
    },
}
"""

# But wait - we need to add all the remaining languages too
# Let me check what the original file has after line 21091 for the ru dict

# Get the original content from line 21090 onwards
original_ru_start = None
for i, line in enumerate(lines):
    if "'ru':" in line and '{' in line:
        original_ru_start = i
        break

print(f"Original ru dict starts at line: {original_ru_start + 1}")

# Let me extract the correct ru dict from the original file
# The ru dict content should start at line 21091 and extend to line 27780 (where zh starts)

# Extract original ru dict content
ru_content = ''.join(lines[21090:27780])  # lines 21091-27780

# Combine prefix + original ru content
full_content = prefix + ru_content

# Write to test file
with open('translations_rebuilt.py', 'w', encoding='utf-8') as f:
    f.write(full_content)

# Test parse
import ast
try:
    ast.parse(full_content)
    print("Rebuilt content parses OK!")
except SyntaxError as e:
    print(f"Rebuilt content FAILS: {e.msg} at line {e.lineno}")
    # Show context
    all_lines = full_content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(all_lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if i == e.lineno - 1 else '   '
        ascii_line = ''.join(c if ord(c) < 128 else '?' for c in all_lines[i][:80])
        print(f"{marker} {i+1}: {ascii_line}")