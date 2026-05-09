"""
Translation Loader Module
=========================

Efficient JSON-based translation loading system that replaces the monolithic
translations.py approach. Supports lazy loading, caching, and fallback behavior.

Usage:
    from translation_loader import get_translation, get_translations, is_rtl

    # Get a single translation
    text = get_translation('fa', 'sales')

    # Get all translations for a language
    all_fa = get_translations('fa')

    # Check RTL
    if is_rtl('fa'):
        print("RTL language")
"""

import os
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TRANSLATIONS_DIR = os.path.join(BASE_DIR, 'translations')
META_FILE = os.path.join(TRANSLATIONS_DIR, '_meta.json')

# Cache settings
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 100

# ============================================================================
# Language Metadata
# ============================================================================

class LanguageMetadata:
    """Thread-safe language metadata store."""

    def __init__(self):
        self._languages: Dict[str, Dict] = {}
        self._rtl_languages: set = set()
        self._lock = threading.RLock()
        self._loaded = False

    def load(self):
        """Load language metadata from _meta.json."""
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return

            try:
                with open(META_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for lang in data.get('languages', []):
                    self._languages[lang['code']] = lang
                    if lang.get('direction') == 'rtl':
                        self._rtl_languages.add(lang['code'])

                self._loaded = True
            except Exception as e:
                # Fallback defaults
                self._languages = {
                    'en': {'code': 'en', 'name': 'English', 'native_name': 'English', 'direction': 'ltr'},
                    'fa': {'code': 'fa', 'name': 'Persian', 'native_name': 'فارسی', 'direction': 'rtl'},
                    'ar': {'code': 'ar', 'name': 'Arabic', 'native_name': 'العربية', 'direction': 'rtl'},
                }
                self._rtl_languages = {'fa', 'ar'}
                self._loaded = True

    @property
    def languages(self) -> Dict[str, Dict]:
        self.load()
        return self._languages

    @property
    def rtl_languages(self) -> set:
        self.load()
        return self._rtl_languages

    def get_language_info(self, code: str) -> Optional[Dict]:
        self.load()
        return self._languages.get(code)

    def is_rtl(self, code: str) -> bool:
        self.load()
        return code in self._rtl_languages


# Global metadata instance
_language_metadata = LanguageMetadata()


# ============================================================================
# Translation Cache
# ============================================================================

class TranslationCache:
    """Thread-safe LRU cache for translations with TTL support."""

    def __init__(self, max_size: int = 100, ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()

    def _make_key(self, lang: str) -> str:
        return lang

    def get(self, lang: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(lang)
        import time as _time
        with self._lock:
            if key in self._cache:
                if _time.time() - self._timestamps[key] < self._ttl:
                    return self._cache[key]
                else:
                    del self._cache[key]
                    del self._timestamps[key]
            return None

    def set(self, lang: str, translations: Dict[str, Any]):
        key = self._make_key(lang)
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self._max_size:
                oldest_key = min(self._timestamps, key=self._timestamps.get)
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]

            self._cache[key] = translations
            import time as _time
            self._timestamps[key] = _time.time()

    def invalidate(self, lang: Optional[str] = None):
        with self._lock:
            if lang is None:
                self._cache.clear()
                self._timestamps.clear()
            else:
                key = self._make_key(lang)
                if key in self._cache:
                    del self._cache[key]
                    del self._timestamps[key]


# Global cache instance
_translation_cache = TranslationCache(max_size=MAX_CACHE_SIZE, ttl=CACHE_TTL)


# ============================================================================
# Translation Loading
# ============================================================================

def _load_translation_file(lang: str) -> Optional[Dict[str, Any]]:
    """Load a single language translation file."""
    file_path = os.path.join(TRANSLATIONS_DIR, f'{lang}.json')
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def get_translations(lang: str) -> Dict[str, Any]:
    """
    Get all translations for a language.

    Args:
        lang: Language code (e.g., 'en', 'fa', 'ar')

    Returns:
        Dictionary of translation keys to values
    """
    # Check cache first
    cached = _translation_cache.get(lang)
    if cached is not None:
        return cached

    # Load from file
    translations = _load_translation_file(lang)
    if translations is None:
        # Fallback to English
        if lang != 'en':
            translations = _load_translation_file('en')
        if translations is None:
            return {}

    # Cache the result
    _translation_cache.set(lang, translations)
    return translations


def get_translation(lang: str, key: str, default: Optional[str] = None) -> str:
    """
    Get a single translation by key.

    Args:
        lang: Language code
        key: Translation key (supports dot notation for nested keys)
        default: Default value if key not found

    Returns:
        Translated string or default
    """
    translations = get_translations(lang)

    # Support dot notation for nested keys
    if '.' in key:
        parts = key.split('.')
        value = translations
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                break
        if value is not None:
            return str(value)

    return str(translations.get(key, default if default is not None else key))


def is_rtl(lang: str) -> bool:
    """Check if a language is RTL."""
    return _language_metadata.is_rtl(lang)


def get_language_direction(lang: str) -> str:
    """Get the text direction for a language ('ltr' or 'rtl')."""
    info = _language_metadata.get_language_info(lang)
    if info:
        return info.get('direction', 'ltr')
    return 'ltr'


# ============================================================================
# Legacy Compatibility
# ============================================================================

# For backward compatibility with code importing from translations.py
LANGUAGES = list(_language_metadata.languages.keys())
RTL_LANGUAGES = list(_language_metadata.rtl_languages)


# ============================================================================
# Service Interface (for compatibility with existing code)
# ============================================================================

class TranslationService:
    """Service class providing translation functionality."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_translations(self, lang: str) -> Dict[str, Any]:
        return get_translations(lang)

    def get_translation(self, lang: str, key: str, default: Optional[str] = None) -> str:
        return get_translation(lang, key, default)

    def is_rtl(self, lang: str) -> bool:
        return is_rtl(lang)

    def get_language_direction(self, lang: str) -> str:
        return get_language_direction(lang)

    def get_available_languages(self) -> list:
        return list(_language_metadata.languages.keys())

    def get_language_info(self, lang: str) -> Optional[Dict]:
        return _language_metadata.get_language_info(lang)


# Singleton instance
_translation_service = None


def get_translation_service() -> TranslationService:
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


# ============================================================================
# Module-level exports for compatibility
# ============================================================================

# These are set up for lazy loading to avoid importing heavy modules at startup
def __getattr__(name):
    if name == 'TRANSLATIONS':
        # Lazy load all translations as a big dict (for backward compat)
        all_trans = {}
        for lang in LANGUAGES:
            all_trans[lang] = get_translations(lang)
        return all_trans
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ============================================================================
# Debugging and Diagnostics
# ============================================================================

def get_loaded_languages() -> list:
    """Return list of languages that have translation files."""
    if not os.path.exists(TRANSLATIONS_DIR):
        return []
    return [f.stem for f in Path(TRANSLATIONS_DIR).glob('*.json') if f.stem != '_meta']


def get_cache_stats() -> Dict:
    """Return cache statistics."""
    return {
        'cache_size': len(_translation_cache._cache),
        'max_size': _translation_cache._max_size,
        'loaded_languages': get_loaded_languages()
    }


def reload_translations(lang: Optional[str] = None):
    """Reload translation files (useful for development)."""
    _translation_cache.invalidate(lang)
    _language_metadata.load()