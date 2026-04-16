"""Check Arabic SAME_AS_KEY and fix them."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

en = TRANSLATIONS['en']
ar = TRANSLATIONS['ar']

same = [k for k in ar if ar[k] == k]
print(f"AR SAME_AS_KEY count: {len(same)}")

# Group by prefix
from collections import defaultdict
groups = defaultdict(list)
for k in same:
    prefix = k.split('_')[0] if '_' in k else k
    groups[prefix].append(k)

print("\nGroups:")
for prefix, keys in sorted(groups.items()):
    print(f"  {prefix}: {len(keys)} keys")