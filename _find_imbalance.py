with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find all functions and track triple quote balance per function
current_func = None
func_start = 0
balance = 0  # +1 for open, -1 for close
in_triple = False
triple_char = None

func_stats = []

i = 0
while i < len(lines):
    line = lines[i]

    # Check for function definition
    if 'def ' in line and not current_func:
        current_func = line.strip()
        func_start = i + 1
        balance = 0
        in_triple = False

    # Track triple quotes in this line
    j = 0
    while j < len(line):
        if not in_triple:
            if line[j:j+3] == "'''":
                balance += 1
                in_triple = True
                j += 2
            elif line[j:j+3] == '"""':
                balance -= 1  # triple double closes what triple single opened (actually this doesn't mix)
                j += 2
            j += 1
        else:
            # We're inside a triple quote, look for closing
            if line[j:j+3] == "'''":
                balance -= 1
                in_triple = False
                j += 2
            j += 1

    # Check for end of function (next def or route, or end of file)
    if current_func:
        if i < len(lines) - 1:
            next_line = lines[i+1]
            if ('def ' in next_line and not 'api' in next_line and not 'report' in next_line) or \
               '@app.route' in next_line or '@manufacturing_bp.route' in next_line:
                if balance != 0:
                    print(f"Function at line {func_start}: {current_func[:60]}")
                    print(f"  Triple quote balance: {balance} (should be 0)")
                    print(f"  Last line: {line.strip()[:60]}")
                    print()
                func_stats.append((func_start, current_func[:50], balance))
                current_func = None

    i += 1

# Check last function
if current_func and balance != 0:
    print(f"Last function at line {func_start}: {current_func[:60]}")
    print(f"  Triple quote balance: {balance}")

print("Functions with imbalance:")
for item in func_stats:
    if item[2] != 0:
        print(f"  Line {item[0]}: {item[1]} (balance={item[2]})")