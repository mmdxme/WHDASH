"""Find remaining AR SAME_AS_KEY."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

ar = TRANSLATIONS['ar']
same = [k for k in ar if ar[k] == k]
print(f"Remaining: {same}")