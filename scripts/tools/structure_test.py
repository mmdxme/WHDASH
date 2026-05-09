#!/usr/bin/env python3

# Let's create a test that exactly mimics the translations.py structure at the boundary

# First, let me check: what does the start of the fa dict look like?
# From earlier output: fa dict starts at line 8186 with "    'fa': {"

# And fa dict ends at line 14740 with "    }," (4-space indent closing fa dict)
# Then line 14741 is blank
# Then line 14742 is "    'ar': {" (4-space indent starting ar dict)

# So the structure is:
# ...
#     },    <- closes fa dict (4 spaces before })
#          <- blank line
#     'ar': {  <- starts ar dict (4 spaces)
# ...

# Let's test if this structure works
test_a = """TRANSLATIONS = {
    'fa': {
        'key1': 'value1',
    },

    'ar': {
        'key2': 'value2',
    },
}
"""

try:
    import ast
    ast.parse(test_a)
    print("test_a (blank line between dicts): parses OK")
except SyntaxError as e:
    print(f"test_a: FAIL - {e.msg} at line {e.lineno}")

# What about with more content before?
# Let's test with more realistic content that mimics actual translations

test_b = """TRANSLATIONS = {
    'fa': {
        'a': 'A',
        'b': 'B',
        'c': 'C',
        'd': 'D',
        'e': 'E',
        'f': 'F',
        'g': 'G',
        'h': 'H',
        'i': 'I',
        'j': 'J',
        'k': 'K',
        'l': 'L',
        'm': 'M',
        'n': 'N',
        'o': 'O',
        'p': 'P',
        'q': 'Q',
        'r': 'R',
        's': 'S',
        't': 'T',
        'u': 'U',
        'v': 'V',
        'w': 'W',
        'x': 'X',
        'y': 'Y',
        'z': 'Z',
        'search': '???',
        'save': '???',
        'cancel': '???',
        'export': '???',
        'import': '???',
        'actions': '???',
        'view_all': '???',
        'all_channels': '???',
        'all_statuses': '???',
    },

    'ru': {
        'app_name': '???',
    },
}
"""

try:
    ast.parse(test_b)
    print("test_b (mimics actual structure): parses OK")
except SyntaxError as e:
    print(f"test_b: FAIL - {e.msg} at line {e.lineno}")