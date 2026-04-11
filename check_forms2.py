"""Check form builder templates."""
from form_models import get_form_templates, get_form_template

templates = get_form_templates()
print(f'Templates: {len(templates)}')
for t in templates:
    print(f'  - {t["id"]}: {t["form_title"]} ({t["status"]})')

# Check sections
from form_models import get_template_sections
for t in templates[:3]:
    sections = get_template_sections(t['id'])
    print(f'  Template {t["id"]} has {len(sections)} sections')

    from form_models import get_section_fields
    total_fields = 0
    for s in sections:
        fields = get_section_fields(s['id'])
        total_fields += len(fields)
    print(f'  Total fields: {total_fields}')
