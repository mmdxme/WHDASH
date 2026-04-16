"""Check SAME_AS_KEY for all languages."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
    same = [k for k in TRANSLATIONS[lang] if TRANSLATIONS[lang][k] == k]
    print(f"{lang}: {len(same)} SAME_AS_KEY entries")