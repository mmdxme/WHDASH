import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
try:
    import translations
    print('Import OK')
    en = set(translations.TRANSLATIONS['en'].keys())
    for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        lang_keys = set(translations.TRANSLATIONS.get(lang, {}).keys())
        missing = en - lang_keys
        empty = sum(1 for k in lang_keys if not translations.TRANSLATIONS[lang].get(k, '').strip())
        print(f'{lang}: {len(lang_keys)} keys, {len(missing)} missing, {empty} empty')
except SyntaxError as e:
    print(f'Syntax Error: {e}')
except Exception as e:
    print(f'Error: {e}')