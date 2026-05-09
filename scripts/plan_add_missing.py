"""
Comprehensive script to add all missing translations for zh, es, hi, de (and fix fa/ar).
Missing keys are from EN: Flow (flow_*), Task Center (task_*), Quick Tools (quick_*).
"""
import subprocess
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Get EN and FA reference keys/translations
exec(compile(open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8').read(), 'translations.py', 'exec'))

en = TRANSLATIONS['en']
fa = TRANSLATIONS['fa']

# Find missing keys
missing_keys = sorted([k for k in en.keys() if k not in fa])
print(f"Missing keys to add: {len(missing_keys)}")
print(f"First 20: {missing_keys[:20]}")

# Create translation blocks for each language
# We need to add these before the 'strategy' key in each language

# Find 'strategy' line for each language (ru, zh, es, hi, de - from earlier analysis)
insert_before = {
    'ru': 2676 - 1,  # line 2676 -> insert at 2675
    'zh': 3363 - 1,
    'es': 4004 - 1,
    'hi': 4645 - 1,
    'de': 5286 - 1,
}

# For fa and ar, they need the same keys added before 'strategy'
# But their current positions are different
# Let me find their 'strategy' lines too
for i, line in enumerate(lines):
    if "'strategy':" in line:
        for lang in ['fa', 'ar']:
            if f"'{lang}':" in lines[i-200:i] and "'strategy':" in line:
                print(f"{lang}: 'strategy' at line {i+1}")