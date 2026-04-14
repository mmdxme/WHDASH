import sys
sys.path.insert(0, 'C:\\Users\\sdads\\WHDASH')

from flow_models import get_or_create_private_conversation

# Test creating a private conversation between user 1 and user 6
try:
    conv_id = get_or_create_private_conversation(1, 6)
    print(f"SUCCESS: conv_id = {conv_id}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
