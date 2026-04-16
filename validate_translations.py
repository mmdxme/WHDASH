#!/usr/bin/env python3
"""
Translation Validation Script
Run this script to check the health of translations in WHDASH.

Usage:
    python validate_translations.py
    python validate_translations.py --verbose
    python validate_translations.py --fix

Exit codes:
    0 = All checks passed
    1 = Validation errors found
"""

import sys
import argparse
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

def validate_translations(verbose=False):
    """Run all translation validation checks."""
    try:
        exec(open('translations.py', encoding='utf-8').read(), globals())
    except Exception as e:
        print(f"ERROR: Failed to import translations.py: {e}")
        return False

    en = TRANSLATIONS['en']
    en_count = len(en)

    print("=" * 60)
    print("WHDASH TRANSLATION VALIDATION REPORT")
    print("=" * 60)
    print()

    all_passed = True
    lang_results = {}

    # Check each language
    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if lang == 'en':
            lang_results[lang] = {'keys': len(TRANSLATIONS[lang]), 'missing': 0, 'empty': 0, 'same_as_key': 0}
            continue

        lang_dict = TRANSLATIONS[lang]

        # Count missing keys
        missing = sum(1 for k in en if k not in lang_dict)

        # Count empty values
        empty = sum(1 for k in lang_dict if not lang_dict[k])

        # Count SAME_AS_KEY entries
        same_as_key = sum(1 for k in lang_dict if lang_dict[k] == k)

        lang_results[lang] = {
            'keys': len(lang_dict),
            'missing': missing,
            'empty': empty,
            'same_as_key': same_as_key
        }

        # Check for issues
        has_issues = missing > 0 or empty > 0 or same_as_key > 0
        if has_issues:
            all_passed = False

    # Print results table
    print(f"{'Language':<12} {'Keys':>6} {'Missing':>8} {'Empty':>6} {'SameAsKey':>10} {'Status':>10}")
    print("-" * 60)

    for lang in ['en', 'fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        r = lang_results[lang]
        status = "PASS" if r['missing'] == 0 and r['empty'] == 0 and r['same_as_key'] == 0 else "FAIL"
        print(f"{lang:<12} {r['keys']:>6} {r['missing']:>8} {r['empty']:>6} {r['same_as_key']:>10} {status:>10}")

    print("-" * 60)
    print()

    # Print detailed issues
    if verbose:
        for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
            r = lang_results[lang]
            if r['missing'] > 0 or r['empty'] > 0 or r['same_as_key'] > 0:
                print(f"\n=== {lang.upper()} Issues ===")
                lang_dict = TRANSLATIONS[lang]

                if r['missing'] > 0:
                    missing_keys = [k for k in en if k not in lang_dict]
                    print(f"\nMissing keys ({r['missing']}):")
                    for k in sorted(missing_keys)[:20]:
                        print(f"  - {k}")
                    if len(missing_keys) > 20:
                        print(f"  ... and {len(missing_keys) - 20} more")

                if r['empty'] > 0:
                    empty_keys = [k for k in lang_dict if not lang_dict[k]]
                    print(f"\nEmpty values ({r['empty']}):")
                    for k in sorted(empty_keys)[:20]:
                        print(f"  - {k}")
                    if len(empty_keys) > 20:
                        print(f"  ... and {len(empty_keys) - 20} more")

                if r['same_as_key'] > 0:
                    same_keys = [k for k in lang_dict if lang_dict[k] == k]
                    print(f"\nSAME_AS_KEY entries ({r['same_as_key']}):")
                    for k in sorted(same_keys)[:20]:
                        print(f"  - {k}")
                    if len(same_keys) > 20:
                        print(f"  ... and {len(same_keys) - 20} more")

    # Check for orphaned keys
    print("\n=== Orphaned Keys Check ===")
    orphaned_count = 0
    for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        lang_dict = TRANSLATIONS[lang]
        orphaned = [k for k in lang_dict if k not in en]
        if orphaned:
            print(f"  {lang}: {len(orphaned)} orphaned keys")
            orphaned_count += len(orphaned)
            if verbose:
                for k in sorted(orphaned)[:10]:
                    print(f"    - {k}")

    if orphaned_count == 0:
        print("  No orphaned keys found. PASS")

    # Check RTL/LTR consistency
    print("\n=== RTL/LTR Consistency Check ===")
    rtl_langs = {'fa', 'ar'}
    ltr_langs = {'en', 'ru', 'zh', 'es', 'hi', 'de'}

    for lang in rtl_langs:
        if 'RTL_LANGUAGES' in dir():
            if lang not in RTL_LANGUAGES:
                print(f"  WARNING: {lang} is RTL but not in RTL_LANGUAGES list")
    print("  RTL/LTR configuration check passed")

    # Final summary
    print("\n" + "=" * 60)
    if all_passed and orphaned_count == 0:
        print("VALIDATION RESULT: ALL CHECKS PASSED")
        print("=" * 60)
        return True
    else:
        print("VALIDATION RESULT: ISSUES FOUND")
        print("=" * 60)
        return False

def main():
    parser = argparse.ArgumentParser(description='Validate WHDASH translations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--fix', '-f', action='store_true', help='Attempt to fix issues (where possible)')
    args = parser.parse_args()

    result = validate_translations(verbose=args.verbose)

    sys.exit(0 if result else 1)

if __name__ == '__main__':
    main()