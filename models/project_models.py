"""
Project Management Module Database Models
==========================================
This file contains all Project Management-related database table definitions.

Tables:
- project_types: Project type definitions
- project_categories: Project category definitions
- projects: Project master data
- project_phases: Project phases
- project_wbs: Work Breakdown Structure nodes
- project_tasks: Project tasks
- project_task_dependencies: Task dependencies
- project_task_checklists: Task subtasks/checklists
- project_task_comments: Task comments
- project_task_attachments: Task attachments
- project_milestones: Project milestones
- project_resource_allocations: Resource allocations
- project_issues: Project issues/blockers
- project_documents: Project documents
- project_status_updates: Status update history
- project_settings: Project configuration settings
- project_audit_logs: Audit trail
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# PROJECT TABLE DEFINITIONS
# =============================================================================

PROJECT_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Project Types
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        code TEXT UNIQUE,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 2. Project Categories
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        code TEXT UNIQUE,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 3. Projects - Master Data
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_code TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        project_type_id INTEGER,
        category_id INTEGER,
        description TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        department_id INTEGER,
        owner_user_id INTEGER,
        manager_user_id INTEGER,
        sponsor_user_id INTEGER,
        planned_start_date DATE,
        planned_end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        target_completion_date DATE,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Draft',
        progress INTEGER DEFAULT 0,
        baseline_start_date DATE,
        baseline_end_date DATE,
        cost_center TEXT,
        budget_code TEXT,
        customer_id INTEGER,
        vendor_id INTEGER,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        archived_at DATETIME,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_type_id) REFERENCES project_types(id) ON DELETE SET NULL,
        FOREIGN KEY (category_id) REFERENCES project_categories(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (manager_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (sponsor_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Project Phases
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_phases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        phase_name TEXT NOT NULL,
        phase_order INTEGER DEFAULT 0,
        description TEXT,
        planned_start_date DATE,
        planned_end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        status TEXT DEFAULT 'Pending',
        progress INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 5. Project WBS Nodes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_wbs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        parent_wbs_id INTEGER,
        wbs_code TEXT NOT NULL,
        wbs_name TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_wbs_id) REFERENCES project_wbs(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 6. Project Tasks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        phase_id INTEGER,
        wbs_id INTEGER,
        parent_task_id INTEGER,
        task_code TEXT UNIQUE,
        task_name TEXT NOT NULL,
        description TEXT,
        task_type_id INTEGER,
        category TEXT,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Draft',
        owner_user_id INTEGER,
        assigned_user_id INTEGER,
        assigned_team_id INTEGER,
        reviewer_user_id INTEGER,
        planned_start_date DATE,
        planned_end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        duration_days INTEGER DEFAULT 0,
        estimated_hours DECIMAL(8,2) DEFAULT 0,
        actual_hours DECIMAL(8,2) DEFAULT 0,
        progress INTEGER DEFAULT 0,
        is_blocked INTEGER DEFAULT 0,
        blocked_reason TEXT,
        delay_flag INTEGER DEFAULT 0,
        milestone_id INTEGER,
        deliverable TEXT,
        completion_notes TEXT,
        closure_verified INTEGER DEFAULT 0,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (phase_id) REFERENCES project_phases(id) ON DELETE SET NULL,
        FOREIGN KEY (wbs_id) REFERENCES project_wbs(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (reviewer_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (milestone_id) REFERENCES project_milestones(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 7. Task Dependencies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_task_dependencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        predecessor_task_id INTEGER NOT NULL,
        successor_task_id INTEGER NOT NULL,
        dependency_type TEXT DEFAULT 'FS',
        lag_days INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (predecessor_task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (successor_task_id) REFERENCES project_tasks(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. Task Checklists (Subtasks)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_task_checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_task_id INTEGER NOT NULL,
        checklist_title TEXT NOT NULL,
        description TEXT,
        assigned_user_id INTEGER,
        status TEXT DEFAULT 'Pending',
        progress INTEGER DEFAULT 0,
        due_date DATE,
        completed_at DATETIME,
        sort_order INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Task Comments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_task_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comment TEXT NOT NULL,
        is_internal INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 10. Task Attachments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_task_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 11. Project Milestones
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        milestone_code TEXT,
        milestone_name TEXT NOT NULL,
        milestone_type TEXT,
        owner_user_id INTEGER,
        planned_date DATE,
        target_date DATE,
        actual_completion_date DATE,
        status TEXT DEFAULT 'Pending',
        related_task_ids TEXT,
        progress_contribution INTEGER DEFAULT 0,
        approval_required INTEGER DEFAULT 0,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        is_overdue INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Resource Allocations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_resource_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        task_id INTEGER,
        resource_type TEXT NOT NULL,
        resource_id INTEGER NOT NULL,
        role_on_project TEXT,
        allocation_percentage DECIMAL(5,2) DEFAULT 100,
        planned_hours DECIMAL(8,2) DEFAULT 0,
        actual_hours DECIMAL(8,2) DEFAULT 0,
        planned_start_date DATE,
        planned_end_date DATE,
        allocation_status TEXT DEFAULT 'Allocated',
        availability_status TEXT DEFAULT 'Available',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Project Issues / Blockers
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        task_id INTEGER,
        issue_number TEXT UNIQUE,
        issue_title TEXT NOT NULL,
        category TEXT,
        severity TEXT DEFAULT 'Medium',
        impact TEXT,
        owner_user_id INTEGER,
        reported_by_user_id INTEGER,
        reported_date DATE,
        due_date DATE,
        is_blocker INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Open',
        root_cause TEXT,
        mitigation_plan TEXT,
        escalation_level TEXT,
        resolution_date DATE,
        closure_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE SET NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (reported_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 14. Project Documents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        document_type TEXT,
        title TEXT NOT NULL,
        description TEXT,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        version TEXT DEFAULT '1.0',
        is_latest INTEGER DEFAULT 1,
        uploaded_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 15. Project Status Updates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_status_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        progress_change INTEGER DEFAULT 0,
        update_note TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 16. Project Settings / Configuration
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'string',
        category TEXT,
        description TEXT,
        is_system INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 17. Project Audit Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        task_id INTEGER,
        action_type TEXT NOT NULL,
        field_changed TEXT,
        old_value TEXT,
        new_value TEXT,
        actor_user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE SET NULL,
        FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 18. Project Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT NOT NULL,
        description TEXT,
        project_type_id INTEGER,
        created_by_user_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_type_id) REFERENCES project_types(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 19. Template Phases (for cloning)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_template_phases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        phase_name TEXT NOT NULL,
        phase_order INTEGER DEFAULT 0,
        duration_days INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 20. Template Tasks (for cloning)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_template_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        phase_order INTEGER DEFAULT 0,
        task_name TEXT NOT NULL,
        description TEXT,
        task_type TEXT,
        default_priority TEXT DEFAULT 'Medium',
        default_duration_days INTEGER DEFAULT 1,
        is_milestone INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES project_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 21. Approval Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS project_approval_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        task_id INTEGER,
        approval_type TEXT NOT NULL,
        requester_user_id INTEGER NOT NULL,
        approver_user_id INTEGER,
        status TEXT DEFAULT 'Pending',
        remarks TEXT,
        rejection_reason TEXT,
        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        decided_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE SET NULL,
        FOREIGN KEY (requester_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approver_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",
]


# =============================================================================
# TABLE INITIALIZATION
# =============================================================================

def init_project_tables():
    """Initialize all project management tables."""
    conn = get_db()
    try:
        for table_sql in PROJECT_TABLES:
            conn.execute(table_sql)
        conn.commit()
        _seed_default_data(conn)
    finally:
        conn.close()


def _seed_default_data(conn):
    """Seed default project types, categories, and settings."""
    # Default project types
    default_types = [
        ('Construction', 'Construction and infrastructure projects'),
        ('Software Development', 'Software and IT development projects'),
        ('Research', 'Research and development projects'),
        ('Marketing', 'Marketing and campaign projects'),
        ('Operations', 'Operational improvement projects'),
        ('Training', 'Training and development projects'),
        ('Event', 'Event management projects'),
        ('Consulting', 'Consulting and advisory projects'),
    ]
    for name, desc in default_types:
        code = name.lower().replace(' ', '_')[:20]
        conn.execute(
            "INSERT OR IGNORE INTO project_types (name, description, code) VALUES (?, ?, ?)",
            (name, desc, code)
        )

    # Default project categories
    default_categories = [
        ('Internal', 'Internal company projects'),
        ('External', 'Client-facing projects'),
        ('Regulatory', 'Compliance and regulatory projects'),
        ('Strategic', 'Strategic initiative projects'),
        ('Maintenance', 'Ongoing maintenance projects'),
        ('Emergency', 'Emergency response projects'),
    ]
    for name, desc in default_categories:
        code = name.lower()[:20]
        conn.execute(
            "INSERT OR IGNORE INTO project_categories (name, description, code) VALUES (?, ?, ?)",
            (name, desc, code)
        )

    # Default settings
    default_settings = [
        ('project_number_prefix', 'PRJ', 'string', 'Numbering'),
        ('project_number_sequence', '1', 'int', 'Numbering'),
        ('task_number_prefix', 'TSK', 'string', 'Numbering'),
        ('task_number_sequence', '1', 'int', 'Numbering'),
        ('milestone_number_prefix', 'MS', 'string', 'Numbering'),
        ('default_priority', 'Medium', 'string', 'Tasks'),
        ('auto_close_completed_tasks', '0', 'bool', 'Tasks'),
        ('enable_baseline_tracking', '1', 'bool', 'Planning'),
        ('enable_approval_workflow', '1', 'bool', 'Approvals'),
        ('require_milestone_approval', '0', 'bool', 'Approvals'),
    ]
    for key, value, stype, category in default_settings:
        conn.execute(
            """INSERT OR IGNORE INTO project_settings 
               (setting_key, setting_value, setting_type, category) VALUES (?, ?, ?, ?)""",
            (key, value, stype, category)
        )

    conn.commit()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_project_count(db, company_id=None, status=None):
    """Get count of projects with optional filters."""
    sql = "SELECT COUNT(*) as cnt FROM projects WHERE 1=1"
    params = []
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if status:
        sql += " AND status = ?"
        params.append(status)
    result = db.execute(sql, params).fetchone()
    return result['cnt'] if result else 0


def get_active_projects(db, company_id=None, limit=50):
    """Get active projects."""
    sql = """
        SELECT p.*, pt.name as type_name, u1.username as manager_name,
               c.name as company_name
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN users u1 ON p.manager_user_id = u1.id
        LEFT JOIN companies c ON p.company_id = c.id
        WHERE p.is_archived = 0 AND p.status NOT IN ('Completed', 'Cancelled', 'Archived')
    """
    params = []
    if company_id:
        sql += " AND p.company_id = ?"
        params.append(company_id)
    sql += " ORDER BY p.priority DESC, p.planned_end_date ASC LIMIT ?"
    params.append(limit)
    return [dict(row) for row in db.execute(sql, params).fetchall()]


def get_project_stats(db, company_id=None):
    """Get project statistics."""
    base_sql = "FROM projects p WHERE p.is_archived = 0"
    params = []
    if company_id:
        base_sql += " AND p.company_id = ?"
        params.append(company_id)

    stats = {}
    
    # Total projects
    result = db.execute(f"SELECT COUNT(*) as cnt {base_sql}", params).fetchone()
    stats['total'] = result['cnt'] if result else 0
    
    # By status
    status_breakdown = [dict(row) for row in db.execute(
        f"""SELECT COALESCE(p.status, 'Draft') as status, COUNT(*) as cnt 
            {base_sql} GROUP BY p.status ORDER BY cnt DESC""", 
        params
    ).fetchall()]
    stats['by_status'] = status_breakdown
    
    # By priority
    priority_breakdown = [dict(row) for row in db.execute(
        f"""SELECT COALESCE(p.priority, 'Medium') as priority, COUNT(*) as cnt 
            {base_sql} GROUP BY p.priority ORDER BY cnt DESC""", 
        params
    ).fetchall()]
    stats['by_priority'] = priority_breakdown
    
    # Delayed projects
    result = db.execute(
        f"""SELECT COUNT(*) as cnt {base_sql} 
            AND p.status NOT IN ('Completed', 'Cancelled') 
            AND p.planned_end_date < date('now')""", 
        params
    ).fetchone()
    stats['delayed'] = result['cnt'] if result else 0
    
    # Upcoming milestones
    result = db.execute(
        """SELECT COUNT(*) as cnt FROM project_milestones pm
           JOIN projects p ON pm.project_id = p.id
           WHERE pm.is_overdue = 0 AND pm.status = 'Pending'
           AND pm.planned_date BETWEEN date('now') AND date('now', '+7 days')"""
    ).fetchone()
    stats['upcoming_milestones'] = result['cnt'] if result else 0
    
    # Overdue milestones
    result = db.execute(
        """SELECT COUNT(*) as cnt FROM project_milestones pm
           WHERE pm.is_overdue = 1 AND pm.status != 'Completed'"""
    ).fetchone()
    stats['overdue_milestones'] = result['cnt'] if result else 0
    
    # Active issues
    result = db.execute(
        """SELECT COUNT(*) as cnt FROM project_issues
           WHERE is_blocker = 1 AND status NOT IN ('Resolved', 'Closed')"""
    ).fetchone()
    stats['active_blockers'] = result['cnt'] if result else 0
    
    return stats


def get_project_with_details(db, project_id):
    """Get project with all related details."""
    project = db.execute("""
        SELECT p.*, pt.name as type_name, pc.name as category_name,
               c.name as company_name, b.name as branch_name,
               d.name as department_name,
               u1.username as owner_name, u2.username as manager_name,
               u3.username as sponsor_name,
               creator.username as created_by_name,
               approver.username as approved_by_name
        FROM projects p
        LEFT JOIN project_types pt ON p.project_type_id = pt.id
        LEFT JOIN project_categories pc ON p.category_id = pc.id
        LEFT JOIN companies c ON p.company_id = c.id
        LEFT JOIN branches b ON p.branch_id = b.id
        LEFT JOIN hr_departments d ON p.department_id = d.id
        LEFT JOIN users u1 ON p.owner_user_id = u1.id
        LEFT JOIN users u2 ON p.manager_user_id = u2.id
        LEFT JOIN users u3 ON p.sponsor_user_id = u3.id
        LEFT JOIN users creator ON p.created_by_user_id = creator.id
        LEFT JOIN users approver ON p.approved_by_user_id = approver.id
        WHERE p.id = ?
    """, (project_id,)).fetchone()
    
    if not project:
        return None
    
    result = dict(project)
    
    # Get phases
    result['phases'] = [dict(row) for row in db.execute("""
        SELECT * FROM project_phases WHERE project_id = ? ORDER BY phase_order
    """, (project_id,)).fetchall()]
    
    # Get tasks
    result['tasks'] = [dict(row) for row in db.execute("""
        SELECT t.*, u.username as assigned_name,
               (SELECT COUNT(*) FROM project_task_checklists WHERE parent_task_id = t.id) as subtask_count
        FROM project_tasks t
        LEFT JOIN users u ON t.assigned_user_id = u.id
        WHERE t.project_id = ? AND t.is_archived = 0
        ORDER BY t.planned_start_date
    """, (project_id,)).fetchall()]
    
    # Get milestones
    result['milestones'] = [dict(row) for row in db.execute("""
        SELECT * FROM project_milestones WHERE project_id = ? ORDER BY planned_date
    """, (project_id,)).fetchall()]
    
    # Get resource allocations
    result['resources'] = [dict(row) for row in db.execute("""
        SELECT pra.*, u.username as resource_name
        FROM project_resource_allocations pra
        LEFT JOIN users u ON pra.resource_type = 'user' AND pra.resource_id = u.id
        WHERE pra.project_id = ?
    """, (project_id,)).fetchall()]
    
    # Get issues
    result['issues'] = [dict(row) for row in db.execute("""
        SELECT * FROM project_issues WHERE project_id = ? ORDER BY created_at DESC
    """, (project_id,)).fetchall()]
    
    return result


def get_user_workload(db, user_id, start_date=None, end_date=None):
    """Get workload for a specific user across projects."""
    sql = """
        SELECT p.project_name, p.project_code, t.task_name, t.planned_start_date,
               t.planned_end_date, t.progress, pra.allocation_percentage
        FROM project_tasks t
        JOIN projects p ON t.project_id = p.id
        JOIN project_resource_allocations pra ON pra.task_id = t.id
        WHERE pra.resource_type = 'user' AND pra.resource_id = ?
        AND t.is_archived = 0 AND t.status NOT IN ('Completed', 'Cancelled')
    """
    params = [user_id]
    
    if start_date:
        sql += " AND t.planned_end_date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND t.planned_start_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY t.planned_start_date"
    
    return [dict(row) for row in db.execute(sql, params).fetchall()]


def calculate_project_progress(db, project_id):
    """Calculate project progress based on task progress."""
    tasks = db.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
               AVG(COALESCE(progress, 0)) as avg_progress
        FROM project_tasks 
        WHERE project_id = ? AND is_archived = 0
    """, (project_id,)).fetchone()
    
    if not tasks or tasks['total'] == 0:
        return 0
    
    if tasks['completed'] == tasks['total']:
        return 100
    
    return int(tasks['avg_progress']) if tasks['avg_progress'] else 0


def log_project_audit(db, project_id, task_id, action_type, field_changed=None,
                      old_value=None, new_value=None, actor_user_id=None,
                      ip_address=None, user_agent=None):
    """Log a project audit entry."""
    db.execute("""
        INSERT INTO project_audit_logs 
        (project_id, task_id, action_type, field_changed, old_value, new_value,
         actor_user_id, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, task_id, action_type, field_changed, old_value, new_value,
          actor_user_id, ip_address, user_agent))
    db.commit()
