#!/usr/bin/env python3
import re

with open('translations.py', encoding='utf-8') as f:
    content = f.read()

# Find 'ru' dict start more carefully
# Pattern:  optional whitespace, then 'ru': {
pattern = r"^\s*'ru':\s*\{"

lines = content.split('\n')
for i, line in enumerate(lines):
    if "'ru':" in line and '{' in line:
        indent = len(line) - len(line.lstrip())
        print(f"Line {i+1}: indent={indent}, content={line[:40].encode('ascii', errors='replace').decode()}")

# Also check what closes the fa dict
print("\n=== Checking fa dict closure ===")
fa_start = None
fa_end = None
for i, line in enumerate(lines):
    if "'fa':" in line and "{" in line:
        fa_start = i
    if fa_start and i > fa_start:
        stripped = line.strip()
        if stripped == "}," or stripped == "}":
            fa_end = i
            break

if fa_start and fa_end:
    print(f"fa dict: starts line {fa_start+1}, closes at line {fa_end+1}")
    print(f"Next line after fa close: {lines[fa_end+1][:40].encode('ascii', errors='replace').decode() if fa_end+1 < len(lines) else 'EOF'}")