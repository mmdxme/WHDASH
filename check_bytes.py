data = open('C:/Users/sdads/WHDASH/translations.py', 'rb').read()
lines = data.split(b'\n')
print(f'Total lines: {len(lines)}')
for i in range(6580, 6592):
    line = lines[i]
    # Show first 80 bytes as hex
    hex_str = line[:80].hex()
    # Try decode
    try:
        txt = line.decode('utf-8')
    except:
        txt = line.decode('latin-1', errors='replace')
    print(f'Line {i+1}: {repr(txt)[:80]}')