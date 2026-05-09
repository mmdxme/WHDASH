import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
import translations as t

en_keys = list(t.TRANSLATIONS['en'].keys())
ru_keys = set(t.TRANSLATIONS.get('ru', {}).keys())
missing = set(en_keys) - ru_keys
missing_sorted = sorted(missing, key=lambda k: en_keys.index(k))

# Find section breaks by looking for gaps in indices
sections = {}
current_section = None
for k in missing_sorted:
    idx = en_keys.index(k)
    if current_section is None:
        current_section = (k, idx, k)
    else:
        # If gap > 5, new section
        if idx - en_keys.index(current_section[2]) > 10:
            sections[current_section[0]] = (current_section[1], en_keys.index(current_section[2]))
            current_section = (k, idx, k)
        else:
            current_section = (current_section[0], current_section[1], k)

if current_section[0]:
    sections[current_section[0]] = (current_section[1], en_keys.index(current_section[2]))

print("Missing sections in ru:")
for name, (start, end) in sorted(sections.items(), key=lambda x: x[1][0]):
    count = end - start + 1
    print(f"  {name}: keys {start}-{end} ({count} keys)")
    # Show first and last key
    print(f"    First: {en_keys[start]}, Last: {en_keys[end]}")
    print(f"    Last missing: {missing_sorted[-5:]}")