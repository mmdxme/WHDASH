"""Check Persian SAME_AS_KEY entries."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

en = TRANSLATIONS['en']
fa = TRANSLATIONS['fa']

same_as_key = [k for k in fa if fa[k] == k]
print(f"FA SAME_AS_KEY count: {len(same_as_key)}")
with open('C:/Users/sdads/WHDASH/fa_same_as_key.txt', 'w', encoding='utf-8') as out:
    for k in sorted(same_as_key):
        out.write(f"  {k}: {en.get(k, 'N/A')}\n")
print("Written to fa_same_as_key.txt")