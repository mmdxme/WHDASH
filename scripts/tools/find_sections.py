import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
import translations as t

# Find the last key in each language to understand where sections end
for lang in ['ru', 'zh', 'es', 'hi', 'de', 'fa', 'ar']:
    keys = list(t.TRANSLATIONS.get(lang, {}).keys())
    print(f"{lang}: last 5 keys = {keys[-5:]}")
    print(f"  Total keys: {len(keys)}")

# Also find the line numbers for section starts/ends
print("\n--- EN section boundaries ---")
en_keys = list(t.TRANSLATIONS['en'].keys())
# Find where Quick Tools section starts (look for 'quick_tools')
for i, k in enumerate(en_keys):
    if 'quick_tools' in k or 'add_note' in k:
        print(f"  {k}: index {i}")