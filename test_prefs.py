from app import build_user_preferences

# Test build_user_preferences without arguments
result = build_user_preferences()
print("build_user_preferences() works:", result is not None)
print("Keys:", list(result.keys()) if result else "None")