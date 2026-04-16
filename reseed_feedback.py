"""Quick script to reseed feedback data."""
import time
from database import get_db, get_db_context, get_one, get_all

# Drop all feedback tables
with get_db_context() as db:
    db.execute('DROP TABLE IF EXISTS feedback_activity_log')
    db.execute('DROP TABLE IF EXISTS feedback_assignment_history')
    db.execute('DROP TABLE IF EXISTS feedback_status_history')
    db.execute('DROP TABLE IF EXISTS feedback_comments')
    db.execute('DROP TABLE IF EXISTS feedback_attachments')
    db.execute('DROP TABLE IF EXISTS feedback_report_tags')
    db.execute('DROP TABLE IF EXISTS feedback_tags')
    db.execute('DROP TABLE IF EXISTS feedback_notification_prefs')
    db.execute('DROP TABLE IF EXISTS feedback_settings')
    db.execute('DROP TABLE IF EXISTS feedback_reports')
    db.execute('DROP TABLE IF EXISTS feedback_categories')
    db.commit()
    print('Tables dropped successfully')

time.sleep(1)

# Import after dropping
from feedback_models import init_feedback_tables, get_categories, generate_reference_number
from feedback_models import create_report, add_comment, log_activity, get_report_by_id, change_status
from feedback_models import assign_report, add_attachment, delete_report, get_stats
from feedback_models import STATUS_CHOICES, PRIORITY_CHOICES

# Initialize tables
init_feedback_tables()
print('Tables initialized')

# Sample data - using reporter_user_id=1 (admin) for all
SAMPLE_REPORTS = [
    {
        'title': 'Login page crashes on mobile devices',
        'report_type': 'bug',
        'priority': 'High',
        'status': 'In Progress',
        'description': 'When attempting to login from a mobile device (iOS Safari and Chrome Android), the login page crashes after entering credentials. The error occurs consistently when tapping the submit button.',
        'expected_behavior': 'User should be able to login successfully from any device including mobile.',
        'actual_behavior': 'Page crashes and returns to the login screen without any error message.',
        'steps_to_reproduce': '1. Open the application on a mobile device\n2. Navigate to the login page\n3. Enter valid credentials\n4. Tap the Submit button\n5. Observe the crash',
        'affected_module': 'Authentication',
        'frequency': 'always',
        'browser_info': 'Safari iOS 17.2 / Chrome Android 120',
    },
    {
        'title': 'Dashboard charts not loading for premium users',
        'report_type': 'bug',
        'priority': 'High',
        'status': 'Under Review',
        'description': 'The analytics dashboard charts fail to load for users with premium subscriptions. The loading spinner appears indefinitely and no data is displayed.',
        'expected_behavior': 'Charts should load and display data for all premium users.',
        'actual_behavior': 'Charts show loading spinner forever, never displaying data.',
        'affected_module': 'Dashboard',
        'frequency': 'always',
    },
    {
        'title': 'Add dark mode support to the application',
        'report_type': 'feature_request',
        'priority': 'Medium',
        'status': 'Open',
        'description': 'Many users have requested dark mode support for the application. This would reduce eye strain and save battery on OLED devices.',
        'expected_behavior': 'Users should be able to toggle between light and dark themes.',
        'affected_module': 'UI',
    },
    {
        'title': 'Slow report generation - taking over 5 minutes',
        'report_type': 'performance',
        'priority': 'High',
        'status': 'Assigned',
        'description': 'Generating monthly reports takes over 5 minutes, significantly impacting productivity. Users have to wait and cannot use the system during this time.',
        'expected_behavior': 'Reports should generate within 30 seconds.',
        'actual_behavior': 'Reports take 5-10 minutes to generate.',
        'affected_module': 'Reports',
        'frequency': 'often',
    },
    {
        'title': 'Cannot export data to Excel format',
        'report_type': 'bug',
        'priority': 'Medium',
        'status': 'Resolved',
        'description': 'The export to Excel button is not working. When clicked, nothing happens.',
        'expected_behavior': 'Clicking export should download an Excel file.',
        'actual_behavior': 'No download occurs.',
        'affected_module': 'Reports',
        'frequency': 'sometimes',
    },
    {
        'title': 'User permissions not applying correctly after role change',
        'report_type': 'access_issue',
        'priority': 'Critical',
        'status': 'New',
        'description': "After changing a user's role from Manager to Employee, the new permissions are not being applied. The user still has access to manager-level features.",
        'expected_behavior': 'Permissions should immediately reflect the new role.',
        'actual_behavior': 'Old permissions persist until user logs out and back in.',
        'affected_module': 'User Management',
        'frequency': 'always',
        'is_confidential': True,
    },
    {
        'title': 'Add integration with Slack for notifications',
        'report_type': 'feature_request',
        'priority': 'Medium',
        'status': 'Backlog',
        'description': 'Our team uses Slack extensively. It would be great to receive notifications and updates directly in Slack channels.',
        'expected_behavior': 'System should send Slack messages for important notifications.',
        'affected_module': 'Integrations',
    },
    {
        'title': 'Inventory counts are showing incorrect quantities',
        'report_type': 'data_issue',
        'priority': 'Critical',
        'status': 'In Progress',
        'description': 'The warehouse inventory system is showing incorrect quantities. For example, item SKU-12345 shows 150 units but physical count reveals only 142.',
        'expected_behavior': 'Inventory counts should accurately reflect physical stock.',
        'actual_behavior': 'Displayed quantities do not match physical inventory.',
        'affected_module': 'WMS',
        'frequency': 'sometimes',
    },
]

print('Creating sample reports...')

for i, sample in enumerate(SAMPLE_REPORTS):
    report_data = {
        'title': sample['title'],
        'report_type': sample['report_type'],
        'status': sample['status'],
        'priority': sample['priority'],
        'description': sample['description'],
        'expected_behavior': sample.get('expected_behavior', ''),
        'actual_behavior': sample.get('actual_behavior', ''),
        'steps_to_reproduce': sample.get('steps_to_reproduce', ''),
        'affected_module': sample.get('affected_module', ''),
        'frequency': sample.get('frequency', 'unknown'),
        'browser_info': sample.get('browser_info', ''),
        'reporter_user_id': 1,  # Admin user
        'reporter_name': 'Admin User',
        'reporter_department': 'Administration',
        'is_confidential': sample.get('is_confidential', False),
        'submit_now': True,
    }

    report_id = create_report(report_data, 1)
    title = sample["title"][:50] + "..." if len(sample["title"]) > 50 else sample["title"]
    print(f'Created report {i+1}: {title}')

print('Seed data complete!')
