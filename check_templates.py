"""Check form templates."""
from database import get_all, get_db_context

print("Form Templates:")
templates = get_all("SELECT id, template_code, form_title, status FROM form_templates ORDER BY id")
for t in templates:
    print(f"  {t['id']}: {t['template_code']} - {t['form_title']} ({t['status']})")

print(f"\nTotal: {len(templates)} templates")

# Check sections and fields count
with get_db_context() as db:
    sections = db.execute("SELECT COUNT(*) as cnt FROM form_sections").fetchone()
    fields = db.execute("SELECT COUNT(*) as cnt FROM form_fields").fetchone()
    print(f"Total Sections: {sections['cnt']}")
    print(f"Total Fields: {fields['cnt']}")
