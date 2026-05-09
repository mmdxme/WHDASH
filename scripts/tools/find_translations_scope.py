#!/usr/bin/env python3

# I need to properly understand where TRANSLATIONS opens and closes

with open('translations_normalized.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# The TRANSLATIONS dict should open at line 8 with "'en': {"
# and should close at the very end of the file (or near it)

# Let me trace bracket balance more carefully
# Starting at balance = 0 before the file starts

balance = 0
translations_open = None

# Start from line 1 and trace
for i in range(len(lines)):
    line = lines[i]
    # Check if this line contains the TRANSLATIONS = { opening
    if 'TRANSLATIONS' in line and '=' in line and '{' in line:
        # This is where TRANSLATIONS opens
        translations_open = i + 1  # 1-indexed

    for c in line:
        if c == '{':
            balance += 1
        elif c == '}':
            balance -= 1

    # Check if TRANSLATIONS closes
    # It would close when balance goes back to 0 after being opened

print(f"TRANSLATIONS opens at line: {translations_open}")
print(f"Final balance at end of file: {balance}")

# Now let's check what's happening at line 21089
# If balance is 0 at line 21089, that means something closed at that line
# But TRANSLATIONS shouldn't close until the end

# Let me trace balance specifically around the problem area
print("\nBracket balance around lines 21085-21095:")
bal_at_line_start = []
running = 0
for i in range(21084, 21096):
    # Balance before this line
    for j in range(i):
        for c in lines[j]:
            if c == '{':
                running += 1
            elif c == '}':
                running -= 1
    bal_at_line_start.append((i+1, running))

for ln, bal in bal_at_line_start:
    print(f"  Before line {ln}: balance = {bal}")

# Also: find where line 21089 "}," is and what it closes
print("\nLooking at what closes at line 21089:")
# Get content of lines 21085-21092
for i in range(21084, 21092):
    line = lines[i]
    print(f"Line {i+1}: {repr(line[:60])}")