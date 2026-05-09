import codecs
data = open('C:/Users/sdads/WHDASH/translations.py', 'rb').read()
lines = data.split(b'\n')
# Find the tab character issue around lines 6206-6208
for i in range(6205, 6210):
    print(f"Line {i+1} starts with: {hex(lines[i][:10])}")