"""
Talent Management Module Database Models and Migrations
=========================================================
This file contains all Talent Management-related database table definitions and migration functions.
Tables are designed to be added to the existing SQLite database without conflicts.

Talent Management Tables:
- tm_competency_categories: Skill categories
- tm_competencies: Competency/Skill library
- tm_employee_competencies: Employee skill assessments
- tm_talent_profiles: Extended talent data
- tm_talent_pools: Talent pool definitions
- tm_talent_pool_members: Pool memberships
- tm_critical_roles: Critical position tracking
- tm_succession_plans: Succession planning
- tm_career_paths: Career path definitions
- tm_development_plans: Individual Development Plans (IDP)
- tm_development_goals: Development goals
- tm_development_actions: IDP action items
- tm_talent_reviews: Talent review cycles
- tm_talent_review_participants: Review participants
- tm_talent_notes: Talent annotations
- tm_talent_history: Talent audit trail
- tm_mentoring_assignments: Mentoring relationships
- tm_mobility_requests: Internal mobility requests
- tm_talent_settings: Configuration
- tm_talent_audit_logs: Audit trail
- tm_talent_engagement_signals: Employee experience signals
- tm_talent_approvals: Approval workflow records
- tm_talent_notifications: Notification records
"""

import sqlite3
import os
import json
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


TALENT_TABLES = [
    """CREATE TABLE IF NOT EXISTS tm_competency_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        name_ru TEXT,
        name_hi TEXT,
        name_es TEXT,
        name_zh TEXT,
        name_de TEXT,
        description TEXT,
        parent_id INTEGER,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES tm_competency_categories(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_competencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        name_ru TEXT,
        name_hi TEXT,
        name_es TEXT,
        name_zh TEXT,
        name_de TEXT,
        category_id INTEGER,
        description TEXT,
        description_ar TEXT,
        description_fa TEXT,
        proficiency_levels TEXT,
        is_technical INTEGER DEFAULT 0,
        is_leadership INTEGER DEFAULT 0,
        is_core INTEGER DEFAULT 0,
        weight_factor DECIMAL(3,2) DEFAULT 1.0,
        assessment_method TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES tm_competency_categories(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_employee_competencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        competency_id INTEGER NOT NULL,
        proficiency_level INTEGER DEFAULT 1,
        proficiency_name TEXT,
        required_level INTEGER DEFAULT 3,
        gap_score INTEGER DEFAULT 0,
        assessed_by INTEGER,
        assessment_date DATE,
        expiry_date DATE,
        evidence TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (competency_id) REFERENCES tm_competencies(id) ON DELETE CASCADE,
        FOREIGN KEY (assessed_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL UNIQUE,
        potential_rating TEXT,
        potential_score INTEGER,
        readiness_level TEXT,
        readiness_score INTEGER,
        readiness_horizon TEXT,
        performance_rating TEXT,
        performance_score INTEGER,
        performance_trend TEXT,
        risk_level TEXT,
        flight_risk INTEGER DEFAULT 0,
        career_interests TEXT,
        mobility_preference TEXT,
        mobility_ready INTEGER DEFAULT 0,
        mobility_target_date DATE,
        last_reviewed DATE,
        last_promotion_date DATE,
        tenure_years DECIMAL(4,1),
        emp_segment TEXT,
        talent_flags TEXT,
        development_priority INTEGER DEFAULT 3,
        succession_candidate INTEGER DEFAULT 0,
        hi_po INTEGER DEFAULT 0,
        notes TEXT,
        profile_completeness INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_pools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        name_ru TEXT,
        name_hi TEXT,
        name_es TEXT,
        name_zh TEXT,
        name_de TEXT,
        pool_type TEXT NOT NULL,
        description TEXT,
        criteria_json TEXT,
        owner_id INTEGER,
        color_code TEXT DEFAULT '#6366f1',
        icon_class TEXT DEFAULT 'fa-users',
        min_members INTEGER DEFAULT 0,
        max_members INTEGER,
        is_active INTEGER DEFAULT 1,
        allow_self_nomination INTEGER DEFAULT 1,
        requires_approval INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_pool_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pool_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        joined_date DATE,
        exit_date DATE,
        reason TEXT,
        nominated_by INTEGER,
        approved_by INTEGER,
        status TEXT DEFAULT 'Active',
        membership_type TEXT DEFAULT 'Manual',
        performance_baseline TEXT,
        potential_baseline TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pool_id) REFERENCES tm_talent_pools(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (nominated_by) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_critical_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id INTEGER NOT NULL,
        department_id INTEGER,
        role_type TEXT DEFAULT 'Critical',
        criticality_level TEXT DEFAULT 'High',
        risk_factors TEXT,
        backup_required INTEGER DEFAULT 1,
        backup_status TEXT,
        last_reviewed DATE,
        next_review DATE,
        succession_strategy TEXT,
        emergency_ready INTEGER DEFAULT 0,
        bench_strength_score INTEGER,
        incumbent_id INTEGER,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (position_id) REFERENCES hr_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (incumbent_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_succession_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        critical_role_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        successor_id INTEGER,
        deputy_id INTEGER,
        relationship_type TEXT DEFAULT 'Primary',
        readiness_level TEXT,
        readiness_score INTEGER,
        readiness_horizon TEXT,
        development_needs TEXT,
        development_progress INTEGER DEFAULT 0,
        timeline_months INTEGER,
        handover_planned INTEGER DEFAULT 0,
        handover_date DATE,
        risk_of_vacancy TEXT DEFAULT 'Medium',
        contingency_notes TEXT,
        approved_by INTEGER,
        approved_at DATE,
        status TEXT DEFAULT 'Draft',
        effective_from DATE,
        effective_to DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (critical_role_id) REFERENCES tm_critical_roles(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (successor_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (deputy_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_career_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        path_type TEXT NOT NULL,
        from_position_id INTEGER,
        to_position_id INTEGER NOT NULL,
        sequence_order INTEGER DEFAULT 0,
        avg_duration_months INTEGER,
        is_approved INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        requirements_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_position_id) REFERENCES hr_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (to_position_id) REFERENCES hr_positions(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_development_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        plan_year INTEGER NOT NULL,
        plan_title TEXT,
        manager_id INTEGER,
        status TEXT DEFAULT 'Draft',
        priority_level TEXT DEFAULT 'Medium',
        start_date DATE,
        end_date DATE,
        completion_percentage INTEGER DEFAULT 0,
        total_goals INTEGER DEFAULT 0,
        completed_goals INTEGER DEFAULT 0,
        approved_by INTEGER,
        approved_at DATE,
        submitted_at DATE,
        last_reviewed DATE,
        next_review_date DATE,
        budget_allocated DECIMAL(10,2) DEFAULT 0,
        budget_used DECIMAL(10,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (manager_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_development_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        goal_title TEXT NOT NULL,
        goal_description TEXT,
        goal_type TEXT DEFAULT 'Development',
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Not Started',
        target_date DATE,
        completed_at DATE,
        competency_focus TEXT,
        proficiency_target INTEGER,
        proficiency_current INTEGER,
        weight_percentage INTEGER DEFAULT 10,
        linked_objectives TEXT,
        obstacles TEXT,
        support_needed TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plan_id) REFERENCES tm_development_plans(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_development_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_id INTEGER NOT NULL,
        action_title TEXT NOT NULL,
        action_type TEXT,
        description TEXT,
        due_date DATE,
        status TEXT DEFAULT 'Pending',
        completed_at DATE,
        completed_by INTEGER,
        linked_learning_id INTEGER,
        linked_learning_title TEXT,
        mentor_id INTEGER,
        stretch_assignment INTEGER DEFAULT 0,
        resources_required TEXT,
        cost_estimate DECIMAL(8,2) DEFAULT 0,
        actual_cost DECIMAL(8,2) DEFAULT 0,
        progress_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (goal_id) REFERENCES tm_development_goals(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_learning_id) REFERENCES hr_training_programs(id) ON DELETE SET NULL,
        FOREIGN KEY (mentor_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (completed_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle_name TEXT NOT NULL,
        period_start DATE,
        period_end DATE,
        status TEXT DEFAULT 'Planning',
        review_type TEXT DEFAULT 'Annual',
        calibration_date DATE,
        approval_deadline DATE,
        participants_count INTEGER DEFAULT 0,
        completed_count INTEGER DEFAULT 0,
        department_filter TEXT,
        created_by INTEGER,
        approved_by INTEGER,
        approved_at DATE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_review_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        manager_id INTEGER,
        potential_rating TEXT,
        performance_rating TEXT,
        readiness_rating TEXT,
        manager_input TEXT,
        hr_input TEXT,
        final_rating TEXT,
        final_rating_value INTEGER,
        talent_segment TEXT,
        recommended_actions TEXT,
        promotion_ready INTEGER DEFAULT 0,
        retention_risk TEXT,
        succession_candidate INTEGER DEFAULT 0,
        development_focus TEXT,
        review_notes TEXT,
        is_calibrated INTEGER DEFAULT 0,
        calibrated_by INTEGER,
        calibrated_at DATE,
        status TEXT DEFAULT 'Pending',
        submitted_at DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (review_id) REFERENCES tm_talent_reviews(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (manager_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (calibrated_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        note_type TEXT NOT NULL,
        content TEXT NOT NULL,
        is_private INTEGER DEFAULT 0,
        is_flagged INTEGER DEFAULT 0,
        flag_reason TEXT,
        related_review_id INTEGER,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (related_review_id) REFERENCES tm_talent_reviews(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        field_name TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        change_reason TEXT,
        changed_by INTEGER NOT NULL,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        entity_type TEXT,
        entity_id INTEGER,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (changed_by) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_mentoring_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mentor_id INTEGER NOT NULL,
        mentee_id INTEGER NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        status TEXT DEFAULT 'Active',
        objectives TEXT,
        focus_areas TEXT,
        sessions_planned INTEGER DEFAULT 0,
        sessions_completed INTEGER DEFAULT 0,
        next_session DATE,
        last_session DATE,
        outcome TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mentor_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (mentee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_mobility_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        from_position_id INTEGER,
        from_department_id INTEGER,
        to_position_id INTEGER NOT NULL,
        to_department_id INTEGER,
        request_type TEXT NOT NULL,
        motivation TEXT,
        relevant_experience TEXT,
        expected_start_date DATE,
        actual_start_date DATE,
        status TEXT DEFAULT 'Pending',
        approved_by INTEGER,
        approved_at DATE,
        rejection_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (from_position_id) REFERENCES hr_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (from_department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (to_position_id) REFERENCES hr_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (to_department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'String',
        category TEXT,
        description TEXT,
        is_editable INTEGER DEFAULT 1,
        updated_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        change_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_engagement_signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        signal_type TEXT NOT NULL,
        source TEXT,
        signal_value INTEGER,
        sentiment_score DECIMAL(3,2),
        themes TEXT,
        recorded_at DATE,
        review_period TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_type TEXT NOT NULL,
        reference_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        approver_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        sequence_order INTEGER DEFAULT 1,
        comments TEXT,
        decision_at DATE,
        delegation_from INTEGER,
        sla_due_date DATE,
        sla_breached INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approver_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (delegation_from) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    """CREATE TABLE IF NOT EXISTS tm_talent_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_id INTEGER NOT NULL,
        notification_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT,
        link_url TEXT,
        priority TEXT DEFAULT 'Normal',
        is_read INTEGER DEFAULT 0,
        read_at DATE,
        expires_at DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipient_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",
]


def run_talent_migrations():
    """Run all Talent Management table migrations."""
    conn = get_db()
    try:
        for table_sql in TALENT_TABLES:
            conn.executescript(table_sql)
        conn.commit()
        seed_talent_defaults(conn)
        return True, "Talent Management migrations completed successfully"
    except Exception as e:
        conn.rollback()
        return False, f"Talent Management migration error: {str(e)}"
    finally:
        conn.close()


def seed_talent_defaults(conn):
    """Seed default Talent Management data."""
    categories = [
        ('Leadership', 'القيادة', 'رهبری', 'Leadership', 'नेतृत्व', 'Liderazgo', '领导力', 'Führung', 1, 1),
        ('Technical Skills', 'المهارات التقنية', 'مهارت‌های فنی', 'Technical Skills', 'तकनीकी कौशल', 'Habilidades Técnicas', '技术技能', 'Technische Fähigkeiten', 2, 2),
        ('Business Acumen', 'الفهم التجاري', 'درک کسب‌وکار', 'Business Acumen', 'व्यापारिक समझ', 'Visión de Negocio', '商业洞察', 'Geschäftssinn', 3, 3),
        ('Communication', 'التواصل', 'ارتباطات', 'Communication', 'संचार', 'Comunicación', '沟通', 'Kommunikation', 4, 4),
        ('Problem Solving', 'حل المشكلات', 'حل مسئله', 'Problem Solving', 'समस्या समाधान', 'Resolución de Problemas', '问题解决', 'Problemlösung', 5, 5),
        ('Teamwork', 'العمل الجماعي', 'کار تیمی', 'Teamwork', 'टीम वर्क', 'Trabajo en Equipo', '团队协作', 'Teamarbeit', 6, 6),
        ('Innovation', 'الابتكار', 'نوآوری', 'Innovation', 'नवाचार', 'Innovación', '创新', 'Innovation', 7, 7),
        ('Customer Focus', 'التركيز على العميل', 'تمرکز بر مشتری', 'Customer Focus', 'ग्राहक केंद्रित', 'Enfoque al Cliente', '客户导向', 'Kundenfokus', 8, 8),
    ]
    for cat in categories:
        conn.execute("""
            INSERT OR IGNORE INTO tm_competency_categories 
            (name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, sort_order, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, cat)

    competencies = [
        ('Strategic Thinking', 'التفكير الاستراتيجي', 'تفکر استراتژیک', 'Strategic Thinking', 'रणनीतिक सोच', 'Pensamiento Estratégico', '战略思维', 'Strategisches Denken', 1, 'Strategic ability to see the big picture', 1, 1, 1, 1.5, 'Assessment Center', 1),
        ('Team Leadership', 'قيادة الفريق', 'رهبری تیم', 'Team Leadership', 'टीम लीडरशिप', 'Liderazgo de Equipo', '团队领导', 'Teamführung', 1, 'Ability to lead and inspire teams', 1, 1, 1, 1.3, '360 Feedback', 1),
        ('Decision Making', 'اتخاذ القرارات', 'تصمیم‌گیری', 'Decision Making', 'निर्णय लेना', 'Toma de Decisiones', '决策能力', 'Entscheidungsfindung', 1, 'Ability to make effective decisions', 1, 1, 0, 1.2, 'Case Study', 1),
        ('Data Analysis', 'تحليل البيانات', 'تحلیل داده‌ها', 'Data Analysis', 'डेटा विश्लेषण', 'Análisis de Datos', '数据分析', 'Datenanalyse', 2, 'Ability to analyze data and derive insights', 1, 1, 0, 1.4, 'Technical Test', 1),
        ('Technical Expertise', 'الخبرة التقنية', 'تخصص فنی', 'Technical Expertise', 'तकनीकी विशेषज्ञता', 'Experiencia Técnica', '专业技术', 'Technische Expertise', 2, 'Depth of technical knowledge', 1, 1, 0, 1.6, 'Portfolio Review', 1),
        ('Communication', 'التواصل', 'ارتباطات', 'Communication', 'संचार', 'Comunicación', '沟通', 'Kommunikation', 4, 'Effective verbal and written communication', 1, 0, 0, 1.0, 'Presentation Assessment', 1),
        ('Analytical Thinking', 'التفكير التحليلي', 'تفکر تحلیلی', 'Analytical Thinking', 'विश्लेषणात्मक सोच', 'Pensamiento Analítico', '分析思维', 'Analytisches Denken', 5, 'Break down complex problems', 1, 1, 0, 1.3, 'Case Study', 1),
        ('Collaboration', 'التعاون', 'همکاری', 'Collaboration', 'सहयोग', 'Colaboración', '协作能力', 'Zusammenarbeit', 6, 'Work effectively with others', 1, 0, 0, 1.0, 'Team Activity', 1),
    ]
    for comp in competencies:
        conn.execute("""
            INSERT OR IGNORE INTO tm_competencies 
            (name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, category_id, description, 
             is_technical, is_leadership, is_core, weight_factor, assessment_method, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, comp)

    settings = [
        ('potential_rating_scale', '3', 'String', 'Talent', 'Scale for potential ratings', 0),
        ('readiness_horizons', 'Ready Now,6 Months,1 Year,2 Years,3+ Years', 'String', 'Talent', 'Available readiness horizons', 0),
        ('talent_segments', 'High Performer High Potential,High Performer Low Potential,Low Performer High Potential,Low Performer Low Potential', 'String', 'Talent', 'Talent segmentation', 0),
        ('default_review_cycle', 'Annual', 'String', 'Review', 'Default review cycle type', 0),
        ('hi_po_criteria_performance', '4', 'Integer', 'HiPo', 'Min performance for Hi-Po', 0),
        ('hi_po_criteria_potential', '3', 'Integer', 'HiPo', 'Min potential for Hi-Po', 0),
        ('succession_coverage_target', '2', 'Integer', 'Succession', 'Target successors per critical role', 0),
        ('approval_workflow_enabled', '1', 'Boolean', 'Workflow', 'Enable approval workflows', 0),
        ('export_max_rows', '10000', 'Integer', 'Export', 'Max rows per export', 0),
    ]
    for setting in settings:
        conn.execute("""
            INSERT OR IGNORE INTO tm_talent_settings 
            (setting_key, setting_value, setting_type, category, description, is_editable)
            VALUES (?, ?, ?, ?, ?, ?)
        """, setting)

    pools = [
        ('High Potential Pool', ' pools', 'Future Leaders', 'High potential employees being developed', '{"performance_min": 4, "potential_min": 3}', '#8b5cf6', 'fa-star', 1, 0),
        ('Successor Pool', ' pools', 'Succession', 'Employees being prepared as successors', '{"succession_candidate": 1}', '#10b981', 'fa-user-clock', 1, 1),
        ('Critical Role Backup', ' pools', 'Critical', 'Backup for critical positions', '{"is_backup_candidate": 1}', '#f59e0b', 'fa-shield-alt', 1, 1),
        ('Future Leaders', ' pools', 'Leadership', 'High-performers for executive roles', '{"performance_min": 4}', '#6366f1', 'fa-crown', 1, 0),
    ]
    for pool in pools:
        conn.execute("""
            INSERT OR IGNORE INTO tm_talent_pools 
            (name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, pool_type, description, 
             criteria_json, color_code, icon_class, is_active, requires_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pool)

    conn.commit()


def get_talent_profile(employee_id: int) -> Optional[Dict[str, Any]]:
    """Get complete talent profile for an employee."""
    conn = get_db()
    try:
        profile = conn.execute("""
            SELECT tp.*, e.first_name, e.last_name, e.employee_code, e.email, e.status,
                   d.name as department_name, p.title as position_title,
                   m.first_name || ' ' || m.last_name as manager_name
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees m ON ee.reporting_to_id = m.id
            WHERE tp.employee_id = ?
        """, (employee_id,)).fetchone()
        return dict(profile) if profile else None
    finally:
        conn.close()


def get_employee_competencies(employee_id: int) -> List[Dict[str, Any]]:
    """Get all competencies for an employee with gap analysis."""
    conn = get_db()
    try:
        competencies = conn.execute("""
            SELECT ec.*, c.name as competency_name, c.name_ar, c.name_fa, c.category_id,
                   cat.name as category_name,
                   c.proficiency_levels, c.weight_factor,
                   (ec.proficiency_level - ec.required_level) as gap_score
            FROM tm_employee_competencies ec
            JOIN tm_competencies c ON ec.competency_id = c.id
            LEFT JOIN tm_competency_categories cat ON c.category_id = cat.id
            WHERE ec.employee_id = ? AND ec.status = 'Active'
            ORDER BY cat.sort_order, c.name
        """, (employee_id,)).fetchall()
        return [dict(c) for c in competencies]
    finally:
        conn.close()


def get_talent_pool_members(pool_id: int) -> List[Dict[str, Any]]:
    """Get all members of a talent pool."""
    conn = get_db()
    try:
        members = conn.execute("""
            SELECT m.*, e.first_name, e.last_name, e.employee_code, e.email,
                   d.name as department_name, p.title as position_title,
                   n.first_name || ' ' || n.last_name as nominated_by_name,
                   a.first_name || ' ' || a.last_name as approved_by_name
            FROM tm_talent_pool_members m
            JOIN hr_employees e ON m.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions p ON ee.position_id = p.id
            LEFT JOIN hr_employees n ON m.nominated_by = n.id
            LEFT JOIN hr_employees a ON m.approved_by = a.id
            WHERE m.pool_id = ? AND m.status = 'Active'
            ORDER BY m.joined_date DESC
        """, (pool_id,)).fetchall()
        return [dict(m) for m in members]
    finally:
        conn.close()


def get_succession_plans(critical_role_id: int = None) -> List[Dict[str, Any]]:
    """Get succession plans."""
    conn = get_db()
    try:
        if critical_role_id:
            plans = conn.execute("""
                SELECT sp.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code,
                       s.first_name || ' ' || s.last_name as successor_name,
                       d.first_name || ' ' || d.last_name as deputy_name,
                       cr.position_id, cr.criticality_level,
                       p.title as position_title
                FROM tm_succession_plans sp
                JOIN hr_employees e ON sp.employee_id = e.id
                LEFT JOIN hr_employees s ON sp.successor_id = s.id
                LEFT JOIN hr_employees d ON sp.deputy_id = d.id
                JOIN tm_critical_roles cr ON sp.critical_role_id = cr.id
                LEFT JOIN hr_positions p ON cr.position_id = p.id
                WHERE sp.critical_role_id = ?
                ORDER BY sp.readiness_level, sp.status
            """, (critical_role_id,)).fetchall()
        else:
            plans = conn.execute("""
                SELECT sp.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code,
                       s.first_name || ' ' || s.last_name as successor_name,
                       d.first_name || ' ' || d.last_name as deputy_name,
                       cr.position_id, cr.criticality_level,
                       p.title as position_title
                FROM tm_succession_plans sp
                JOIN hr_employees e ON sp.employee_id = e.id
                LEFT JOIN hr_employees s ON sp.successor_id = s.id
                LEFT JOIN hr_employees d ON sp.deputy_id = d.id
                JOIN tm_critical_roles cr ON sp.critical_role_id = cr.id
                LEFT JOIN hr_positions p ON cr.position_id = p.id
                WHERE sp.status != 'Archived'
                ORDER BY cr.criticality_level, sp.readiness_level
            """).fetchall()
        return [dict(p) for p in plans]
    finally:
        conn.close()


def get_development_plans(db=None, employee_id: int = None, status: str = None) -> List[Dict[str, Any]]:
    """Get development plans."""
    if db is None:
        db = get_db()
    try:
        query = """
            SELECT dp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code,
                   m.first_name || ' ' || m.last_name as manager_name,
                   a.first_name || ' ' || a.last_name as approved_by_name
            FROM tm_development_plans dp
            JOIN hr_employees e ON dp.employee_id = e.id
            LEFT JOIN hr_employees m ON dp.manager_id = m.id
            LEFT JOIN hr_employees a ON dp.approved_by = a.id
            WHERE 1=1
        """
        params = []
        if employee_id:
            query += " AND dp.employee_id = ?"
            params.append(employee_id)
        if status:
            query += " AND dp.status = ?"
            params.append(status)
        query += " ORDER BY dp.plan_year DESC, dp.created_at DESC"
        plans = db.execute(query, params).fetchall()
        return [dict(p) for p in plans]
    finally:
        db.close()


def get_talent_review_participants(review_id: int) -> List[Dict[str, Any]]:
    """Get all participants in a talent review cycle."""
    conn = get_db()
    try:
        participants = conn.execute("""
            SELECT p.*, e.first_name, e.last_name, e.employee_code,
                   m.first_name || ' ' || m.last_name as manager_name,
                   d.name as department_name,
                   pos.title as position_title
            FROM tm_talent_review_participants p
            JOIN hr_employees e ON p.employee_id = e.id
            LEFT JOIN hr_employees m ON p.manager_id = m.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            LEFT JOIN hr_positions pos ON ee.position_id = pos.id
            WHERE p.review_id = ?
            ORDER BY p.final_rating_value DESC, e.last_name
        """, (review_id,)).fetchall()
        return [dict(p) for p in participants]
    finally:
        conn.close()


def log_talent_audit(entity_type: str, entity_id: int, action: str, 
                     field_name: str = None, old_value: str = None, 
                     new_value: str = None, user_id: int = None,
                     ip_address: str = None, user_agent: str = None,
                     change_reason: str = None) -> bool:
    """Log a talent management audit entry."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO tm_talent_audit_logs 
            (entity_type, entity_id, action, field_name, old_value, new_value, 
             user_id, ip_address, user_agent, change_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, field_name, old_value, new_value,
              user_id, ip_address, user_agent, change_reason))
        conn.commit()
        return True
    except Exception as e:
        print(f"Audit log error: {e}")
        return False
    finally:
        conn.close()


def calculate_bench_strength(critical_role_id: int) -> Dict[str, Any]:
    """Calculate bench strength metrics for a critical role."""
    conn = get_db()
    try:
        cr = conn.execute("""
            SELECT cr.*, p.title as position_title, d.name as department_name
            FROM tm_critical_roles cr
            JOIN hr_positions p ON cr.position_id = p.id
            LEFT JOIN hr_departments d ON cr.department_id = d.id
            WHERE cr.id = ?
        """, (critical_role_id,)).fetchone()
        if not cr:
            return None
        successors = conn.execute("""
            SELECT sp.*, e.first_name || ' ' || e.last_name as successor_name,
                   e.employee_code
            FROM tm_succession_plans sp
            JOIN hr_employees e ON sp.successor_id = e.id
            WHERE sp.critical_role_id = ? AND sp.status = 'Approved'
            ORDER BY sp.readiness_level
        """, (critical_role_id,)).fetchall()
        total_successors = len(successors)
        ready_now = sum(1 for s in successors if s['readiness_level'] == 'Ready Now')
        ready_6m = sum(1 for s in successors if s['readiness_level'] == '6 Months')
        ready_1y = sum(1 for s in successors if s['readiness_level'] == '1 Year')
        weighted_score = (ready_now * 100 + ready_6m * 75 + ready_1y * 50) / 100 if total_successors > 0 else 0
        return {
            'critical_role': dict(cr),
            'total_successors': total_successors,
            'ready_now': ready_now,
            'ready_6_months': ready_6m,
            'ready_1_year': ready_1y,
            'bench_strength_score': round(weighted_score, 1),
            'successors': [dict(s) for s in successors]
        }
    finally:
        conn.close()


def get_talent_dashboard_metrics(department_id: int = None, entity_id: int = None) -> Dict[str, Any]:
    """Get aggregate talent dashboard metrics."""
    conn = get_db()
    try:
        base_filter = ""
        params = []
        if department_id:
            base_filter += " AND ee.department_id = ?"
            params.append(department_id)
        total_profiles = conn.execute(f"""
            SELECT COUNT(DISTINCT tp.employee_id) as cnt
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE e.status = 'Active' {base_filter}
        """, params).fetchone()['cnt']
        hipo_count = conn.execute(f"""
            SELECT COUNT(DISTINCT tp.employee_id) as cnt
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE e.status = 'Active' AND tp.hi_po = 1 {base_filter}
        """, params).fetchone()['cnt']
        critical_no_successor = conn.execute(f"""
            SELECT COUNT(*) as cnt
            FROM tm_critical_roles cr
            LEFT JOIN tm_succession_plans sp ON cr.id = sp.critical_role_id AND sp.status = 'Approved'
            WHERE cr.status = 'Active' {base_filter.replace('ee.department_id', 'cr.department_id')}
        """, params).fetchone()['cnt']
        idp_in_progress = conn.execute(f"""
            SELECT COUNT(*) as cnt
            FROM tm_development_plans dp
            JOIN hr_employees e ON dp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE dp.status = 'In Progress' {base_filter}
        """, params).fetchone()['cnt']
        active_reviews = conn.execute("""
            SELECT COUNT(*) as cnt FROM tm_talent_reviews WHERE status IN ('Planning', 'In Progress')
        """).fetchone()['cnt']
        total_critical = conn.execute(f"""
            SELECT COUNT(*) as cnt FROM tm_critical_roles WHERE status = 'Active' {base_filter.replace('ee.department_id', 'cr.department_id')}
        """, params).fetchone()['cnt']
        succession_coverage = round(((total_critical - critical_no_successor) / total_critical * 100), 1) if total_critical > 0 else 0
        readiness_dist = conn.execute(f"""
            SELECT tp.readiness_level, COUNT(*) as cnt
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            WHERE e.status = 'Active' AND tp.readiness_level IS NOT NULL {base_filter}
            GROUP BY tp.readiness_level
        """, params).fetchall()
        return {
            'total_profiles': total_profiles,
            'hi_po_count': hipo_count,
            'critical_roles_count': total_critical,
            'critical_without_successor': critical_no_successor,
            'succession_coverage_pct': succession_coverage,
            'idp_in_progress': idp_in_progress,
            'active_review_cycles': active_reviews,
            'readiness_distribution': {r['readiness_level']: r['cnt'] for r in readiness_dist}
        }
    finally:
        conn.close()


__all__ = [
    'TALENT_TABLES', 'run_talent_migrations', 'seed_talent_defaults',
    'get_db', 'get_talent_profile', 'get_employee_competencies',
    'get_talent_pool_members', 'get_succession_plans', 'get_development_plans',
    'get_talent_review_participants', 'log_talent_audit', 'calculate_bench_strength',
    'get_talent_dashboard_metrics'
]
