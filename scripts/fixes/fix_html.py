"""Find and fix common HTML template issues in category.html"""

with open('templates/admin/settings/category.html', 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Fix 1: standalone {{ row.status }} inside span without closing >
# Pattern: </span>>
content = content.replace('</span>>', '</span></td>')

# Fix 2: standalone > inside closing tag
# Pattern: <span>>  -> <span>> but let me check for actual issues

# Fix 3: Check for common Jinja2 issues - unclosed for loops
import re
for_matches = list(re.finditer(r'\{% for [A-Za-z0-9_]+ in [A-Za-z0-9_\[\]."\' |]+ %\}', content))
endfor_matches = list(re.finditer(r'\{% endfor %\}', content))
print(f"for loops: {len(for_matches)}, endfor: {len(endfor_matches)}")

# Fix 4: Check for unclosed divs
open_divs = len(re.findall(r'<div\b', content))
close_divs = len(re.findall(r'</div>', content))
print(f"open divs: {open_divs}, close divs: {close_divs}")

# Fix 5: Look for {{ value }} }} patterns (double closing braces)
double_close = len(re.findall(r'\}\}', content))
print(f"double close braces: {double_close}")

# Fix 6: Look for {{ value }}}} (triple close)
triple_close = len(re.findall(r'\}\}\}', content))
print(f"triple close braces: {triple_close}")

# Fix 7: Check for stray </span> not preceded by >
bad_span = re.findall(r'<span[^>]*>[^<]*</span>[^<>]', content[:1000])
print(f"\nFirst 5 bad_span near start: {bad_span[:5]}")

# Print stats
print(f"\nOriginal size: {len(original)}")
print(f"After fix: {len(content)}")

if content != original:
    with open('templates/admin/settings/category.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("CHANGES MADE!")
else:
    print("No changes needed")
