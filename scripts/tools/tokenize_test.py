# Use tokenize to find exact error location
import tokenize
import io

with open('quality_models.py', 'rb') as f:
    data = f.read()

try:
    list(tokenize.tokenize(io.BytesIO(data).readline))
    print('Tokenize: SUCCESS')
except tokenize.TokenError as e:
    print(f'Tokenize error: {e}')
except Exception as e:
    print(f'Other error: {type(e).__name__}: {e}')