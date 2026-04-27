#!/usr/bin/env python3

# Find the ACTUAL English dict close line

with open('translations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# Find fa dict start
fa_start = None
for i, line in enumerate(lines):
    if "'fa':" in line and "{" in line:
        fa_start = i
        break

print(f"fa dict starts at line {fa_start + 1}")

# Find the line BEFORE fa dict that's the English dict close
# It should be "    }," at 4-space indent
en_close = None
for i in range(fa_start - 1, max(0, fa_start - 10), -1):
    line = lines[i].rstrip('\n')
    if line.strip() == '},':
        indent = len(lines[i]) - len(lines[i].lstrip())
        if indent == 4:
            en_close = i
            print(f"English dict closes at line {i + 1}: {repr(lines[i])}")
            break

if en_close is None:
    print("ERROR: Could not find English dict close line")
    exit(1)

# Now the structure is:
# lines[0:en_close] = everything up to but NOT including the close line
# lines[en_close] = "    },\n" (the close line)
# lines[fa_start:] = fa dict onwards

# We need to insert project translations between lines[0:en_close] and lines[en_close]

project_translations = """        # Project Management
        'project_management': 'Project Management',
        'project_dashboard': 'Project Dashboard',
        'project_executive': 'Executive Dashboard',
        'project_pmo': 'PMO Workspace',
        'project_portfolio': 'Portfolio',
        'project_programs': 'Programs',
        'project_strategic_initiatives': 'Strategic Initiatives',
        'project_intake': 'Project Intake',
        'project_requests': 'Project Requests',
        'project_new_request': 'New Request',
        'project_business_case': 'Business Case',
        'project_request_review': 'Request Review',
        'project_approval_queue': 'Approval Queue',
        'project_rejected': 'Rejected',
        'project_approved_pipeline': 'Approved Pipeline',
        'project_list': 'Project List',
        'project_new': 'New Project',
        'project_active': 'Active',
        'project_onhold': 'On Hold',
        'project_completed': 'Completed',
        'project_cancelled': 'Cancelled',
        'project_archived': 'Archived',
        'project_charter': 'Project Charter',
        'project_scope': 'Scope',
        'project_team': 'Project Team',
        'project_stakeholders': 'Stakeholders',
        'project_objectives': 'Objectives',
        'project_baseline': 'Baseline',
        'project_governance': 'Governance',
        'project_wbs': 'WBS',
        'project_phases': 'Phases',
        'project_milestones': 'Milestones',
        'project_deliverables': 'Deliverables',
        'project_dependencies': 'Dependencies',
        'project_baseline_dates': 'Baseline Dates',
        'project_progress': 'Progress',
        'project_task_board': 'Task Board',
        'project_task_list': 'Task List',
        'project_my_tasks': 'My Tasks',
        'project_delayed': 'Delayed',
        'project_completed_tasks': 'Completed Tasks',
        'project_templates': 'Templates',
        'project_resource_pool': 'Resource Pool',
        'project_allocations': 'Allocations',
        'project_capacity': 'Capacity Planning',
        'project_utilization': 'Utilization',
        'project_conflicts': 'Allocation Conflicts',
        'project_availability': 'Availability',
        'project_budget': 'Budget',
        'project_budget_baseline': 'Budget Baseline',
        'project_actual_costs': 'Actual Costs',
        'project_cost_centers': 'Cost Centers',
        'project_commitments': 'Commitments',
        'project_budget_vs_actual': 'Budget vs Actual',
        'project_forecast': 'Forecast',
        'project_cost_reports': 'Cost Reports',
        'project_procurement': 'Procurement',
        'project_purchase_requests': 'Purchase Requests',
        'project_vendor_packages': 'Vendor Packages',
        'project_external_work': 'External Work',
        'project_contracts': 'Contracts',
        'project_procurement_reports': 'Procurement Reports',
        'project_timesheet': 'Timesheet',
        'project_effort': 'Effort',
        'project_resource_hours': 'Resource Hours',
        'project_planned_effort': 'Planned Effort',
        'project_actual_effort': 'Actual Effort',
        'project_overtime': 'Overtime',
        'project_risks': 'Risks',
        'project_risk_register': 'Risk Register',
        'project_risk_matrix': 'Risk Matrix',
        'project_mitigation': 'Mitigation',
        'project_risk_owners': 'Risk Owners',
        'project_escalated_risks': 'Escalated Risks',
        'project_closed_risks': 'Closed Risks',
        'project_risk_reports': 'Risk Reports',
        'project_issues': 'Issues',
        'project_issue_register': 'Issue Register',
        'project_open_issues': 'Open Issues',
        'project_assigned_issues': 'Assigned Issues',
        'project_issue_escalations': 'Issue Escalations',
        'project_resolutions': 'Resolutions',
        'project_closed_issues': 'Closed Issues',
        'project_issue_reports': 'Issue Reports',
        'project_changes': 'Changes',
        'project_change_requests': 'Change Requests',
        'project_scope_changes': 'Scope Changes',
        'project_schedule_changes': 'Schedule Changes',
        'project_budget_changes': 'Budget Changes',
        'project_change_approvals': 'Change Approvals',
        'project_approved_changes': 'Approved Changes',
        'project_rejected_changes': 'Rejected Changes',
        'project_change_reports': 'Change Reports',
        'project_documents': 'Documents',
        'project_version_history': 'Version History',
        'project_document_reports': 'Document Reports',
        'project_governance_reports': 'Governance Reports',
        'project_weekly_status': 'Weekly Status',
        'project_monthly_review': 'Monthly Review',
        'project_steering_committee': 'Steering Committee',
        'project_decisions': 'Decisions',
        'project_action_items': 'Action Items',
        'project_raid_summary': 'RAID Summary',
        'project_health': 'Health',
        'project_reports': 'Reports',
        'project_analytics': 'Analytics',
        'project_custom_reports': 'Custom Reports',
        'project_export_center': 'Export Center',
        'project_workflow': 'Workflow',
        'project_approval_rules': 'Approval Rules',
        'project_pending_approvals': 'Pending Approvals',
        'project_escalations': 'Escalations',
        'project_delegations': 'Delegations',
        'project_sla_policies': 'SLA Policies',
        'project_approval_history': 'Approval History',
        'project_settings': 'Settings',

        # Project Status Values
        'status_draft': 'Draft',
        'status_active': 'Active',
        'status_on_hold': 'On Hold',
        'status_completed': 'Completed',
        'status_cancelled': 'Cancelled',
        'status_archived': 'Archived',
        'status_pending': 'Pending',
        'status_in_progress': 'In Progress',
        'status_approved': 'Approved',
        'status_rejected': 'Rejected',
        'status_resolved': 'Resolved',
        'status_closed': 'Closed',
        'status_escalated': 'Escalated',
        'status_open': 'Open',

        # Project Priority Values
        'priority_low': 'Low',
        'priority_medium': 'Medium',
        'priority_high': 'High',
        'priority_critical': 'Critical',
        'priority_urgent': 'Urgent',

        # WBS Terms
        'wbs_code': 'WBS Code',
        'wbs_name': 'WBS Name',
        'wbs_level': 'Level',
        'wbs_parent': 'Parent',
        'wbs_child': 'Child',
        'wbs_builder': 'WBS Builder',

        # Task Terms
        'task_code': 'Task Code',
        'task_name': 'Task Name',
        'task_owner': 'Owner',
        'task_assignee': 'Assignee',
        'task_team': 'Team',
        'task_duration': 'Duration',
        'task_progress': 'Progress',
        'task_blocked': 'Blocked',
        'task_delay': 'Delay',
        'task_checklist': 'Checklist',
        'task_comment': 'Comment',
        'task_attachment': 'Attachment',
        'task_dependency': 'Dependency',

        # Milestone Terms
        'milestone_code': 'Milestone Code',
        'milestone_name': 'Milestone Name',
        'milestone_type': 'Type',
        'milestone_date': 'Date',
        'milestone_owner': 'Owner',
        'milestone_status': 'Status',
        'milestone_signoff': 'Sign-off',
        'milestone_deliverable': 'Deliverable',

        # Column Headers
        'column_project_name': 'Project Name',
        'column_project_code': 'Project Code',
        'column_status': 'Status',
        'column_priority': 'Priority',
        'column_start_date': 'Start Date',
        'column_end_date': 'End Date',
        'column_budget': 'Budget',
        'column_actual_cost': 'Actual Cost',
        'column_variance': 'Variance',
        'column_percent_complete': '% Complete',
        'column_manager': 'Manager',
        'column_owner': 'Owner',
        'column_assignee': 'Assignee',
        'column_created_date': 'Created Date',
        'column_modified_date': 'Modified Date',
        'column_description': 'Description',
        'column_notes': 'Notes',
        'column_attachments': 'Attachments',
        'column_actions': 'Actions',

        # Filter Labels
        'filter_all_projects': 'All Projects',
        'filter_all_statuses': 'All Statuses',
        'filter_all_priorities': 'All Priorities',
        'filter_all_managers': 'All Managers',
        'filter_date_range': 'Date Range',
        'filter_start_date': 'Start Date',
        'filter_end_date': 'End Date',
        'filter_budget_range': 'Budget Range',
        'filter_clear': 'Clear',
        'filter_apply': 'Apply',

        # Button Labels
        'btn_save': 'Save',
        'btn_cancel': 'Cancel',
        'btn_submit': 'Submit',
        'btn_delete': 'Delete',
        'btn_edit': 'Edit',
        'btn_view': 'View',
        'btn_close': 'Close',
        'btn_add': 'Add',
        'btn_remove': 'Remove',
        'btn_approve': 'Approve',
        'btn_reject': 'Reject',
        'btn_reassign': 'Reassign',
        'btn_export': 'Export',
        'btn_import': 'Import',
        'btn_print': 'Print',
        'btn_refresh': 'Refresh',
        'btn_search': 'Search',
        'btn_filter': 'Filter',
        'btn_clear': 'Clear',
        'btn_reset': 'Reset',
        'btn_upload': 'Upload',
        'btn_download': 'Download',
        'btn_preview': 'Preview',
        'btn_confirm': 'Confirm',
        'btn_back': 'Back',
        'btn_next': 'Next',
        'btn_previous': 'Previous',
        'btn_create': 'Create',
        'btn_update': 'Update',
        'btn_archive': 'Archive',
        'btn_restore': 'Restore',

        # Empty States
        'empty_projects': 'No projects found',
        'empty_projects_hint': 'Create your first project to get started',
        'empty_tasks': 'No tasks found',
        'empty_tasks_hint': 'No tasks match the current filter',
        'empty_milestones': 'No milestones found',
        'empty_milestones_hint': 'No milestones have been created yet',
        'empty_risks': 'No risks identified',
        'empty_risks_hint': 'No risks have been registered yet',
        'empty_issues': 'No issues reported',
        'empty_issues_hint': 'No issues have been reported yet',
        'empty_changes': 'No change requests',
        'empty_changes_hint': 'No change requests have been submitted',
        'empty_documents': 'No documents uploaded',
        'empty_documents_hint': 'Upload documents to this project',
        'empty_deliverables': 'No deliverables defined',
        'empty_deliverables_hint': 'Define deliverables for this project',
        'empty_team': 'No team members',
        'empty_team_hint': 'Add team members to this project',
        'empty_budget': 'No budget data',
        'empty_budget_hint': 'Set up budget for this project',
        'empty_reports': 'No reports available',
        'empty_reports_hint': 'Generate reports to view analytics',

        # Loading States
        'loading_projects': 'Loading projects...',
        'loading_tasks': 'Loading tasks...',
        'loading_milestones': 'Loading milestones...',
        'loading_risks': 'Loading risks...',
        'loading_issues': 'Loading issues...',
        'loading_changes': 'Loading changes...',
        'loading_documents': 'Loading documents...',
        'loading_budget': 'Loading budget data...',
        'loading_reports': 'Loading reports...',
        'loading_resources': 'Loading resources...',
        'loading_wait': 'Please wait...',
"""

# Construct new content:
# prefix = lines[:en_close]  (everything up to but NOT including the close line)
# then project translations
# then close line "    },\n"
# then rest = lines[fa_start:]

prefix = ''.join(lines[:en_close])
suffix = '    },\n' + ''.join(lines[fa_start:])
new_content = prefix + project_translations + suffix

# Write
with open('translations.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

# Verify
import ast
try:
    ast.parse(new_content)
    print("translations.py parses OK!")
except SyntaxError as e:
    print(f"translations.py FAILS: {e.msg} at line {e.lineno}")