import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())
for lang in ["en", "fa", "ar", "ru", "zh", "es", "hi", "de"]:
    missing = sum(1 for k in TRANSLATIONS["en"] if k not in TRANSLATIONS[lang])
    empty = sum(1 for k in TRANSLATIONS[lang] if not TRANSLATIONS[lang][k])
    print(f"{lang}: {len(TRANSLATIONS[lang])} keys, {missing} missing, {empty} empty")