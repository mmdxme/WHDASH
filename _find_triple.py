with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Find all ''' patterns
triple_single_positions = []
for i, line in enumerate(lines):
    pos = 0
    while True:
        idx = line.find("'''", pos)
        if idx == -1:
            break
        triple_single_positions.append((i+1, idx, line))
        pos = idx + 1

print(f"Found {len(triple_single_positions)} triple single quote instances")
print()
print("First 30:")
for item in triple_single_positions[:30]:
    print(f"  Line {item[0]}, pos {item[1]}: {repr(item[2][:50])}")