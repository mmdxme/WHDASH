import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
import translations as t

en = set(t.TRANSLATIONS['en'].keys())
print(f'EN keys: {len(en)}')
for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
    lang_keys = set(t.TRANSLATIONS.get(lang, {}).keys())
    missing = en - lang_keys
    empty = sum(1 for k in lang_keys if not t.TRANSLATIONS[lang].get(k, '').strip())
    print(f'{lang}: {len(lang_keys)} keys, {len(missing)} missing, {empty} empty')

# List some missing keys
print('\n--- Sample missing keys for ru, zh, es, hi, de ---')
for lang in ['ru', 'zh', 'es', 'hi', 'de']:
    missing = sorted(en - set(t.TRANSLATIONS.get(lang, {}).keys()))
    print(f'{lang} missing: {missing[:20]}')