"""
Generate Missing Translation Keys Report by Language
"""

import re
from pathlib import Path

TRANSLATIONS_FILE = Path(__file__).parent / "translations.py"

def extract_translations():
    """Extract all translations from translations.py"""
    with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    translations = {}
    current_lang = None

    for line in content.split('\n'):
        lang_match = re.match(r"\s*'(\w+)':\s*\{", line)
        if lang_match:
            current_lang = lang_match.group(1)
            translations[current_lang] = {}

        if current_lang:
            key_match = re.match(r"\s*'(\w+)':\s*'([^']*)'", line)
            if key_match:
                key = key_match.group(1)
                value = key_match.group(2)
                translations[current_lang][key] = value

    return translations

def get_all_keys(translations):
    all_keys = set()
    for lang in translations:
        all_keys.update(translations[lang].keys())
    return all_keys

def main():
    translations = extract_translations()
    all_keys = get_all_keys(translations)

    languages = sorted(translations.keys())

    for lang in languages:
        lang_keys = set(translations[lang].keys())
        missing = all_keys - lang_keys

        if missing:
            print(f"\n{'='*60}")
            print(f"LANGUAGE: {lang.upper()}")
            print(f"{'='*60}")
            print(f"Missing {len(missing)} keys:\n")

            # Group by prefix
            grouped = {}
            for key in sorted(missing):
                prefix = key.split('_')[0] if '_' in key else key
                if prefix not in grouped:
                    grouped[prefix] = []
                grouped[prefix].append(key)

            for prefix in sorted(grouped.keys()):
                print(f"  [{prefix}]")
                for key in sorted(grouped[prefix]):
                    # Show English value for reference
                    en_value = translations.get('en', {}).get(key, 'N/A')
                    print(f"    - {key}: \"{en_value}\"")

if __name__ == "__main__":
    main()
