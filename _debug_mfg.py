with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("Total lines:", len(lines))
print()

# Check the triple quote usage in api_order_detail
for i in range(1736, 1765):
    line = lines[i]
    # Show quotes explicitly
    shown = line.replace('"', 'DOUBLE').replace("'", 'SINGLE')
    print(f"Line {i+1}: {shown[:80]}")