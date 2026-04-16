"""
Comprehensive script to add all missing translations for fa, ar, ru, zh, es, hi, de.
Missing keys are from EN: Flow (flow_*), Task Center (task_*), Quick Tools (quick_*).
"""
import subprocess
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

exec(compile(open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8').read().replace("'flow': {", "'flow_module': {"), 'translations.py', 'exec'))

en = TRANSLATIONS['en']
fa = TRANSLATIONS['fa']

missing_keys = sorted([k for k in en.keys() if k not in fa])
print(f"Missing keys to add: {len(missing_keys)}")

# Show which section each key belongs to
flow_k = [k for k in missing_keys if k.startswith('flow_')]
task_k = [k for k in missing_keys if k.startswith('task_')]
quick_k = [k for k in missing_keys if k.startswith('quick_')]
print(f"Flow keys: {len(flow_k)}")
print(f"Task keys: {len(task_k)}")
print(f"Quick keys: {len(quick_k)}")
print(f"Other: {[k for k in missing_keys if not k.startswith('flow_') and not k.startswith('task_') and not k.startswith('quick_')]}")