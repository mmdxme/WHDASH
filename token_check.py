import tokenize
import io

with open('C:/Users/sdads/WHDASH/translations.py', 'rb') as f:
    try:
        tokenize.tokenize(f.readline)
        print("No syntax error found")
    except tokenize.TokenError as e:
        print(f"TokenError: {e}")
    except IndentationError as e:
        print(f"IndentationError at line {e.lineno}: {e.msg}")
        print(f"Text: {e.text}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")