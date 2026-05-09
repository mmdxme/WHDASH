"""
Feedback System Seed Data
=========================
Sample/demo data for the feedback and reporting system.

This module provides realistic sample reports, comments, and activity
to populate the feedback system for demonstration purposes.

Usage:
    from feedback_seed_data import seed_feedback_data
    seed_feedback_data()
"""

import json
import random
from datetime import datetime, timedelta
from database import get_db, get_db_context

# Sample data
SAMPLE_USERS = [
    {'id': 1, 'name': 'Alex Thompson', 'department': 'Engineering'},
    {'id': 2, 'name': 'Sarah Chen', 'department': 'Product'},
    {'id': 3, 'name': 'Mike Rodriguez', 'department': 'Sales'},
    {'id': 4, 'name': 'Emily Watson', 'department': 'Customer Support'},
    {'id': 5, 'name': 'David Kim', 'department': 'Engineering'},
    {'id': 6, 'name': 'Lisa Park', 'department': 'Marketing'},
    {'id': 7, 'name': 'James Wilson', 'department': 'Operations'},
    {'id': 8, 'name': 'Anna Martinez', 'department': 'Finance'},
]

SAMPLE_REPORTS = [
    {
        'title': 'Login page crashes on mobile devices',
        'report_type': 'bug',
        'category': 'Bug',
        'priority': 'High',
        'severity': 'Critical',
        'impact': 'Team',
        'urgency': 'Urgent',
        'status': 'In Progress',
        'description': 'When attempting to login from a mobile device (iOS Safari and Chrome Android), the login page crashes after entering credentials. The error occurs consistently when tapping the submit button.',
        'expected_behavior': 'User should be able to login successfully from any device including mobile.',
        'actual_behavior': 'Page crashes and returns to the login screen without any error message.',
        'steps_to_reproduce': '1. Open the application on a mobile device\n2. Navigate to the login page\n3. Enter valid credentials\n4. Tap the Submit button\n5. Observe the crash',
        'affected_module': 'Authentication',
        'frequency': 'always',
        'browser_info': 'Safari iOS 17.2 / Chrome Android 120',
        'device_info': 'iPhone 15 Pro / Samsung Galaxy S24',
        'operating_system': 'iOS 17.2 / Android 14',
    },
    {
        'title': 'Dashboard charts not loading for premium users',
        'report_type': 'bug',
        'category': 'Bug',
        'priority': 'High',
        'severity': 'Major',
        'impact': 'Team',
        'urgency': 'Urgent',
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
        'category': 'Feature',
        'priority': 'Medium',
        'severity': 'Minor',
        'impact': 'Team',
        'urgency': 'Normal',
        'status': 'Open',
        'description': 'Many users have requested dark mode support for the application. This would reduce eye strain and save battery on OLED devices.',
        'expected_behavior': 'Users should be able to toggle between light and dark themes.',
        'affected_module': 'UI',
    },
    {
        'title': 'Slow report generation - taking over 5 minutes',
        'report_type': 'performance',
        'category': 'Performance',
        'priority': 'High',
        'severity': 'Major',
        'impact': 'Department',
        'urgency': 'Urgent',
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
        'category': 'Bug',
        'priority': 'Medium',
        'severity': 'Minor',
        'impact': 'Low',
        'urgency': 'Normal',
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
        'category': 'Access',
        'priority': 'Critical',
        'severity': 'Critical',
        'impact': 'Company-wide',
        'urgency': 'Immediate',
        'status': 'New',
        'description': 'After changing a user\'s role from Manager to Employee, the new permissions are not being applied. The user still has access to manager-level features.',
        'expected_behavior': 'Permissions should immediately reflect the new role.',
        'actual_behavior': 'Old permissions persist until user logs out and back in.',
        'affected_module': 'User Management',
        'frequency': 'always',
        'is_confidential': True,
    },
    {
        'title': 'Add integration with Slack for notifications',
        'report_type': 'feature_request',
        'category': 'Integration',
        'priority': 'Medium',
        'severity': 'Minor',
        'impact': 'Team',
        'urgency': 'Normal',
        'status': 'Backlog',
        'description': 'Our team uses Slack extensively. It would be great to receive notifications and updates directly in Slack channels.',
        'expected_behavior': 'System should send Slack messages for important notifications.',
        'affected_module': 'Integrations',
    },
    {
        'title': 'Inventory counts are showing incorrect quantities',
        'report_type': 'data_issue',
        'category': 'Data',
        'priority': 'Critical',
        'severity': 'Critical',
        'impact': 'Department',
        'urgency': 'Immediate',
        'status': 'In Progress',
        'description': 'The warehouse inventory system is showing incorrect quantities. For example, item SKU-12345 shows 150 units but physical count reveals only 142.',
        'expected_behavior': 'Inventory counts should accurately reflect physical stock.',
        'actual_behavior': 'Displayed quantities do not match physical inventory.',
        'affected_module': 'WMS',
        'frequency': 'sometimes',
    },
    {
        'title': 'Improve search functionality with filters',
        'report_type': 'improvement',
        'category': 'UI/UX',
        'priority': 'Low',
        'severity': 'Minor',
        'impact': 'Low',
        'urgency': 'Low',
        'status': 'Open',
        'description': 'The current search is too basic. Adding filters for date range, category, and status would make it much more useful.',
        'expected_behavior': 'Search should support multiple filters and operators.',
        'affected_module': 'Search',
    },
    {
        'title': 'API endpoints timing out under heavy load',
        'report_type': 'performance',
        'category': 'Performance',
        'priority': 'High',
        'severity': 'Major',
        'impact': 'Department',
        'urgency': 'Urgent',
        'status': 'Under Review',
        'description': 'During peak hours (9-11 AM), API endpoints frequently timeout. This affects approximately 30% of requests during this period.',
        'expected_behavior': 'API should respond within 2 seconds under normal load.',
        'actual_behavior': 'Requests timeout after 30 seconds during peak hours.',
        'affected_module': 'API',
        'frequency': 'often',
    },
    {
        'title': 'Complaint: Delayed response from support team',
        'report_type': 'complaint',
        'category': 'Complaint',
        'priority': 'Medium',
        'severity': 'Minor',
        'impact': 'Team',
        'urgency': 'Normal',
        'status': 'Waiting for Internal',
        'description': 'I submitted a ticket 5 days ago and still haven\'t received a response. This is unacceptable for a premium customer.',
        'expected_behavior': 'Support should respond within 24 hours.',
        'actual_behavior': 'No response after 5 days.',
        'affected_module': 'Customer Support',
        'reporter_name': 'External Customer',
        'reporter_email': 'customer@example.com',
    },
    {
        'title': 'Add keyboard shortcuts for power users',
        'report_type': 'feature_request',
        'category': 'Feature',
        'priority': 'Low',
        'severity': 'Minor',
        'impact': 'Team',
        'urgency': 'Low',
        'status': 'Open',
        'description': 'Adding keyboard shortcuts (like Ctrl+N for new item, Ctrl+S for save) would significantly improve efficiency for power users.',
        'affected_module': 'UI',
    },
    {
        'title': 'System error when uploading large files',
        'report_type': 'system_error',
        'category': 'Bug',
        'priority': 'High',
        'severity': 'Major',
        'impact': 'Team',
        'urgency': 'Urgent',
        'status': 'Assigned',
        'description': 'When uploading files larger than 10MB, the system throws a generic error and the upload fails. Files under 10MB work fine.',
        'expected_behavior': 'Files up to 100MB should be uploadable.',
        'actual_behavior': 'Files over 10MB fail with error code 500.',
        'affected_module': 'File Upload',
        'frequency': 'always',
    },
    {
        'title': 'Suggestion: Add bulk actions for inventory management',
        'report_type': 'improvement',
        'category': 'Feature',
        'priority': 'Medium',
        'severity': 'Minor',
        'impact': 'Team',
        'urgency': 'Normal',
        'status': 'Open',
        'description': 'Being able to select multiple items and apply actions (adjust quantity, transfer location, etc.) would save significant time.',
        'affected_module': 'WMS',
    },
    {
        'title': 'Report generating incorrect totals for international orders',
        'report_type': 'data_issue',
        'category': 'Data',
        'priority': 'High',
        'severity': 'Critical',
        'impact': 'Department',
        'urgency': 'Urgent',
        'status': 'New',
        'description': 'Monthly sales reports are showing incorrect totals for orders with multiple currencies. The exchange rate conversion seems to be using outdated rates.',
        'expected_behavior': 'Totals should use current exchange rates at time of sale.',
        'actual_behavior': 'Incorrect conversion is causing revenue reporting errors.',
        'affected_module': 'Reports',
        'frequency': 'sometimes',
    },
]

SAMPLE_COMMENTS = [
    "I've confirmed this issue on my device. It seems to be related to the recent update.",
    "Looking into this now. Can you provide your user ID?",
    "This is a known issue and our team is working on a fix.",
    "The fix has been deployed. Please verify and close if resolved.",
    "Thanks for reporting. We'll prioritize this in the next sprint.",
    "Can you provide more details about when this started happening?",
    "I've assigned this to our backend team for investigation.",
    "The issue appears to be intermittent. We're monitoring.",
    "Please try clearing your cache and cookies, then try again.",
    "We've identified the root cause and are preparing a patch.",
]

SAMPLE_TAGS = ['urgent', 'backend', 'frontend', 'mobile', 'api', 'database', 'ui', 'performance', 'security', 'integration']


def seed_feedback_data():
    """Seed the feedback system with sample data."""
    from feedback_models import (
        init_feedback_tables, get_categories, generate_reference_number,
        create_report, add_comment, log_activity, get_report_by_id, change_status,
        assign_report, STATUS_CHOICES, PRIORITY_CHOICES
    )
    from flow_models import get_flow_profile
    
    # Initialize tables
    init_feedback_tables()
    
    db = get_db()
    
    # Check if data already exists
    existing = db.execute("SELECT COUNT(*) as cnt FROM feedback_reports").fetchone()
    if existing['cnt'] > 0:
        print("Feedback data already exists. Skipping seed.")
        return
    
    print("Seeding feedback data...")
    
    categories = {cat['name']: cat['id'] for cat in get_categories()}
    
    report_ids = []
    
    for i, sample in enumerate(SAMPLE_REPORTS):
        # Create the report
        reporter = random.choice(SAMPLE_USERS)
        assignee = random.choice(SAMPLE_USERS) if sample['status'] not in ['Open', 'New', 'Draft'] else None
        
        # Calculate dates
        days_ago = random.randint(1, 30)
        created_at = (datetime.now() - timedelta(days=days_ago)).isoformat()
        updated_at = (datetime.now() - timedelta(days=random.randint(0, days_ago))).isoformat()
        
        # Build report data
        report_data = {
            'title': sample['title'],
            'report_type': sample['report_type'],
            'category_id': categories.get(sample.get('category', 'Bug')),
            'status': sample['status'],
            'priority': sample['priority'],
            'severity': sample['severity'],
            'impact': sample['impact'],
            'urgency': sample['urgency'],
            'description': sample['description'],
            'expected_behavior': sample.get('expected_behavior', ''),
            'actual_behavior': sample.get('actual_behavior', ''),
            'steps_to_reproduce': sample.get('steps_to_reproduce', ''),
            'affected_module': sample.get('affected_module', ''),
            'frequency': sample.get('frequency', 'unknown'),
            'browser_info': sample.get('browser_info', ''),
            'device_info': sample.get('device_info', ''),
            'operating_system': sample.get('operating_system', ''),
            'visibility': 'public',
            'is_confidential': sample.get('is_confidential', False),
            'reporter_user_id': reporter['id'],
            'reporter_name': sample.get('reporter_name', reporter['name']),
            'reporter_email': sample.get('reporter_email', f"{reporter['id']}@example.com"),
            'reporter_department': reporter['department'],
            'tags': json.dumps(random.sample(SAMPLE_TAGS, k=random.randint(1, 3))),
            'submit_now': True,
        }
        
        report_id = create_report(report_data, reporter['id'])
        report_ids.append(report_id)
        
        # Update created_at
        db.execute("""
            UPDATE feedback_reports 
            SET created_at = ?, updated_at = ?, submitted_at = ?
            WHERE id = ?
        """, (created_at, updated_at, created_at, report_id))
        
        # Add assignment if applicable
        if assignee:
            assign_report(
                report_id, assignee['id'], assignee['name'],
                team=f"{assignee['department']} Team",
                assigned_by_id=1, assigned_by_name='System',
                reason='Auto-assigned based on category'
            )
            # Update assigned_at
            db.execute("""
                UPDATE feedback_reports 
                SET assigned_at = ?
                WHERE id = ?
            """, (updated_at, report_id))
        
        # Add initial status history
        db.execute("""
            INSERT INTO feedback_status_history 
            (report_id, from_status, to_status, changed_by_user_id, changed_by_name, is_automatic, created_at)
            VALUES (?, NULL, ?, ?, ?, 1, ?)
        """, (report_id, sample['status'], reporter['id'], reporter['name'], created_at))
        
        # Add comments
        num_comments = random.randint(0, 4)
        for j in range(num_comments):
            commenter = random.choice(SAMPLE_USERS)
            comment_time = (datetime.fromisoformat(created_at) + timedelta(hours=random.randint(1, 48))).isoformat()
            
            comment_content = random.choice(SAMPLE_COMMENTS)
            is_internal = random.choice([True, False]) if commenter['department'] in ['Engineering', 'Product'] else False
            
            db.execute("""
                INSERT INTO feedback_comments 
                (report_id, author_user_id, author_name, content, is_internal, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (report_id, commenter['id'], commenter['name'], comment_content, 1 if is_internal else 0, comment_time))
        
        # Update comment count
        db.execute("UPDATE feedback_reports SET comment_count = (SELECT COUNT(*) FROM feedback_comments WHERE report_id = ?) WHERE id = ?", (report_id, report_id))
        
        # Add activity
        log_activity(report_id, 'created', reporter['id'], reporter['name'], f"Report created: {sample['title'][:50]}")
        
        if assignee:
            log_activity(report_id, 'assigned', assignee['id'], assignee['name'], f"Assigned to {assignee['name']}")
        
        # Add some status changes for resolved/closed items
        if sample['status'] in ['Resolved', 'Closed', 'Verified']:
            resolved_time = (datetime.fromisoformat(updated_at) + timedelta(hours=24)).isoformat()
            db.execute("""
                INSERT INTO feedback_status_history 
                (report_id, from_status, to_status, changed_by_user_id, changed_by_name, is_automatic, created_at)
                VALUES (?, ?, 'Resolved', ?, 'System', 1, ?)
            """, (report_id, sample['status'], assignee['id'] if assignee else 1, resolved_time))
            
            db.execute("""
                UPDATE feedback_reports 
                SET status = 'Resolved', resolved_at = ?
                WHERE id = ?
            """, (resolved_time, report_id))
            
            log_activity(report_id, 'status_changed', assignee['id'] if assignee else 1, 
                        assignee['name'] if assignee else 'System', 'Status changed to Resolved')
        
        db.commit()
    
    print(f"Created {len(report_ids)} sample reports with comments and activity.")
    
    # Create some sample attachments (just metadata, no actual files)
    for report_id in report_ids[:5]:
        num_attachments = random.randint(1, 3)
        for j in range(num_attachments):
            file_types = ['image', 'document', 'video']
            file_type = random.choice(file_types)
            
            extensions = {
                'image': ['png', 'jpg', 'gif'],
                'document': ['pdf', 'docx', 'xlsx'],
                'video': ['mp4', 'mov']
            }
            
            ext = random.choice(extensions[file_type])
            filename = f"sample_attachment_{j+1}.{ext}"
            filepath = f"feedback_uploads/{file_type}s/{filename}"
            
            db.execute("""
                INSERT INTO feedback_attachments 
                (report_id, file_name, file_path, file_type, file_size, mime_type, uploaded_by, uploaded_by_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, filename, filepath, file_type,
                random.randint(100000, 5000000),  # 100KB to 5MB
                f'application/{ext}',
                random.choice(SAMPLE_USERS)['id'],
                random.choice(SAMPLE_USERS)['name'],
                datetime.now().isoformat()
            ))
        
        # Update attachment count
        db.execute("UPDATE feedback_reports SET attachment_count = ? WHERE id = ?", (num_attachments, report_id))
        db.commit()
    
    print(f"Added sample attachments to reports.")
    print("Feedback seed data complete!")


if __name__ == '__main__':
    seed_feedback_data()
