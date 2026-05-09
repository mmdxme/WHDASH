import sys
import io
import traceback

output = []
try:
    with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    output.append(f"Total lines: {len(lines)}")
    
    # Show lines 6575-6595 to understand structure
    for i in range(6574, 6595):
        if i < len(lines):
            line = lines[i]
            stripped = line.rstrip('\n\r')
            indent = len(stripped) - len(stripped.lstrip()) if stripped else 0
            output.append(f"Line {i+1} (indent={indent}): {repr(stripped[:80] if stripped else '')}")
        else:
            output.append(f"Line {i+1}: DOES NOT EXIST (file has {len(lines)} lines)")
            
except Exception as e:
    output.append(f"Error: {e}")
    output.append(traceback.format_exc())

with open('C:/Users/sdads/WHDASH/show6580.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))