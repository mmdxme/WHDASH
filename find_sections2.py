import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
import translations as t

en_keys = list(t.TRANSLATIONS['en'].keys())
# Find Feedback section boundaries
print("=== Feedback section ===")
for i, k in enumerate(en_keys):
    if 'feedback' in k:
        print(f"  {i}: '{k}'")

print("\n=== Quick Tools section ===")
for i, k in enumerate(en_keys):
    if 'quick_tools' in k or k in ['add_note', 'calculator', 'favorites', 'tools_']:
        print(f"  {i}: '{k}'")

print("\n=== Social Media section ===")
for i, k in enumerate(en_keys):
    if 'social_media' in k or 'leads_conversion' in k or 'campaigns_ads' in k:
        print(f"  {i}: '{k}'")

print("\n=== Total keys ===")
print(f"EN total: {len(en_keys)}")