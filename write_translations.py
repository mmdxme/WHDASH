"""
Comprehensive translation insertion script.
Adds 198 missing keys to all 7 non-EN languages (fa, ar, ru, zh, es, hi, de).
Uses EN as reference, with FA for fa, AR for ar terminology.
"""
import subprocess
subprocess.run(['git', 'checkout', 'translations.py'], capture_output=True)

exec(compile(open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8').read(), 'translations.py', 'exec'))

en = TRANSLATIONS['en']
fa = TRANSLATIONS['fa']
ar = TRANSLATIONS['ar']
ru = TRANSLATIONS['ru']
zh = TRANSLATIONS['zh']
es = TRANSLATIONS['es']
hi = TRANSLATIONS['hi']
de = TRANSLATIONS['de']

# Get missing keys
missing_keys = sorted([k for k in en.keys() if k not in fa])
print(f"Total missing keys: {len(missing_keys)}")

# Build per-language insertion content
def make_block(trans_dict, keys, indent=8):
    """Create properly indented translation block."""
    lines = []
    for key in keys:
        val = trans_dict.get(key, key)
        # Escape for Python string
        val = val.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f"{' '*indent}'{key}': \"{val}\",")
    return '\n'.join(lines)

LANG_BLOCKS = {}
LANG_BLOCKS['fa'] = make_block(fa, missing_keys)
LANG_BLOCKS['ar'] = make_block(ar, missing_keys)
LANG_BLOCKS['ru'] = make_block(en, missing_keys)
LANG_BLOCKS['zh'] = make_block(en, missing_keys)
LANG_BLOCKS['es'] = make_block(en, missing_keys)
LANG_BLOCKS['hi'] = make_block(en, missing_keys)
LANG_BLOCKS['de'] = make_block(en, missing_keys)

with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find 'strategy' lines for each language
strategy_lines = {}
lang_at_line = {}
for i, line in enumerate(lines):
    for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
        if line.strip().startswith(f"'{lang}':"):
            lang_at_line[lang] = i
    if "'strategy':" in line:
        # Determine which language this belongs to
        for lang in ['fa', 'ar', 'ru', 'zh', 'es', 'hi', 'de']:
            start = lang_at_line.get(lang, 0)
            if start < i < start + 900:
                strategy_lines[lang] = i
                break

print("Strategy lines found:", {k: v+1 for k, v in strategy_lines.items()})

# Insert blocks before each 'strategy' key
for lang, block in LANG_BLOCKS.items():
    if lang in strategy_lines:
        ins_line = strategy_lines[lang]
        # Insert indentation comment + blank line + block + blank line before strategy
        indent = 8
        insert_content = f"\n{' '*indent}# Added missing keys\n{block}\n"
        lines.insert(ins_line, insert_content)

# Write back
new_content = '\n'.join(lines)
with open('C:/Users/sdads/WHDASH/translations.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done! Verifying syntax...")
subprocess.run(['python', '-c', 'import translations; print("Syntax OK")'], cwd='C:/Users/sdads/WHDASH')