"""Fix form builder tables by dropping and recreating."""
from database import get_db_context

with get_db_context() as db:
    tables = [
        'form_field_options', 'form_fields', 'form_sections', 'form_templates',
        'form_template_versions', 'form_workflows', 'workflow_steps', 'workflow_transitions',
        'form_submissions', 'form_submission_values', 'form_submission_rows',
        'form_submission_row_values', 'form_submission_attachments', 'form_status_history',
        'form_comments', 'form_signatures', 'form_assignments', 'form_approvals',
        'form_notifications', 'form_numbering_rules', 'form_links',
        'form_template_access', 'form_access_log'
    ]
    for t in tables:
        try:
            db.execute(f'DROP TABLE IF EXISTS {t}')
            print(f'Dropped: {t}')
        except Exception as e:
            print(f'Error dropping {t}: {e}')
    db.commit()

print('\nAll form builder tables dropped. Now run: python seed_form_templates.py')
