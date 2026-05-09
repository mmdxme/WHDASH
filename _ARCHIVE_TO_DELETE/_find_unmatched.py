with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if module starts with triple quote
print('File starts with:', repr(content[:20]))
print()

# Check all triple quote pairs - simple approach: find all positions and pair them
positions = []
i = 0
while i < len(content):
    if content[i:i+3] == "'''":
        positions.append(('open', i))
        i += 3
    elif content[i:i+3] == '"""':
        positions.append(('close', i))
        i += 3
    else:
        i += 1

print(f"Found {len(positions)} triple quote markers")
print("First 20:", positions[:20])

# Pair them: first open with next close, etc.
stack = []
unmatched = []
for p in positions:
    if p[0] == 'open':
        stack.append(p)
    else:  # close
        if stack:
            stack.pop()
        else:
            unmatched.append(p)

print(f"Unmatched closes (no corresponding open): {len(unmatched)}")
for u in unmatched:
    line_num = content[:u[1]].count('\n') + 1
    print(f"  Position {u[1]}, line {line_num}")

print(f"Unclosed opens (no corresponding close): {len(stack)}")
for s in stack:
    line_num = content[:s[1]].count('\n') + 1
    print(f"  Position {s[1]}, line {line_num}")