"""
Extract all url_for() calls from template files.
"""
import os
import re
from collections import defaultdict

TEMPLATES_DIR = r"C:\Users\sdads\WHDASH\templates"

# Pattern to match url_for('endpoint', arg1=val1, arg2=val2, ...)
URL_FOR_PATTERN = re.compile(
    r"url_for\s*\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*([^)]+))?\)"
)

def extract_url_for_calls(filepath):
    """Extract all url_for calls from a single file."""
    results = []
    try:
        with open(filepath, encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return results

    for match in URL_FOR_PATTERN.finditer(content):
        endpoint = match.group(1)
        args_str = match.group(2) or ""
        args = [a.strip() for a in args_str.split(',') if a.strip()]
        results.append({
            'endpoint': endpoint,
            'args': args,
            'line': content[:match.start()].count('\n') + 1
        })
    return results

def main():
    all_results = defaultdict(list)  # endpoint -> list of (file, args, line)

    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, TEMPLATES_DIR)
                calls = extract_url_for_calls(filepath)
                for call in calls:
                    all_results[call['endpoint']].append({
                        'file': rel_path,
                        'args': call['args'],
                        'line': call['line']
                    })

    # Sort by endpoint name
    for endpoint in sorted(all_results.keys()):
        entries = all_results[endpoint]
        print(f"\n{'='*80}")
        print(f"ENDPOINT: {endpoint}")
        print(f"TOTAL REFERENCES: {len(entries)}")
        print(f"{'='*80}")
        for entry in sorted(entries, key=lambda x: (x['file'], x['line'])):
            args_str = f" | Args: {', '.join(entry['args'])}" if entry['args'] else ""
            print(f"  {entry['file']} (line {entry['line']}){args_str}")

    print(f"\n\n{'#'*80}")
    print(f"TOTAL UNIQUE ENDPOINTS: {len(all_results)}")
    print(f"TOTAL url_for() CALLS: {sum(len(v) for v in all_results.values())}")

if __name__ == '__main__':
    main()
