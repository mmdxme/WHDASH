"""Create quality template directories."""
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(base_dir, 'templates', 'quality')

subdirs = [
    'inspections',
    'ncr',
    'capa',
    'audits',
    'reports'
]

for subdir in subdirs:
    path = os.path.join(templates_dir, subdir)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")

print("Done!")
