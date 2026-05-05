with open('manufacturing_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Simple approach: replace all triple single quotes with triple double quotes
new_content = content.replace("'''", '"""')

print(f"Original triple single quotes: {content.count(chr(39)+chr(39)+chr(39))}")
print(f"New triple single quotes: {new_content.count(chr(39)+chr(39)+chr(39))}")
print(f"Original triple double quotes: {content.count('\"\"\"')}")
print(f"New triple double quotes: {new_content.count('\"\"\"')}")

# Write back
with open('manufacturing_routes.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\nFile updated.")