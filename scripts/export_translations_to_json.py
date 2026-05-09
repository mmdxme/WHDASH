"""
One-time script to export translations from translations.py to individual JSON files.
Run once, then delete.
"""
import json
import os
import sys

# Import the existing translations
sys.path.insert(0, os.path.dirname(__file__))
from translations import TRANSLATIONS, LANGUAGES, RTL_LANGUAGES

output_dir = os.path.join(os.path.dirname(__file__), 'translations')
os.makedirs(output_dir, exist_ok=True)

# Export each language to its own JSON file
for lang_code, lang_dict in TRANSLATIONS.items():
    output_path = os.path.join(output_dir, f'{lang_code}.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(lang_dict, f, ensure_ascii=False, indent=2)
    print(f"Exported {lang_code}: {len(lang_dict)} keys -> {output_path}")

# Export metadata
metadata = {
    'languages': LANGUAGES,
    'rtl_languages': RTL_LANGUAGES,
}
meta_path = os.path.join(output_dir, '_meta.json')
with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)
print(f"Exported metadata -> {meta_path}")

print("\nDone! All translations exported to translations/ directory.")
