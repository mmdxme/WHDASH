import re
from pathlib import Path

filepath = Path('templates/documents/report_access_log.html')
content = filepath.read_text(encoding='utf-8')

print('Lines around include:')
for i, line in enumerate(content.split('\n')[:20], 1):
    print(f'{i:3}: {repr(line)}')

# Check include regex
INCLUDE_RE = re.compile(r"^\s*\{\% include ['\"]base\.html['\"] \%\}")
match = INCLUDE_RE.search(content)
print('\nInclude match:', match)

# Check block content
block_match = re.search(r"\{% block content %\}", content)
print('Block match:', block_match)

# Check endblock
endblock_match = re.search(r"\{% endblock %\}", content)
print('Endblock match:', endblock_match)

# Try simpler include regex
simple = re.search(r"\{\% include 'base\.html' \%\}", content)
print('Simple include:', simple)