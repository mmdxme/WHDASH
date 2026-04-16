"""
Find the exact line ranges for flow, feedback, quick tools sections in EN.
"""
import subprocess
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Find sections by looking for comments and keys
sections = {}
current_section = None

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('# Flow') or stripped.startswith('# Enterprise'):
        current_section = 'flow'
        start = i
    elif stripped.startswith('# Feedback') or stripped.startswith('# Reporting'):
        if current_section == 'flow':
            sections['flow'] = (start, i-1)
        current_section = 'feedback'
        start = i
    elif stripped.startswith('# Quick Tools'):
        if current_section == 'feedback':
            sections['feedback'] = (start, i-1)
        current_section = 'quick'
        start = i
    elif stripped.startswith('# '):
        if current_section in ['flow', 'feedback', 'quick']:
            if current_section == 'flow':
                sections['flow'] = (start, i-1)
            elif current_section == 'feedback':
                sections['feedback'] = (start, i-1)
            else:
                sections['quick'] = (start, i-1)
        current_section = None

# Also check for quick_end
for i, line in enumerate(lines):
    if i > 800:
        stripped = line.strip()
        if stripped.startswith('# '):
            sections['quick'] = (sections['quick'][0], i-1)
            break

print("Sections found:")
for name, (s, e) in sections.items():
    print(f"  {name}: lines {s+1}-{e+1}")

# Show lines around feedback start
print("\nLines around feedback start:")
for i in range(350, 370):
    print(f"  {i+1}|{lines[i]}")