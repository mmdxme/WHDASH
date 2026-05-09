"""
Translation System - Backward Compatibility Layer
================================================

This module provides backward compatibility for code that imports from
`translations` directly. The actual translation loading is now handled
by `translation_loader.py` which reads from JSON files.

For new code, prefer:
    from translation_loader import get_translation, get_translations, is_rtl

This module re-exports everything from translation_loader for backward
compatibility with existing code.

Functions re-exported:
    get_translation(lang, key, default=None) - Get single translation
    get_translations(lang) - Get all translations for a language
    is_rtl(lang) - Check if language is RTL
    get_language_direction(lang) - Get 'ltr' or 'rtl'

Data re-exported:
    LANGUAGES - List of language codes
    RTL_LANGUAGES - List of RTL language codes

Note: The TRANSLATIONS dict is no longer available in this compatibility
layer. If you need the full translations dict, use:
    from translation_loader import get_translations
    translations = get_translations('en')

"""

# Re-export everything from the new translation loader
from translation_loader import (
    get_translation,
    get_translations,
    is_rtl,
    get_language_direction,
    LANGUAGES,
    RTL_LANGUAGES,
    TranslationService,
    get_translation_service,
    get_loaded_languages,
    get_cache_stats,
    reload_translations,
)

# For code that expects TRANSLATIONS to be a dict, provide a warning
# but don't actually load the giant dict (that's the whole point of refactoring)
def __getattr__(name):
    if name == 'TRANSLATIONS':
        import warnings
        warnings.warn(
            "TRANSLATIONS dict is deprecated. Use get_translations(lang) instead. "
            "The giant in-code translation dict has been replaced with JSON-based loading.",
            DeprecationWarning,
            stacklevel=2
        )
        # Return empty dict - this will likely cause errors in code that
        # tries to use it, which is intentional to encourage migration
        return {}
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")