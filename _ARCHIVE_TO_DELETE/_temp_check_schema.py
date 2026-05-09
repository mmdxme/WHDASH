import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
from database import get_one
schema = get_one("SELECT sql FROM sqlite_master WHERE type='table' AND name='roles'")
print(schema['sql'] if schema else 'not found')