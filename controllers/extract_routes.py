"""Extract all routes from navigation.py MENU_STRUCTURE."""
import re

with open('navigation.py', 'r', encoding='utf-8') as f:
    content = f.read()

# MENU_STRUCTURE starts at line 36, ROUTE_BREADCRUMBS at 13967
# So MENU_STRUCTURE ends before 13967
lines = content.split('\n')

routes = []
current_module = None

for i, line in enumerate(lines[:13967], 1):
    stripped = line.lstrip()
    indent = len(line) - len(stripped)

    # Module key detection at indent 4 (2 spaces per level in this file)
    module_match = re.match(r"^\s+'([a-zA-Z_][a-zA-Z0-9_]*)':\s*\{", line)
    if module_match and indent == 4:
        current_module = module_match.group(1)
        continue

    # Route detection at indent 4 (module level) or indent 8 (item level)
    route_match = re.match(r"^\s+'route':\s+'([^']+)'", line)
    if route_match:
        route = route_match.group(1)
        level = 'module' if indent == 4 else 'item'
        routes.append((i, route, current_module or 'unknown', level))

print(f"Total routes found: {len(routes)}")
print()
for line_num, route, module, level in routes:
    print(f"{line_num}: {route} | {module} | {level}")
