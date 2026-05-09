with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count triple quotes
count_triple_single = content.count("'''")
count_triple_double = content.count('"""')

print(f"Triple single quotes: {count_triple_single}")
print(f"Triple double quotes: {count_triple_double}")

# If odd number of triple single quotes, that's a problem
if count_triple_single % 2 != 0:
    print("WARNING: Odd number of triple single quotes!")

if count_triple_double % 2 != 0:
    print("WARNING: Odd number of triple double quotes!")

# Check the end of file
lines = content.split('\n')
print(f"\nTotal lines: {len(lines)}")
print(f"Last line: {repr(lines[-1])}")
print(f"Second to last: {repr(lines[-2])}")