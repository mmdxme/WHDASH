"""
Add translations for zh, es, hi, de by inserting Flow, Feedback, Quick Tools before 'strategy'.
"""
import subprocess

# Restore from git first
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Find insertion points (before 'strategy' for each language)
insert_points = {}
for i, line in enumerate(lines):
    for lang in ['ru', 'zh', 'es', 'hi', 'de']:
        if f"'{lang}':" in line and '{' in line:
            insert_points[lang] = i
            break

strategy_lines = {}
for i, line in enumerate(lines):
    if "'strategy':" in line:
        for lang in ['ru', 'zh', 'es', 'hi', 'de']:
            start = insert_points[lang]
            if start < i < start + 900:
                strategy_lines[lang] = i
                break

# Get the Flow, Feedback, Quick Tools sections from EN (lines 30-282, 355-392, 826-916)
# Flow section
flow_start = None
flow_end = None
feedback_start = None
feedback_end = None
quick_start = None
quick_end = None

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'flow_app_name':") or stripped.startswith('# Flow'):
        if flow_start is None:
            flow_start = i
    if stripped.startswith('# Quick Tools') or stripped.startswith("'quick_"):
        if quick_start is None and stripped.startswith("'quick_"):
            quick_start = i
    if stripped.startswith('# Feedback') or stripped.startswith("'feedback_"):
        if feedback_start is None and stripped.startswith("'feedback_"):
            feedback_start = i
    if flow_start is not None and flow_end is None and i > flow_start and stripped == '},':
        if "'flow_" not in lines[i-1] and "'flow_" not in lines[i-2]:
            pass
    # Detect end of flow section
    if flow_start is not None and flow_end is None:
        if stripped == '},' and i > flow_start + 100:
            flow_end = i
            break

# Let me find sections more carefully
flow_keys = []
feedback_keys = []
quick_keys = []
current_section = None

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'flow_"):
        current_section = 'flow'
    elif stripped.startswith("'feedback_"):
        current_section = 'feedback'
    elif stripped.startswith("'quick_"):
        current_section = 'quick'
    elif stripped.startswith('},') and current_section in ['flow', 'feedback', 'quick']:
        if current_section == 'flow':
            flow_end = i
        elif current_section == 'feedback':
            feedback_end = i
        else:
            quick_end = i
        current_section = None

# Extract EN keys from each section
flow_block = '\n'.join(lines[flow_start:flow_end+1])
feedback_block = '\n'.join(lines[feedback_start:feedback_end+1])
quick_block = '\n'.join(lines[quick_start:quick_end+1])

print(f"Flow section: lines {flow_start+1}-{flow_end+1} ({flow_end-flow_start+1} lines)")
print(f"Feedback section: lines {feedback_start+1}-{feedback_end+1} ({feedback_end-feedback_start+1} lines)")
print(f"Quick section: lines {quick_start+1}-{quick_end+1} ({quick_end-quick_start+1} lines)")