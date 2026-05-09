"""
Initial Baseline Schema
=======================
Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-06

This is the baseline migration that captures the current full schema.
All schema definitions are consolidated here as the single source of truth.
Future schema changes MUST go through new Alembic migrations.

Tables covered:
- Core: companies, roles, users, categories, brands, statuses, parts, inventory, movements
- Sales: customers, customer_transactions
- Logistics: delivery_trips, delivery_stops, delivery_activity_logs, delivery_activities, vehicles
- WMS: warehouses
- Supply: suppliers
- Tasks: task_departments, task_items, task_subtasks, task_history,
          task_transaction_categories, task_transactions, task_report_snapshots,
          task_user_permissions
- Issues: issue_items, issue_history, issue_comments, issue_attachments,
           issue_watchers, issue_escalations, issue_categories,
           issue_sla_rules, issue_workflow_rules
- User: user_preferences, user_task_preferences, user_issue_preferences
- Google: google_workspace_tokens, google_workspace_settings
- Platform: platform_audit_log, platform_notifications, platform_settings,
            user_profile_extensions, user_notification_preferences,
            user_privacy_settings, user_linked_accounts, user_sessions
"""

from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # CORE TABLES (from schema.sql)
    # ========================================================================

    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('role_name', sa.String(length=50), nullable=False),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE')),
        sa.Column('can_edit_stock', sa.Boolean(), server_default='0'),
        sa.Column('can_manage_users', sa.Boolean(), server_default='0'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=50), nullable=False, unique=True),
        sa.Column('email', sa.String(length=150), nullable=False, unique=True),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('profile_pic', sa.String(length=255), server_default='default.png'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id']),
    )

    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
    )

    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), server_default='Genuine'),
    )

    op.create_table(
        'statuses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=50), nullable=False),
    )

    op.create_table(
        'parts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('part_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('brand_id', sa.Integer(), nullable=True),
        sa.Column('status_id', sa.Integer(), nullable=True),
        sa.Column('cost_price', sa.Float(), server_default='0.0'),
        sa.Column('reorder_point', sa.Integer(), server_default='10'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('item_code', sa.String(length=50), nullable=True),
        sa.Column('barcode', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id']),
        sa.ForeignKeyConstraint(['status_id'], ['statuses.id']),
    )

    op.create_table(
        'inventory',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('part_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('zone', sa.String(length=50), nullable=True),
        sa.Column('quantity', sa.Integer(), server_default='0'),
        sa.Column('warehouse_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
    )

    op.create_table(
        'movements',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('part_id', sa.Integer(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('warehouse_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id']),
    )

    # ========================================================================
    # SALES / CUSTOMER TABLES
    # ========================================================================

    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=True),
        sa.Column('salesperson_id', sa.Integer(), nullable=True),
        sa.Column('working_hours', sa.String(length=100), nullable=True),
        sa.Column('working_days', sa.String(length=50), nullable=True),
        sa.Column('balance', sa.Numeric(precision=12, scale=2), server_default='0.00'),
        sa.Column('credit_limit', sa.Numeric(precision=12, scale=2), server_default='5000.00'),
        sa.Column('status', sa.String(length=20), server_default='Active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['salesperson_id'], ['users.id']),
    )

    op.create_table(
        'customer_transactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )

    # ========================================================================
    # LOGISTICS TABLES
    # ========================================================================

    op.create_table(
        'delivery_activities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'delivery_trips',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), server_default=sa.text('CURRENT_DATE')),
        sa.Column('warehouse_departure', sa.DateTime(), nullable=True),
        sa.Column('warehouse_arrival', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='At Warehouse'),
        sa.Column('warehouse_checkin', sa.DateTime(), nullable=True),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['driver_id'], ['users.id']),
    )

    op.create_table(
        'delivery_stops',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('arrival_time', sa.DateTime(), nullable=True),
        sa.Column('departure_time', sa.DateTime(), nullable=True),
        sa.Column('arrival_gps', sa.String(length=100), nullable=True),
        sa.Column('departure_gps', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Pending'),
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['delivery_trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    )

    op.create_table(
        'delivery_activity_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['delivery_trips.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    )

    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('plate_number', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='Active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # ========================================================================
    # WAREHOUSE TABLES
    # ========================================================================

    op.create_table(
        'warehouses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
    )

    # ========================================================================
    # SUPPLIER TABLES
    # ========================================================================

    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('payment_terms', sa.String(length=50), server_default='Net 30'),
        sa.Column('lead_time', sa.String(length=50), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD'),
        sa.Column('margin', sa.String(length=10), nullable=True),
        sa.Column('rating', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(length=20), server_default='Active'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # ========================================================================
    # TASK MANAGEMENT TABLES
    # ========================================================================

    op.create_table(
        'task_departments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='Active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'task_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('priority', sa.String(length=20), server_default='Medium'),
        sa.Column('report_to_user_id', sa.Integer(), nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(length=20), server_default='Open'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('latest_note', sa.Text(), nullable=True),
        sa.Column('due_at', sa.String(length=50), nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default='0'),
        sa.Column('archived_at', sa.String(length=50), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('reminder_days', sa.Integer(), server_default='0'),
        sa.Column('reminder_hours', sa.Integer(), server_default='0'),
        sa.Column('progress_auto', sa.Boolean(), server_default='0'),
        sa.Column('last_reminder_sent', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id']),
        sa.ForeignKeyConstraint(['department_id'], ['task_departments.id']),
    )

    op.create_table(
        'task_subtasks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('parent_task_id', sa.Integer(), nullable=False),
        sa.Column('subtask_title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.String(length=20), server_default='Medium'),
        sa.Column('status', sa.String(length=20), server_default='Pending'),
        sa.Column('progress', sa.Integer(), server_default='0'),
        sa.Column('is_completed', sa.Boolean(), server_default='0'),
        sa.Column('due_at', sa.String(length=50), nullable=True),
        sa.Column('reminder_days', sa.Integer(), server_default='0'),
        sa.Column('reminder_hours', sa.Integer(), server_default='0'),
        sa.Column('last_reminder_sent', sa.String(length=50), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['parent_task_id'], ['task_items.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'task_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('task_name', sa.String(length=255), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('field_name', sa.String(length=50), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
    )

    op.create_table(
        'task_transaction_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), server_default='#6366f1'),
        sa.Column('icon', sa.String(length=50), server_default='fa-money-bill'),
        sa.Column('is_system', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'task_transactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), server_default='0'),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('unit', sa.String(length=20), server_default='unit'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('transaction_date', sa.String(length=50), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['task_id'], ['task_items.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'task_report_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('report_name', sa.String(length=100), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('filters_applied', sa.Text(), nullable=True),
        sa.Column('snapshot_data', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
    )

    op.create_table(
        'task_user_permissions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_key', sa.String(length=100), nullable=False, unique=True),
        sa.Column('permission_value', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # ========================================================================
    # ISSUE TRACKER TABLES
    # ========================================================================

    op.create_table(
        'issue_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('row_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('issue_date', sa.String(length=50), nullable=False),
        sa.Column('issue_date_sort', sa.String(length=50), nullable=True),
        sa.Column('issue', sa.Text(), nullable=False),
        sa.Column('pareto_law', sa.Boolean(), server_default='0'),
        sa.Column('involved_departments', sa.Text(), nullable=True),
        sa.Column('section_team', sa.String(length=100), nullable=True),
        sa.Column('issue_type', sa.String(length=50), nullable=True),
        sa.Column('writer', sa.String(length=100), nullable=True),
        sa.Column('reported_by', sa.String(length=100), nullable=True),
        sa.Column('priority', sa.String(length=20), server_default='Medium'),
        sa.Column('status', sa.String(length=20), server_default='Open'),
        sa.Column('responsible_section', sa.String(length=100), nullable=True),
        sa.Column('responsible_person', sa.String(length=100), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('impact', sa.Text(), nullable=True),
        sa.Column('action_plan', sa.Text(), nullable=True),
        sa.Column('resources_needed', sa.Text(), nullable=True),
        sa.Column('target_resolution_date', sa.String(length=50), nullable=True),
        sa.Column('first_follow_up_date', sa.String(length=50), nullable=True),
        sa.Column('first_follow_up_notes', sa.Text(), nullable=True),
        sa.Column('second_follow_up_date', sa.String(length=50), nullable=True),
        sa.Column('second_follow_up_notes', sa.Text(), nullable=True),
        sa.Column('follow_up_by', sa.String(length=100), nullable=True),
        sa.Column('progress_note', sa.Text(), nullable=True),
        sa.Column('linked_issues', sa.Text(), nullable=True),
        sa.Column('final_status', sa.String(length=50), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id']),
    )

    op.create_table(
        'issue_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id']),
    )

    op.create_table(
        'issue_comments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'issue_attachments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'issue_watchers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('issue_id', 'user_id'),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'issue_escalations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('escalated_by', sa.Integer(), nullable=True),
        sa.Column('escalated_to', sa.Integer(), nullable=True),
        sa.Column('escalation_level', sa.Integer(), server_default='1'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['issue_id'], ['issue_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['escalated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['escalated_to'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_table(
        'issue_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('default_assignee', sa.String(length=100), nullable=True),
        sa.Column('default_priority', sa.String(length=20), server_default='Medium'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'issue_sla_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('response_hours', sa.Integer(), server_default='24'),
        sa.Column('resolution_hours', sa.Integer(), server_default='72'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'issue_workflow_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('from_status', sa.String(length=50), nullable=False),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requires_comment', sa.Boolean(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'user_issue_preferences',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('visible_columns', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # ========================================================================
    # USER PREFERENCES
    # ========================================================================

    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('theme', sa.String(length=20), server_default='dark'),
        sa.Column('font_family', sa.String(length=50), server_default='outfit'),
        sa.Column('font_size', sa.String(length=20), server_default='medium'),
        sa.Column('font_weight', sa.String(length=20), server_default='regular'),
        sa.Column('timezone', sa.String(length=50), server_default='Asia/Dubai'),
        sa.Column('date_format', sa.String(length=20), server_default='DD/MM/YYYY'),
        sa.Column('interface_direction', sa.String(length=10), server_default='auto'),
        sa.Column('currency', sa.String(length=10), server_default='AED'),
        sa.Column('density', sa.String(length=20), server_default='comfortable'),
        sa.Column('reduced_motion', sa.Boolean(), server_default='0'),
        sa.Column('show_seconds', sa.Boolean(), server_default='1'),
        sa.Column('sidebar_compact', sa.Boolean(), server_default='0'),
        sa.Column('language', sa.String(length=10), server_default='en'),
        sa.Column('nav_preferences', sa.Text(), server_default='{}'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'user_task_preferences',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('visible_columns', sa.Text(), nullable=True),
        sa.Column('task_list_columns', sa.Text(), server_default='type,title,parent,assigned,priority,status,progress,due'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # ========================================================================
    # GOOGLE WORKSPACE
    # ========================================================================

    op.create_table(
        'google_workspace_tokens',
        sa.Column('user_id', sa.Integer(), primary_key=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_type', sa.String(length=50), server_default='Bearer'),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.String(length=50), nullable=True),
        sa.Column('email_address', sa.String(length=150), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    op.create_table(
        'google_workspace_settings',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, server_default='1'),
        sa.Column('client_id', sa.String(length=255), nullable=True),
        sa.Column('client_secret', sa.String(length=255), nullable=True),
        sa.Column('redirect_uri', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # ========================================================================
    # PLATFORM TABLES (from database.py initialize_platform_schema)
    # ========================================================================

    op.create_table(
        'platform_audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('entity_type', sa.Text(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('field_name', sa.Text(), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_audit_entity', 'platform_audit_log', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_user', 'platform_audit_log', ['user_id', 'created_at'])
    op.create_index('idx_audit_action', 'platform_audit_log', ['action', 'created_at'])

    op.create_table(
        'platform_notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('notification_type', sa.String(length=20), server_default='INFO'),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(length=20), server_default='MEDIUM'),
        sa.Column('is_read', sa.Boolean(), server_default='0'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('link_url', sa.Text(), nullable=True),
        sa.Column('related_entity_type', sa.Text(), nullable=True),
        sa.Column('related_entity_id', sa.Integer(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_notif_user', 'platform_notifications', ['user_id', 'is_read'])
    op.create_index('idx_notif_role', 'platform_notifications', ['role_id', 'is_read'])
    op.create_index('idx_notif_created', 'platform_notifications', ['created_at'])

    op.create_table(
        'platform_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('setting_key', sa.Text(), nullable=False, unique=True),
        sa.Column('setting_value', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), server_default='GENERAL'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'user_profile_extensions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('first_name', sa.Text(), nullable=True),
        sa.Column('last_name', sa.Text(), nullable=True),
        sa.Column('display_name', sa.Text(), nullable=True),
        sa.Column('preferred_name', sa.Text(), nullable=True),
        sa.Column('date_of_birth', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.Text(), nullable=True),
        sa.Column('nationality', sa.Text(), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('headline', sa.Text(), nullable=True),
        sa.Column('spoken_languages', sa.Text(), nullable=True),
        sa.Column('timezone', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('secondary_email', sa.Text(), nullable=True),
        sa.Column('mobile', sa.Text(), nullable=True),
        sa.Column('secondary_mobile', sa.Text(), nullable=True),
        sa.Column('whatsapp', sa.Text(), nullable=True),
        sa.Column('phone_extension', sa.Text(), nullable=True),
        sa.Column('country', sa.Text(), nullable=True),
        sa.Column('city', sa.Text(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('emergency_contact_name', sa.Text(), nullable=True),
        sa.Column('emergency_contact_phone', sa.Text(), nullable=True),
        sa.Column('emergency_contact_relation', sa.Text(), nullable=True),
        sa.Column('preferred_communication', sa.Text(), nullable=True),
        sa.Column('department', sa.Text(), nullable=True),
        sa.Column('position', sa.Text(), nullable=True),
        sa.Column('job_title', sa.Text(), nullable=True),
        sa.Column('employee_code', sa.Text(), nullable=True),
        sa.Column('work_email', sa.Text(), nullable=True),
        sa.Column('work_phone', sa.Text(), nullable=True),
        sa.Column('hire_date', sa.String(length=50), nullable=True),
        sa.Column('termination_date', sa.String(length=50), nullable=True),
        sa.Column('reporting_to', sa.Text(), nullable=True),
        sa.Column('team', sa.Text(), nullable=True),
        sa.Column('territory', sa.Text(), nullable=True),
        sa.Column('work_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_profile_user', 'user_profile_extensions', ['user_id'])

    op.create_table(
        'user_notification_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('inapp_tasks', sa.Text(), server_default='1'),
        sa.Column('inapp_approvals', sa.Text(), server_default='1'),
        sa.Column('inapp_deliveries', sa.Text(), server_default='1'),
        sa.Column('inapp_stock', sa.Text(), server_default='1'),
        sa.Column('inapp_sales', sa.Text(), server_default='1'),
        sa.Column('inapp_hr', sa.Text(), server_default='1'),
        sa.Column('inapp_system', sa.Text(), server_default='1'),
        sa.Column('email_tasks', sa.Text(), server_default='0'),
        sa.Column('email_approvals', sa.Text(), server_default='0'),
        sa.Column('email_deliveries', sa.Text(), server_default='0'),
        sa.Column('email_stock', sa.Text(), server_default='0'),
        sa.Column('email_sales', sa.Text(), server_default='0'),
        sa.Column('email_digest', sa.Text(), server_default='0'),
        sa.Column('daily_summary', sa.Text(), server_default='0'),
        sa.Column('weekly_summary', sa.Text(), server_default='0'),
        sa.Column('urgent_only', sa.Text(), server_default='0'),
        sa.Column('sound_enabled', sa.Text(), server_default='1'),
        sa.Column('quiet_hours_enabled', sa.Text(), server_default='0'),
        sa.Column('quiet_hours_start', sa.Text(), server_default='22:00'),
        sa.Column('quiet_hours_end', sa.Text(), server_default='08:00'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_notif_prefs_user', 'user_notification_preferences', ['user_id'])

    op.create_table(
        'user_privacy_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('profile_visibility', sa.Text(), server_default='internal'),
        sa.Column('show_email', sa.Text(), server_default='0'),
        sa.Column('show_phone', sa.Text(), server_default='0'),
        sa.Column('show_mobile', sa.Text(), server_default='0'),
        sa.Column('show_department', sa.Text(), server_default='1'),
        sa.Column('show_role', sa.Text(), server_default='1'),
        sa.Column('show_last_login', sa.Text(), server_default='0'),
        sa.Column('allow_directory_search', sa.Text(), server_default='1'),
        sa.Column('show_activity_status', sa.Text(), server_default='1'),
        sa.Column('show_online_indicator', sa.Text(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_privacy_user', 'user_privacy_settings', ['user_id'])

    op.create_table(
        'user_linked_accounts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('provider_user_id', sa.Text(), nullable=True),
        sa.Column('provider_email', sa.Text(), nullable=True),
        sa.Column('access_token_encrypted', sa.Text(), nullable=True),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Text(), server_default='1'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('user_id', 'provider'),
    )
    op.create_index('idx_linked_user', 'user_linked_accounts', ['user_id'])

    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_info', sa.Text(), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('is_current', sa.Boolean(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('last_activity', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_sessions_user', 'user_sessions', ['user_id'])
    op.create_index('idx_sessions_token', 'user_sessions', ['session_token'])


def downgrade() -> None:
    """Downgrade removes all tables. Use with caution on production."""
    op.drop_table('user_sessions')
    op.drop_table('user_linked_accounts')
    op.drop_table('user_privacy_settings')
    op.drop_table('user_notification_preferences')
    op.drop_table('user_profile_extensions')
    op.drop_table('platform_settings')
    op.drop_table('platform_notifications')
    op.drop_table('platform_audit_log')
    op.drop_table('google_workspace_settings')
    op.drop_table('google_workspace_tokens')
    op.drop_table('user_task_preferences')
    op.drop_table('user_preferences')
    op.drop_table('user_issue_preferences')
    op.drop_table('issue_workflow_rules')
    op.drop_table('issue_sla_rules')
    op.drop_table('issue_categories')
    op.drop_table('issue_escalations')
    op.drop_table('issue_watchers')
    op.drop_table('issue_attachments')
    op.drop_table('issue_comments')
    op.drop_table('issue_history')
    op.drop_table('issue_items')
    op.drop_table('task_user_permissions')
    op.drop_table('task_report_snapshots')
    op.drop_table('task_transactions')
    op.drop_table('task_transaction_categories')
    op.drop_table('task_history')
    op.drop_table('task_subtasks')
    op.drop_table('task_items')
    op.drop_table('task_departments')
    op.drop_table('suppliers')
    op.drop_table('warehouses')
    op.drop_table('vehicles')
    op.drop_table('delivery_activity_logs')
    op.drop_table('delivery_stops')
    op.drop_table('delivery_trips')
    op.drop_table('delivery_activities')
    op.drop_table('customer_transactions')
    op.drop_table('customers')
    op.drop_table('movements')
    op.drop_table('inventory')
    op.drop_table('parts')
    op.drop_table('statuses')
    op.drop_table('brands')
    op.drop_table('categories')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('companies')
