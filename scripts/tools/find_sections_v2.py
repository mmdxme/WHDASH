"""
Add translations for zh, es, hi, de by inserting Flow, Feedback, Quick Tools before 'strategy'.
"""
import subprocess

# Restore from git first
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Find the sections in EN
flow_keys = []
feedback_keys = []
quick_keys = []
in_flow = in_feedback = in_quick = False

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'flow_"):
        in_flow = True
        in_feedback = in_quick = False
    elif stripped.startswith("'feedback_"):
        in_flow = in_quick = False
        in_feedback = True
    elif stripped.startswith("'quick_"):
        in_flow = in_feedback = False
        in_quick = True

    if in_flow and stripped != '},':
        flow_keys.append((i, line))
    elif in_flow and stripped == '},':
        in_flow = False
    if in_feedback and stripped != '},':
        feedback_keys.append((i, line))
    elif in_feedback and stripped == '},':
        in_feedback = False
    if in_quick and stripped != '},':
        quick_keys.append((i, line))
    elif in_quick and stripped == '},':
        in_quick = False

# Extract keys only
flow_key_names = [line.strip().split(':')[0].strip().strip("'") for i, line in flow_keys if ':' in line]
feedback_key_names = [line.strip().split(':')[0].strip().strip("'") for i, line in feedback_keys if ':' in line]
quick_key_names = [line.strip().split(':')[0].strip().strip("'") for i, line in quick_keys if ':' in line]

print(f"Flow keys: {len(flow_key_names)}")
print(f"Feedback keys: {len(feedback_key_names)}")
print(f"Quick keys: {len(quick_key_names)}")
print(f"First 5 flow: {flow_key_names[:5]}")
print(f"First 5 feedback: {feedback_key_names[:5]}")
print(f"First 5 quick: {quick_key_names[:5]}")