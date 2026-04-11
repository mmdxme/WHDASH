"""Fix syntax error in quality_models.py"""
with open('quality_models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check for the problematic string formatting pattern
problematic = '""" % where_sql'
if problematic in content:
    # Find the line and check context
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if problematic in line:
            print(f"Found at line {i+1}: {repr(line)}")
            # Check if query is properly closed
            # Find the opening query =
            for j in range(i-1, max(0, i-20), -1):
                if 'query = """' in lines[j] or "query = f""" " in lines[j] or 'query = f"""' in lines[j]:
                    print(f"Opening at line {j+1}: {repr(lines[j])}")
                    break
