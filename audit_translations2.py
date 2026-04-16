import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
import translations as t

en_keys = sorted(t.TRANSLATIONS['en'].keys())
missing_sample = {}
for lang in ['ru', 'zh', 'es', 'hi', 'de']:
    lang_keys = set(t.TRANSLATIONS.get(lang, {}).keys())
    missing = sorted(set(en_keys) - lang_keys)
    missing_sample[lang] = missing
    print(f"{lang}: {len(missing)} missing")
    # Print first 30 to understand pattern
    for k in missing[:30]:
        en_val = t.TRANSLATIONS['en'].get(k, '')
        print(f"  '{k}': '{en_val[:60]}...'")

# Print last missing to understand where sections end
print("\n--- Last 30 missing for ru ---")
for k in missing_sample['ru'][-30:]:
    print(f"  '{k}'")