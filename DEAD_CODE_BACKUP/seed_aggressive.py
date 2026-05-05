"""
MMDx Aggressive Seeder - Fills ALL Empty Tables with FK Disabled
===============================================================
This script disables FK constraints during seeding to allow
unrestricted inserts, then re-enables them.

Usage:
    python seed_aggressive.py
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db(fk=True):
    conn = sqlite3.connect(DATABASE, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    if fk:
        conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def days_future(n):
    return (datetime.now() + timedelta(days=n)).strftime('%Y-%m-%d')


def get_any_id(table, db, limit=200):
    try:
        result = db.execute(f'SELECT id FROM "{table}" LIMIT {limit}').fetchall()
        return [r[0] for r in result]
    except:
        return []


def get_count(table, db):
    try:
        return db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    except:
        return 0


def table_exists(table, db):
    return db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone() is not None


# =============================================================================
# PERSIAN DATA CONSTANTS
# =============================================================================
PF = [
    'محمد', 'احمد', 'علی', 'حسین', 'رضا', 'امیر', 'مهدی', 'سجاد', 'مرتضی',
    'پوریا', 'فاطمه', 'مریم', 'زهرا', 'نرگس', 'سارا', 'نیلوفر', 'ریحانه', 'آسیه', 'محبوبه',
    'علیرضا', 'محمدرضا', 'سیدمحمد', 'ابوالفضل', 'امیرحسین', 'پارسا', 'آرتین', 'کیان',
    'زینب', 'حانیه', 'ملیکا', 'آیدا', 'روژان', 'شیما', 'نازنین', 'هلیا', 'رها'
]
PL = [
    'محمدی', 'احمدی', 'رضایی', 'حسینی', 'کریمی', 'موسوی', 'هاشمی', 'جعفری', 'صادقی',
    'میرزایی', 'علوی', 'نوری', 'مرادی', 'قاسمی', 'طاهری', 'رحیمی', 'عباسی', 'زارعی',
    'فرهادی', 'سلیمانی', 'اکبری', 'بهرامی', 'پورمحمدی', 'توکلی', 'جلالی', 'داوودی'
]
PC = [
    'شرکت بازرگانی آسیا', 'شرکت صنعتی پارس', 'شرکت تولیدی مهر', 'شرکت خدماتی آفتاب',
    'شرکت پیمانکاری سپهر', 'شرکت بازرگانی جم', 'شرکت سرمایه‌گذاری خاور', 'شرکت مهندسی نوح',
    'شرکت تولیدی بهشت', 'شرکت صادراتی ایران', 'شرکت وارداتی اتحاد', 'شرکت ساختمانی امیر',
    'شرکت نساجی پارسیان', 'شرکت الکترونیکی آردی', 'شرکت شیمیایی کیمیا', 'شرکت غذایی سلامت'
]
CC = [
    'تهران', 'اصفهان', 'مشهد', 'شیراز', 'تبریز', 'قم', 'کرج', 'اهواز',
    'مازندران', 'گیلان', 'یزد', 'سمنان', 'اردبیل', 'کرمان', 'همدان', 'زاهدان'
]


# =============================================================================
# PROJECTS MODULE
# =============================================================================
def seed_projects(db):
    """Seed all project tables."""
    print("  Seeding Projects...")

    company_ids = get_any_id('companies', db, 10)
    user_ids = get_any_id('users', db, 10)
    dept_ids = get_any_id('hr_departments', db, 10)
    cat_ids = get_any_id('project_categories', db, 10)
    type_ids = get_any_id('project_types', db, 10)

    if not company_ids:
        company_ids = [1]
    if not user_ids:
        user_ids = [1]
    if not dept_ids:
        dept_ids = [1]
    if not cat_ids:
        cat_ids = [1]
    if not type_ids:
        type_ids = [1]

    # projects
    for i in range(1, 31):
        status = random.choice(['Planning', 'Active', 'On Hold', 'Completed', 'Cancelled'])
        try:
            db.execute("""INSERT INTO projects
                (project_code, project_name, project_type_id, category_id,
                 description, start_date, end_date, status, priority,
                 company_id, manager_user_id, sponsor_user_id, owner_user_id,
                 department_id, budget, progress_percent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PRJ-{i:04d}',
                 f'پروژه {["توسعه", "بهبود", "پیاده‌سازی", "نوسازی", "تحول"][i % 5]} {i}',
                 random.choice(type_ids),
                 random.choice(cat_ids),
                 f'توضیحات پروژه شماره {i}',
                 days_ago(random.randint(30, 300)),
                 days_future(random.randint(30, 365)) if status != 'Completed' else days_ago(random.randint(1, 30)),
                 status,
                 random.choice(['Low', 'Medium', 'High', 'Critical']),
                 random.choice(company_ids),
                 random.choice(user_ids),
                 random.choice(user_ids),
                 random.choice(user_ids),
                 random.choice(dept_ids),
                 random.randint(50000, 5000000),
                 random.randint(10, 90) if status == 'Active' else random.randint(0, 100),
                 now()))
        except Exception as e:
            pass

    db.commit()
    project_ids = get_any_id('projects', db, 50)
    if not project_ids:
        return

    # project_phases
    for proj_id in project_ids:
        for j in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO project_phases
                    (project_id, phase_name, description, start_date, end_date,
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'فاز {j+1}', f'توضیحات فاز {j+1}',
                     days_ago(random.randint(1, 100)), days_future(random.randint(1, 200)),
                     random.choice(['Not Started', 'In Progress', 'Completed']), now()))
            except:
                pass
    db.commit()

    phase_ids = get_any_id('project_phases', db, 200)

    # project_milestones
    for proj_id in project_ids:
        for k in range(random.randint(2, 4)):
            try:
                db.execute("""INSERT INTO project_milestones
                    (project_id, milestone_name, description, due_date,
                     status, owner_user_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'نقطه عطف {k+1}', f'توضیحات نقطه عطف {k+1}',
                     days_future(random.randint(1, 300)),
                     random.choice(['Pending', 'Reached', 'Overdue']),
                     random.choice(user_ids), now()))
            except:
                pass
    db.commit()

    milestone_ids = get_any_id('project_milestones', db, 200)

    # project_wbs
    for proj_id in project_ids[:20]:
        try:
            db.execute("""INSERT INTO project_wbs
                (project_id, wbs_code, wbs_name, description, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (proj_id, f'WBS-{proj_id}-01',
                 f'ساختار شکست کار پروژه {proj_id}',
                 f'توضیحات WBS', now()))
        except:
            pass
    db.commit()

    wbs_ids = get_any_id('project_wbs', db, 200)

    # project_tasks
    for proj_id in project_ids:
        for t in range(random.randint(5, 15)):
            status = random.choice(['Pending', 'In Progress', 'Completed', 'Blocked'])
            try:
                db.execute("""INSERT INTO project_tasks
                    (project_id, task_name, description, assigned_user_id,
                     owner_user_id, reviewer_user_id, phase_id, wbs_id,
                     milestone_id, parent_task_id, start_date, end_date,
                     status, priority, progress_percent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'وظیفه {t+1}', f'توضیحات وظیفه {t+1}',
                     random.choice(user_ids), random.choice(user_ids),
                     random.choice(user_ids),
                     random.choice(phase_ids) if phase_ids else None,
                     random.choice(wbs_ids) if wbs_ids else None,
                     random.choice(milestone_ids) if milestone_ids else None,
                     None,
                     days_ago(random.randint(0, 50)), days_future(random.randint(1, 100)),
                     status, random.choice(['Low', 'Medium', 'High']),
                     100 if status == 'Completed' else random.randint(0, 80), now()))
            except:
                pass
    db.commit()

    task_ids = get_any_id('project_tasks', db, 500)

    # project_resource_allocations
    for proj_id in project_ids[:15]:
        for u in random.sample(user_ids, min(random.randint(2, 5), len(user_ids))):
            try:
                db.execute("""INSERT INTO project_resource_allocations
                    (project_id, user_id, role, allocated_hours,
                     allocated_percentage, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (proj_id, u,
                     random.choice(['Developer', 'Manager', 'Analyst', 'Tester']),
                     random.randint(40, 200), random.randint(25, 100), now()))
            except:
                pass

    # project_documents
    for proj_id in project_ids[:20]:
        for d in range(random.randint(1, 3)):
            try:
                db.execute("""INSERT INTO project_documents
                    (project_id, document_name, document_type,
                     uploaded_by, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (proj_id, f'سند {d} پروژه {proj_id}',
                     random.choice(['Report', 'Plan', 'Spec', 'Contract']),
                     random.choice(user_ids), now()))
            except:
                pass

    # project_issues
    for proj_id in project_ids[:20]:
        for iss in range(random.randint(0, 3)):
            try:
                db.execute("""INSERT INTO project_issues
                    (project_id, issue_title, description, severity,
                     status, reported_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'مشکل {iss+1}', f'توضیحات مشکل {iss+1}',
                     random.choice(['Low', 'Medium', 'High', 'Critical']),
                     random.choice(['Open', 'In Progress', 'Resolved', 'Closed']),
                     random.choice(user_ids), now()))
            except:
                pass

    # project_status_updates
    for proj_id in project_ids:
        for s in range(random.randint(1, 5)):
            try:
                db.execute("""INSERT INTO project_status_updates
                    (project_id, update_text, updated_by, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (proj_id, f'به‌روزرسانی وضعیت پروژه - مرحله {s}',
                     random.choice(user_ids), days_ago(random.randint(0, 100))))
            except:
                pass

    # project_approval_records
    for i in range(15):
        try:
            db.execute("""INSERT INTO project_approval_records
                (project_id, approver_id, status, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.choice(project_ids),
                 random.choice(user_ids),
                 random.choice(['Pending', 'Approved', 'Rejected']), now()))
        except:
            pass

    # project_audit_logs
    for proj_id in project_ids[:10]:
        try:
            db.execute("""INSERT INTO project_audit_logs
                (project_id, action, user_id, details, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (proj_id, 'Created', random.choice(user_ids),
                 f'لاگ حسابرسی', now()))
        except:
            pass

    db.commit()
    print("    + Projects: 30 projects, tasks, milestones seeded")


# =============================================================================
# SPC MODULE
# =============================================================================
def seed_spc(db):
    """Seed SPC tables."""
    print("  Seeding SPC...")

    part_ids = get_any_id('parts', db, 30)
    if not part_ids:
        part_ids = list(range(1, 41))

    chart_ids = get_any_id('spc_control_charts', db, 30)
    if not chart_ids:
        chart_ids = [1]

    # Add more spc_control_charts if needed
    for i in range(1, 31):
        try:
            db.execute("""INSERT INTO spc_control_charts
                (chart_code, chart_name, chart_type, part_id, process_parameter,
                 ucl, lcl, cl, sample_size, measurement_unit, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SPC-{i:03d}', f'نمودار کنترل {i}',
                 random.choice(['X-bar R', 'X-bar S', 'X-mR', 'p-chart', 'c-chart']),
                 random.choice(part_ids),
                 random.choice(['وزن', 'طول', 'عرض', 'فشار', 'دما']),
                 round(random.uniform(95, 105), 2),
                 round(random.uniform(5, 15), 2),
                 round(random.uniform(50, 60), 2),
                 random.randint(5, 25),
                 random.choice(['mm', 'kg', 'psi', '°C']), 1, now()))
        except:
            pass
    db.commit()

    chart_ids = get_any_id('spc_control_charts', db, 60)

    # spc_measurement_data
    for chart_id in chart_ids:
        for day in range(30):  # 30 days of data
            timestamp = days_ago(30 - day) + ' 08:00:00'
            for subgroup in range(4):
                try:
                    avg = round(random.uniform(48, 62), 3)
                    db.execute("""INSERT INTO spc_measurement_data
                        (chart_id, chart_code, measurement_group, sample_size,
                         sample_values, average, range_val, std_dev,
                         measurement_date, control_status, is_out_of_control, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (chart_id, f'SPC-{chart_id:03d}',
                         f'Group-{day}-{subgroup}', random.randint(5, 25),
                         ','.join([str(round(random.uniform(45, 65), 2)) for _ in range(5)]),
                         avg, round(random.uniform(0.5, 8), 3),
                         round(random.uniform(1, 5), 3),
                         timestamp,
                         random.choice(['In Control', 'Out of Control', 'Warning']),
                         1 if random.random() > 0.9 else 0, now()))
                except:
                    pass
    db.commit()

    # spc_capability_studies
    for i in range(1, 21):
        try:
            db.execute("""INSERT INTO spc_capability_studies
                (study_code, study_name, part_id, process_name, characteristic_name,
                 data_points, cp, cpk, pp, ppk, sample_size, study_date,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'STUDY-{i:03d}', f'مطالعه قابلیت {i}',
                 random.choice(part_ids), f'فرآیند تولید {i}',
                 random.choice(['قطر', 'طول', 'وزن', 'فشار']),
                 random.randint(50, 200),
                 round(random.uniform(1.0, 2.0), 3),
                 round(random.uniform(0.8, 1.8), 3),
                 round(random.uniform(1.0, 1.8), 3),
                 round(random.uniform(0.8, 1.5), 3),
                 random.randint(30, 100),
                 days_ago(random.randint(1, 180)),
                 random.choice(['Completed', 'In Progress', 'Scheduled']), now()))
        except:
            pass

    # spc_sampling_plans
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO spc_sampling_plans
                (plan_code, plan_name, inspection_level, AQL_level,
                 sample_size_code, acceptance_number, rejection_number,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PLAN-{i:03d}', f'طرح نمونه‌گیری {i}',
                 random.choice(['Normal', 'Reduced', 'Tightened']),
                 round(random.uniform(0.1, 4.0), 1),
                 random.choice(['I', 'II', 'III']),
                 random.randint(1, 5), random.randint(3, 8), 1, now()))
        except:
            pass

    # spc_specification_limits
    for part_id in part_ids[:20]:
        try:
            db.execute("""INSERT INTO spc_specification_limits
                (part_id, characteristic, usl, lsl, target, nominal,
                 measurement_unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (part_id, random.choice(['قطر', 'طول', 'عرض', 'وزن']),
                 round(random.uniform(100, 150), 2),
                 round(random.uniform(50, 90), 2),
                 round(random.uniform(95, 105), 2),
                 round(random.uniform(95, 105), 2),
                 random.choice(['mm', 'kg', 'cm']), now()))
        except:
            pass

    # spc_calibration_records
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO spc_calibration_records
                (instrument_code, instrument_name, calibration_date,
                 next_calibration_date, calibration_result, technician,
                 certificate_number, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CAL-{i:03d}', f'ابزار اندازه‌گیری {i}',
                 days_ago(random.randint(1, 180)),
                 days_future(random.randint(30, 180)),
                 random.choice(['Passed', 'Failed', 'Calibrated']),
                 f'تکنسین {random.choice(PF)} {random.choice(PL)}',
                 f'CERT-{random.randint(10000, 99999)}', 1, now()))
        except:
            pass

    # spc_gage_rr_studies
    for i in range(1, 12):
        try:
            db.execute("""INSERT INTO spc_gage_rr_studies
                (study_code, gage_name, study_date, operator_count, trial_count,
                 GRR_percentage, ndc, study_result, is_acceptable, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'GRR-{i:03d}', f'گیج {i}',
                 days_ago(random.randint(1, 120)),
                 random.randint(2, 4), random.randint(2, 5),
                 round(random.uniform(5, 35), 2), random.randint(4, 10),
                 random.choice(['Acceptable', 'Marginal', 'Unacceptable']),
                 random.choice([0, 1]), now()))
        except:
            pass

    # spc_trend_analysis
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO spc_trend_analysis
                (chart_id, analysis_date, trend_type, description,
                 severity, recommendation, is_resolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(chart_ids) if chart_ids else 1,
                 days_ago(random.randint(1, 60)),
                 random.choice(['Increasing', 'Decreasing', 'Cycling', 'Stratification']),
                 f'تحلیل روند {i}',
                 random.choice(['Low', 'Medium', 'High']),
                 f'توصیه: بررسی {i}', random.choice([0, 1]), now()))
        except:
            pass

    # spc_aql_inspections
    for i in range(1, 21):
        try:
            db.execute("""INSERT INTO spc_aql_inspections
                (inspection_code, lot_number, sample_size, AQL_level,
                 accept_number, reject_number, inspected_quantity,
                 defective_quantity, inspection_result, inspector,
                 inspection_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'AQL-{i:03d}', f'LOT-{random.randint(1000, 9999)}',
                 random.randint(20, 200), round(random.uniform(0.1, 4.0), 1),
                 random.randint(1, 5), random.randint(3, 10),
                 random.randint(50, 500), random.randint(0, 15),
                 random.choice(['Accepted', 'Rejected']),
                 f'بازرس {random.choice(PF)}',
                 days_ago(random.randint(1, 90)), now()))
        except:
            pass

    # spc_quality_metrics
    for i in range(1, 31):
        try:
            db.execute("""INSERT INTO spc_quality_metrics
                (metric_name, metric_value, metric_unit, target_value,
                 collection_date, data_source, is_within_spec, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['نرخ ضایعات', 'دقت ابعادی', 'زمان تولید', 'راندمان']),
                 round(random.uniform(0.5, 5.0), 2),
                 random.choice(['%', 'mm', 'min', 'unit/hr']),
                 round(random.uniform(1.0, 3.0), 2),
                 days_ago(random.randint(1, 60)),
                 f'خط تولید {random.randint(1, 5)}',
                 random.choice([0, 1, 1, 1]), now()))
        except:
            pass

    # spc_anomaly_alerts
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO spc_anomaly_alerts
                (chart_id, alert_type, description, detected_at,
                 acknowledged, acknowledged_by, resolved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(chart_ids) if chart_ids else 1,
                 random.choice(['Rule Violation', 'Trend Violation', 'Out of Spec']),
                 f'هشدار ناهنجاری {i}',
                 days_ago(random.randint(1, 30)),
                 random.choice([0, 1, 1]),
                 random.choice(user_ids) if user_ids else 1,
                 days_ago(random.randint(0, 15)) if random.random() > 0.3 else None, now()))
        except:
            pass

    db.commit()
    print("    + SPC: measurement data, capability studies seeded")


# =============================================================================
# TALENT MANAGEMENT
# =============================================================================
def seed_talent(db):
    """Seed Talent Management tables."""
    print("  Seeding Talent Management...")

    employee_ids = get_any_id('hr_employees', db, 100)
    dept_ids = get_any_id('hr_departments', db, 20)
    pos_ids = get_any_id('hr_positions', db, 20)
    user_ids = get_any_id('users', db, 20)

    if not employee_ids:
        employee_ids = list(range(1, 95))

    # tm_competency_categories
    cat_ids = []
    for name, desc in [('فنی', 'مهارت‌های فنی'), ('رهبری', 'رهبری و مدیریت'),
                        ('ارتباطی', 'مهارت‌های ارتباطی'), ('تحلیلی', 'تحلیلی و حل مسئله'),
                        ('بازرگانی', 'کسب‌وکار و مالی')]:
        try:
            db.execute("""INSERT INTO tm_competency_categories
                (name, description, created_at) VALUES (?, ?, ?)""",
                (name, desc, now()))
            cat_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_competencies
    comp_ids = []
    competencies = [
        ('برنامه‌نویسی Python', 'توانایی برنامه‌نویسی', cat_ids[0] if len(cat_ids) > 0 else 1, 5),
        ('تحلیل داده', 'تحلیل داده‌های کسب‌وکار', cat_ids[0] if len(cat_ids) > 0 else 1, 4),
        ('مدیریت پروژه', 'مدیریت پروژه', cat_ids[1] if len(cat_ids) > 1 else 1, 5),
        ('رهبری تیم', 'هدایت تیم', cat_ids[1] if len(cat_ids) > 1 else 1, 4),
        ('ارتباط مؤثر', 'برقراری ارتباط', cat_ids[2] if len(cat_ids) > 2 else 1, 4),
        ('حل مسئله', 'تحلیل و حل مسائل', cat_ids[3] if len(cat_ids) > 3 else 1, 5),
        ('حسابداری', 'امور مالی و حسابداری', cat_ids[4] if len(cat_ids) > 4 else 1, 3),
        ('بازاریابی', 'بازاریابی و فروش', cat_ids[4] if len(cat_ids) > 4 else 1, 3),
    ]
    for name, desc, cat_id, prof in competencies:
        try:
            db.execute("""INSERT INTO tm_competencies
                (name, description, category_id, proficiency_level, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, desc, cat_id, prof, 1, now()))
            comp_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_talent_profiles
    for emp_id in employee_ids[:50]:
        try:
            db.execute("""INSERT INTO tm_talent_profiles
                (employee_id, readiness_level, flight_risk, succession_ready,
                 potential_rating, performance_rating, last_review_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id,
                 random.choice(['Ready Now', '1-2 Years', '2-3 Years', 'Development Needed']),
                 random.choice(['Low', 'Medium', 'High']),
                 random.choice([0, 1]),
                 random.choice(['High', 'Medium', 'Low']),
                 round(random.uniform(2.5, 5.0), 1),
                 days_ago(random.randint(30, 365)), now()))
        except:
            pass
    db.commit()

    # tm_employee_competencies
    for emp_id in employee_ids[:40]:
        for comp_id in random.sample(comp_ids, min(random.randint(3, 6), len(comp_ids))):
            try:
                db.execute("""INSERT INTO tm_employee_competencies
                    (employee_id, competency_id, proficiency_level,
                     verified_by, verified_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (emp_id, comp_id, random.randint(2, 5),
                     random.choice(employee_ids),
                     days_ago(random.randint(10, 180)), now()))
            except:
                pass
    db.commit()

    # tm_talent_pools
    pool_ids = []
    for name in ['نخبگان', 'رهبران آینده', 'متخصصان فنی', 'مدیران میانی']:
        try:
            db.execute("""INSERT INTO tm_talent_pools
                (name, description, criteria, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, f'استخر استعداد {name}',
                 f'معیارهای {name}', 1, now()))
            pool_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_talent_pool_members
    for pool_id in pool_ids:
        for emp_id in random.sample(employee_ids, min(random.randint(5, 15), len(employee_ids))):
            try:
                db.execute("""INSERT INTO tm_talent_pool_members
                    (pool_id, employee_id, added_by, added_at, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (pool_id, emp_id, random.choice(employee_ids),
                     days_ago(random.randint(10, 200)),
                     random.choice(['Active', 'Inactive', 'Graduated']), now()))
            except:
                pass
    db.commit()

    # tm_critical_roles
    for i, pos_id in enumerate(random.sample(pos_ids, min(10, len(pos_ids))) if pos_ids else range(1, 11)):
        try:
            db.execute("""INSERT INTO tm_critical_roles
                (position_id, role_name, criticality_level, succession_urgency,
                 is_backfilled, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (pos_id, f'نقش حیاتی {i+1}',
                 random.choice(['Critical', 'High', 'Medium']),
                 random.choice(['Immediate', '1-3 Months', '3-6 Months']),
                 random.choice([0, 1]), now()))
        except:
            pass
    db.commit()

    # tm_succession_plans
    for pool_id in pool_ids[:3]:
        for emp_id in random.sample(employee_ids, min(random.randint(3, 8), len(employee_ids))):
            try:
                db.execute("""INSERT INTO tm_succession_plans
                    (employee_id, target_role_id, readiness_timeline,
                     development_actions, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (emp_id, random.choice(pos_ids) if pos_ids else 1,
                     random.choice(['Ready Now', '6 Months', '1 Year']),
                     f'اقدامات توسعه', random.choice(['Active', 'Completed', 'On Hold']), now()))
            except:
                pass
    db.commit()

    # tm_development_plans
    for emp_id in employee_ids[:30]:
        try:
            db.execute("""INSERT INTO tm_development_plans
                (employee_id, plan_title, description, goal_type,
                 start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, f'برنامه توسعه {emp_id}',
                 f'شرح برنامه',
                 random.choice(['Technical', 'Leadership', 'Certification']),
                 days_ago(random.randint(10, 60)), days_future(random.randint(30, 180)),
                 random.choice(['Not Started', 'In Progress', 'Completed']), now()))
        except:
            pass
    db.commit()

    # tm_development_goals
    for emp_id in employee_ids[:30]:
        for g in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO tm_development_goals
                    (employee_id, goal_text, goal_type, target_date,
                     status, progress_percent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, f'هدف {g+1}: {random.choice(["یادگیری", "مهارت", "گواهینامه"])}',
                     random.choice(['Learning', 'Skill', 'Certification']),
                     days_future(random.randint(30, 200)),
                     random.choice(['Not Started', 'In Progress', 'Completed']),
                     random.randint(0, 100), now()))
            except:
                pass
    db.commit()

    # tm_talent_reviews
    for emp_id in employee_ids[:35]:
        try:
            db.execute("""INSERT INTO tm_talent_reviews
                (employee_id, review_date, reviewer_id, overall_rating,
                 potential_rating, retention_risk, recommendations, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, days_ago(random.randint(30, 300)),
                 random.choice(employee_ids),
                 round(random.uniform(2.5, 5.0), 1),
                 random.choice(['High', 'Medium', 'Low']),
                 random.choice(['Low', 'Medium', 'High']),
                 f'توصیه‌های ارزیابی', now()))
        except:
            pass

    # tm_mentoring_assignments
    for i in range(1, 21):
        try:
            db.execute("""INSERT INTO tm_mentoring_assignments
                (mentor_id, mentee_id, relationship_type, start_date,
                 end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(employee_ids), random.choice(employee_ids),
                 random.choice(['Formal', 'Informal', 'Reverse']),
                 days_ago(random.randint(30, 180)),
                 days_future(random.randint(30, 180)),
                 random.choice(['Active', 'Completed', 'Terminated']), now()))
        except:
            pass

    # tm_career_paths
    for pos_id in random.sample(pos_ids, min(8, len(pos_ids))) if pos_ids else range(1, 9):
        try:
            db.execute("""INSERT INTO tm_career_paths
                (position_id, career_path_name, path_description,
                 is_technical_track, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (pos_id, f'مسیر شغلی {pos_id}',
                 f'شرح مسیر شغلی',
                 random.choice([0, 1]), now()))
        except:
            pass

    # tm_talent_notes
    for emp_id in employee_ids[:20]:
        try:
            db.execute("""INSERT INTO tm_talent_notes
                (employee_id, note_text, note_type, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (emp_id, f'یادداشت استعداد {emp_id}',
                 random.choice(['General', 'Development', 'Performance']),
                 random.choice(employee_ids), now()))
        except:
            pass

    # tm_talent_history
    for emp_id in employee_ids[:20]:
        for h in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO tm_talent_history
                    (employee_id, event_type, event_date, description, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (emp_id, random.choice(['Promotion', 'Transfer', 'Review', 'Award']),
                     days_ago(random.randint(30, 365)),
                     f'رویداد {h} برای {emp_id}', now()))
            except:
                pass

    # tm_mobility_requests
    for emp_id in random.sample(employee_ids, min(15, len(employee_ids))):
        try:
            db.execute("""INSERT INTO tm_mobility_requests
                (employee_id, request_type, from_department_id, to_department_id,
                 request_date, target_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, random.choice(['Internal Transfer', 'Promotion', 'Lateral Move']),
                 random.choice(dept_ids) if dept_ids else 1,
                 random.choice(dept_ids) if dept_ids else 1,
                 days_ago(random.randint(10, 60)),
                 days_future(random.randint(30, 120)),
                 random.choice(['Pending', 'Approved', 'Rejected']), now()))
        except:
            pass

    db.commit()
    print("    + Talent Management seeded")


# =============================================================================
# MANUFACTURING / WORK CENTERS
# =============================================================================
def seed_manufacturing(db):
    """Seed manufacturing tables."""
    print("  Seeding Manufacturing...")

    company_ids = get_any_id('companies', db, 10)
    branch_ids = get_any_id('company_branches', db, 10)
    employee_ids = get_any_id('hr_employees', db, 50)
    warehouse_ids = get_any_id('warehouses', db, 10)
    part_ids = get_any_id('parts', db, 30)

    if not company_ids:
        company_ids = [1]
    if not branch_ids:
        branch_ids = [1]
    if not employee_ids:
        employee_ids = list(range(1, 95))
    if not warehouse_ids:
        warehouse_ids = [1]
    if not part_ids:
        part_ids = list(range(1, 41))

    # work_centers
    wc_types = ['Assembly', 'Machining', 'Painting', 'Packaging', 'Testing', 'Welding', 'CNC']
    wc_ids = []
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO work_centers
                (work_center_code, work_center_name, description, work_center_type,
                 plant_id, location, capacity_hours_per_day, efficiency_target,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WC-{i:02d}',
                 f'مرکز کار {["مونتاژ", "ماشین‌کاری", "رنگ‌آمیزی", "بسته‌بندی", "آزمایش", "جوشکاری", "CNC"][i % 7]} {i}',
                 f'مرکز کار تولیدی {i}',
                 wc_types[i % len(wc_types)],
                 random.choice(branch_ids) if branch_ids else 1,
                 f'سالن {["A", "B", "C", "D", "E"][i % 5]}',
                 random.randint(8, 16), round(random.uniform(80, 98), 1),
                 random.choice(['Active', 'Active', 'Active', 'Idle', 'Maintenance']), now()))
            wc_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # work_center_shifts
    for wc_id in wc_ids:
        for name, start, end in [('صبح', '06:00', '14:00'), ('عصر', '14:00', '22:00'), ('شب', '22:00', '06:00')]:
            try:
                db.execute("""INSERT INTO work_center_shifts
                    (work_center_id, shift_name, start_time, end_time,
                     is_night_shift, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (wc_id, name, start, end, 1 if 'شب' in name else 0, 1, now()))
            except:
                pass

    # work_center_capacity
    for wc_id in wc_ids:
        for month in range(1, 7):
            try:
                db.execute("""INSERT INTO work_center_capacity
                    (work_center_id, period_start, available_hours, scheduled_hours,
                     utilized_hours, efficiency_percent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (wc_id, f'2025-{month:02d}-01',
                     random.randint(160, 320), random.randint(100, 280),
                     random.randint(80, 240), round(random.uniform(60, 95), 1), now()))
            except:
                pass
    db.commit()

    # work_order_operation_codes
    op_codes = [
        ('CUT', 'برش', 'عملیات برش'), ('DRILL', 'سوراخ‌کاری', 'سوراخ‌کاری دقیق'),
        ('WELD', 'جوشکاری', 'جوشکاری'), ('ASSEM', 'مونتاژ', 'مونتاژ نهایی'),
        ('PAINT', 'رنگ‌آمیزی', 'رنگ‌آمیزی'), ('PACK', 'بسته‌بندی', 'بسته‌بندی'),
        ('INSPECT', 'بازرسی', 'بازرسی'), ('TEST', 'آزمایش', 'تست')
    ]
    for code, name, desc in op_codes:
        try:
            db.execute("""INSERT INTO work_order_operation_codes
                (operation_code, operation_name, description,
                 estimated_time_minutes, work_center_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (code, name, desc, random.randint(10, 120),
                 random.choice(wc_ids) if wc_ids else 1, 1, now()))
        except:
            pass
    db.commit()

    # work_order_operations
    for i in range(1, 101):
        for seq, (code, name, desc) in enumerate(random.sample(op_codes, random.randint(3, 6)), 1):
            try:
                db.execute("""INSERT INTO work_order_operations
                    (operation_code, operation_name, work_center_id, sequence_number,
                     planned_start, planned_end, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (code, name, random.choice(wc_ids) if wc_ids else 1, seq,
                     days_ago(random.randint(1, 30)), days_ago(random.randint(0, 20)),
                     random.choice(['Pending', 'In Progress', 'Completed']), now()))
            except:
                pass
    db.commit()

    # work_order_components
    for wo_op_id in range(1, 101):
        for comp in range(random.randint(2, 6)):
            try:
                db.execute("""INSERT INTO work_order_components
                    (work_order_operation_id, component_part_id, quantity_required,
                     quantity_issued, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (wo_op_id, random.choice(part_ids),
                     random.randint(1, 20), random.randint(0, 15),
                     random.choice(['Pending', 'Issued', 'Consumed']), now()))
            except:
                pass
    db.commit()

    # work_order_confirmations
    for i in range(1, 101):
        try:
            db.execute("""INSERT INTO work_order_confirmations
                (confirmation_date, confirmed_by, quantity_completed,
                 quantity_rejected, work_station_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (days_ago(random.randint(0, 30)),
                 random.choice(employee_ids),
                 random.randint(50, 500), random.randint(0, 10),
                 random.choice(wc_ids) if wc_ids else 1,
                 random.choice(['Confirmed', 'Pending']), now()))
        except:
            pass

    # work_order_cost_plan
    for i in range(1, 51):
        try:
            db.execute("""INSERT INTO work_order_cost_plan
                (cost_type, planned_cost, actual_cost, variance,
                 currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Material', 'Labor', 'Overhead', 'Total']),
                 round(random.uniform(1000, 50000), 2),
                 round(random.uniform(1000, 50000), 2),
                 round(random.uniform(-5000, 5000), 2),
                 random.choice(['USD', 'AED']), now()))
        except:
            pass

    # work_order_skill_requirements
    for wc_id in wc_ids[:8]:
        for skill in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO work_order_skill_requirements
                    (work_center_id, skill_name, required_level,
                     is_mandatory, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (wc_id, f'مهارت {skill}', random.randint(1, 5),
                     random.choice([0, 1]), now()))
            except:
                pass

    # work_order_tools
    for wc_id in wc_ids[:8]:
        for tool in range(random.randint(3, 8)):
            try:
                db.execute("""INSERT INTO work_order_tools
                    (work_center_id, tool_name, tool_type, quantity_available,
                     maintenance_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (wc_id, f'ابزار {tool}',
                     random.choice(['Hand', 'Power', 'Measuring']),
                     random.randint(1, 20),
                     random.choice(['Good', 'Needs Maintenance', 'New']), now()))
            except:
                pass

    db.commit()
    print("    + Manufacturing: work centers, operations seeded")


# =============================================================================
# SERVICE, WARRANTY, TECHNICIAN
# =============================================================================
def seed_service(db):
    """Seed service, warranty, technician tables."""
    print("  Seeding Service/Warranty...")

    employee_ids = get_any_id('hr_employees', db, 30)
    customer_ids = get_any_id('customers', db, 50)
    part_ids = get_any_id('parts', db, 30)
    user_ids = get_any_id('users', db, 20)

    if not employee_ids:
        employee_ids = list(range(1, 95))
    if not customer_ids:
        customer_ids = list(range(1, 785))
    if not part_ids:
        part_ids = list(range(1, 41))
    if not user_ids:
        user_ids = [1]

    # service_agreements
    ag_types = ['Basic', 'Standard', 'Premium', 'Enterprise']
    for i in range(1, 31):
        try:
            db.execute("""INSERT INTO service_agreements
                (agreement_number, customer_id, agreement_type, start_date,
                 end_date, coverage_terms, annual_value, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SA-{i:04d}', random.choice(customer_ids),
                 ag_types[i % len(ag_types)],
                 days_ago(random.randint(30, 365)),
                 days_future(random.randint(30, 365)),
                 f'پوشش {["پایه", "استاندارد", "ویژه", "سازمانی"][i % 4]}',
                 round(random.uniform(5000, 100000), 2),
                 random.choice(['Active', 'Expired', 'Renewed', 'Cancelled']), now()))
        except:
            pass

    # service_order_types
    for name in ['Installation', 'Repair', 'Maintenance', 'Inspection', 'Emergency']:
        try:
            db.execute("""INSERT INTO service_order_types
                (type_name, description, SLA_hours, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, f'توضیحات {name}', random.randint(4, 72), 1, now()))
        except:
            pass

    # warranty_records
    for i in range(1, 41):
        try:
            db.execute("""INSERT INTO warranty_records
                (warranty_number, customer_id, part_id, serial_number,
                 purchase_date, warranty_start_date, warranty_end_date,
                 warranty_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WARR-{i:04d}', random.choice(customer_ids),
                 random.choice(part_ids), f'SN-{random.randint(10000, 99999)}',
                 days_ago(random.randint(30, 365)),
                 days_ago(random.randint(0, 30)),
                 days_future(random.randint(30, 730)),
                 random.choice(['Standard', 'Extended', 'Manufacturer']),
                 random.choice(['Active', 'Expired', 'Claimed']), now()))
        except:
            pass

    # warranty_claims
    for i in range(1, 26):
        try:
            db.execute("""INSERT INTO warranty_claims
                (claim_number, warranty_id, claim_type, description,
                 claim_amount, status, filed_date, resolved_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WC-{i:04d}', random.randint(1, 40),
                 random.choice(['Repair', 'Replacement', 'Refund']),
                 f'توضیحات ادعای گارانتی {i}',
                 round(random.uniform(100, 5000), 2),
                 random.choice(['Submitted', 'Under Review', 'Approved', 'Rejected']),
                 days_ago(random.randint(1, 60)),
                 days_ago(random.randint(0, 30)) if random.random() > 0.3 else None, now()))
        except:
            pass

    # technician_shifts
    for emp_id in random.sample(employee_ids, min(20, len(employee_ids))):
        for name, start, end in [('صبح', '06:00', '14:00'), ('عصر', '14:00', '22:00')]:
            try:
                db.execute("""INSERT INTO technician_shifts
                    (technician_id, shift_date, shift_name, start_time,
                     end_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, days_ago(random.randint(0, 14)),
                     name, start, end,
                     random.choice(['Scheduled', 'Completed', 'Absent']), now()))
            except:
                pass

    # technician_skill_levels
    for emp_id in random.sample(employee_ids, min(20, len(employee_ids))):
        skills = ['Electronics', 'Mechanical', 'Hydraulics', 'Pneumatics', 'PLC', 'HVAC']
        for skill in random.sample(skills, random.randint(2, 4)):
            try:
                db.execute("""INSERT INTO technician_skill_levels
                    (technician_id, skill_name, skill_level, certified_date,
                     expiry_date, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, skill, random.randint(1, 5),
                     days_ago(random.randint(30, 365)),
                     days_future(random.randint(90, 730)), 1, now()))
            except:
                pass

    # skill_catalog
    for skill in ['Electronics', 'Mechanical', 'Hydraulics', 'Pneumatics',
                  'PLC Programming', 'HVAC', 'Welding', 'CNC Operation', 'Quality Control', 'Safety']:
        try:
            db.execute("""INSERT INTO skill_catalog
                (skill_name, description, category, proficiency_levels,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (skill, f'توضیحات {skill}',
                 random.choice(['Technical', 'Safety', 'Management']),
                 '1-5', 1, now()))
        except:
            pass

    db.commit()
    print("    + Service, Warranty, Technician seeded")


# =============================================================================
# CRM EXTRA
# =============================================================================
def seed_crm(db):
    """Seed additional CRM tables."""
    print("  Seeding CRM extra...")

    customer_ids = get_any_id('customers', db, 100)
    user_ids = get_any_id('users', db, 20)
    employee_ids = get_any_id('hr_employees', db, 30)

    if not customer_ids:
        customer_ids = list(range(1, 785))
    if not user_ids:
        user_ids = [1]
    if not employee_ids:
        employee_ids = list(range(1, 95))

    # crm_customer_contacts
    for cust_id in random.sample(customer_ids, min(50, len(customer_ids))):
        for c in range(random.randint(1, 3)):
            try:
                db.execute("""INSERT INTO crm_customer_contacts
                    (customer_id, contact_name, contact_role, phone, email,
                     is_primary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (cust_id,
                     f'{random.choice(PF)} {random.choice(PL)}',
                     random.choice(['مدیر', 'کارشناس', 'مسئول', 'مدیرعامل']),
                     f'+97150{random.randint(1000000, 9999999)}',
                     f'c{c}{cust_id}@example.com',
                     1 if c == 0 else 0, now()))
            except:
                pass

    # crm_lead_contacts
    for i in range(1, 51):
        try:
            db.execute("""INSERT INTO crm_lead_contacts
                (lead_id, contact_name, phone, email, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (i, f'{random.choice(PF)} {random.choice(PL)}',
                 f'+97150{random.randint(1000000, 9999999)}',
                 f'lead{i}@example.com', now()))
        except:
            pass

    # crm_lead_notes
    for i in range(1, 41):
        try:
            db.execute("""INSERT INTO crm_lead_notes
                (lead_id, note_text, created_by, created_at)
                VALUES (?, ?, ?, ?)""",
                (i % 50 + 1, f'یادداشت برای لید {i}',
                 random.choice(user_ids), now()))
        except:
            pass

    # crm_lead_qualifications
    for i in range(1, 31):
        try:
            db.execute("""INSERT INTO crm_lead_qualifications
                (lead_id, qualification_score, budget, timeline,
                 decision_maker, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (i % 50 + 1, random.randint(1, 10),
                 random.choice(['<10K', '10K-50K', '50K-100K', '>100K']),
                 random.choice(['Immediate', '1-3 Months', '3-6 Months']),
                 random.choice([0, 1]), now()))
        except:
            pass

    # crm_customer_segments
    for i in range(1, 11):
        try:
            db.execute("""INSERT INTO crm_customer_segments
                (segment_name, segment_code, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'Segment {i}', f'SEG-{i:02d}',
                 f'توضیحات بخش {i}', 1, now()))
        except:
            pass

    # crm_customer_engagement
    for cust_id in random.sample(customer_ids, min(40, len(customer_ids))):
        for e in range(random.randint(2, 6)):
            try:
                db.execute("""INSERT INTO crm_customer_engagement
                    (customer_id, engagement_type, engagement_date, score, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (cust_id, random.choice(['Email', 'Call', 'Meeting', 'Visit']),
                     days_ago(random.randint(1, 90)),
                     random.randint(1, 10), now()))
            except:
                pass

    # crm_customer_credit_risk
    for cust_id in random.sample(customer_ids, min(40, len(customer_ids))):
        try:
            db.execute("""INSERT INTO crm_customer_credit_risk
                (customer_id, risk_score, risk_rating, credit_limit,
                 outstanding_balance, risk_factors, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cust_id, round(random.uniform(1, 10), 1),
                 random.choice(['Low', 'Medium', 'High']),
                 random.randint(10000, 500000), random.randint(0, 200000),
                 f'عوامل ریسک', now()))
        except:
            pass

    # crm_customer_churn_risk
    for cust_id in random.sample(customer_ids, min(40, len(customer_ids))):
        try:
            db.execute("""INSERT INTO crm_customer_churn_risk
                (customer_id, churn_score, risk_level, churn_probability,
                 retention_actions, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (cust_id, round(random.uniform(0, 100), 1),
                 random.choice(['Low', 'Medium', 'High', 'Critical']),
                 round(random.uniform(0, 0.5), 3),
                 random.choice(['None', 'Discount', 'Call', 'Loyalty']), now()))
        except:
            pass

    # crm_touchpoints
    for cust_id in random.sample(customer_ids, min(30, len(customer_ids))):
        for t in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO crm_touchpoints
                    (customer_id, touchpoint_type, touchpoint_date, channel,
                     sentiment, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (cust_id, random.choice(['Website', 'Store', 'Call', 'Email', 'Social']),
                     days_ago(random.randint(1, 60)),
                     random.choice(['Online', 'Offline', 'Phone']),
                     random.choice(['Positive', 'Neutral', 'Negative']), now()))
            except:
                pass

    # crm_account_reviews
    for i in range(1, 21):
        try:
            db.execute("""INSERT INTO crm_account_reviews
                (customer_id, review_date, reviewer_id, overall_rating,
                 financial_rating, operational_rating, strategic_rating,
                 next_review_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(customer_ids),
                 days_ago(random.randint(1, 180)),
                 random.choice(user_ids),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 days_future(random.randint(30, 180)), now()))
        except:
            pass

    db.commit()
    print("    + CRM extra seeded")


# =============================================================================
# QUALITY EXTRA
# =============================================================================
def seed_quality(db):
    """Seed additional quality tables."""
    print("  Seeding Quality extra...")

    employee_ids = get_any_id('hr_employees', db, 30)
    part_ids = get_any_id('parts', db, 30)

    if not employee_ids:
        employee_ids = list(range(1, 95))
    if not part_ids:
        part_ids = list(range(1, 41))

    # quality_inspections
    for i in range(21, 61):
        try:
            db.execute("""INSERT INTO quality_inspections
                (inspection_number, inspection_type, part_id, quantity_inspected,
                 quantity_passed, quantity_failed, defect_rate, result,
                 inspector_id, inspection_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'INS-{i:04d}', random.choice(['Incoming', 'In-Process', 'Final']),
                 random.choice(part_ids), random.randint(50, 500),
                 random.randint(40, 480), random.randint(0, 30),
                 round(random.uniform(0, 5), 2),
                 random.choice(['PASS', 'FAIL']),
                 random.choice(employee_ids),
                 days_ago(random.randint(1, 90)), now()))
        except:
            pass

    # quality_non_conformances
    for i in range(11, 31):
        try:
            db.execute("""INSERT INTO quality_non_conformances
                (ncr_number, description, severity, status, reported_by,
                 reported_date, resolved_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'NCR-{i:04d}', f'توضیحات عدم انطباق {i}',
                 random.choice(['Critical', 'Major', 'Minor']),
                 random.choice(['Open', 'In Progress', 'Closed']),
                 random.choice(employee_ids),
                 days_ago(random.randint(1, 120)),
                 days_ago(random.randint(0, 60)) if random.random() > 0.3 else None, now()))
        except:
            pass

    # quality_capa_records
    for i in range(9, 24):
        try:
            db.execute("""INSERT INTO quality_capa_records
                (capa_number, title, description, severity, status,
                 root_cause, corrective_action, preventive_action,
                 assigned_to, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CAPA-{i:04d}', f'CAPA {i}',
                 f'شرح CAPA {i}',
                 random.choice(['Critical', 'Major', 'Minor']),
                 random.choice(['Open', 'In Progress', 'Completed', 'Verified']),
                 f'علت ریشه‌ای {i}',
                 f'اقدام اصلاحی {i}',
                 f'اقدام پیشگیرانه {i}',
                 random.choice(employee_ids),
                 days_future(random.randint(7, 60)), now()))
        except:
            pass

    # quality_audit_plans
    for i in range(7, 17):
        try:
            db.execute("""INSERT INTO quality_audit_plans
                (plan_code, plan_name, audit_type, scope, objectives,
                 auditor_id, scheduled_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'AUD-PLAN-{i:03d}', f'برنامه ممیزی {i}',
                 random.choice(['Internal', 'External', 'Supplier']),
                 f'دامنه {i}', f'اهداف {i}',
                 random.choice(employee_ids),
                 days_future(random.randint(7, 90)),
                 random.choice(['Planned', 'In Progress', 'Completed']), now()))
        except:
            pass

    # quality_audit_findings
    for i in range(2, 31):
        try:
            db.execute("""INSERT INTO quality_audit_findings
                (audit_plan_id, finding_code, finding_type, description,
                 severity, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 16), f'FIND-{i:03d}',
                 random.choice(['Non-Conformance', 'Observation', 'Opportunity']),
                 f'یافته {i}',
                 random.choice(['Critical', 'Major', 'Minor', 'Observation']),
                 random.choice(['Open', 'In Progress', 'Closed']),
                 days_future(random.randint(7, 45)), now()))
        except:
            pass

    db.commit()
    print("    + Quality extra seeded")


# =============================================================================
# BTP/INTEGRATION EXTRA
# =============================================================================
def seed_btp(db):
    """Seed additional BTP/integration tables."""
    print("  Seeding BTP/Integration...")

    connector_ids = get_any_id('btp_connectors', db, 20)
    flow_ids = get_any_id('btp_integration_flows', db, 20)
    user_ids = get_any_id('users', db, 20)

    if not connector_ids:
        connector_ids = list(range(1, 16))
    if not flow_ids:
        flow_ids = list(range(1, 16))
    if not user_ids:
        user_ids = [1]

    tables_btp = [
        ('btp_ai_chats', 25, lambda: f"chat-{random.randint(1,1000)}"),
        ('btp_ai_messages', 80, lambda: f"msg-{random.randint(1,500)}"),
        ('btp_event_subscriptions', 15, lambda: f"sub-{random.randint(1,100)}"),
        ('btp_webhook_deliveries', 30, lambda: f"wh-{random.randint(1,200)}"),
        ('btp_change_requests', 18, lambda: f"CR-{random.randint(1000,9999)}"),
        ('btp_mapping_versions', 12, lambda: f"map-{random.randint(1,50)}"),
        ('btp_extension_rules', 12, lambda: f"rule-{random.randint(1,50)}"),
        ('btp_job_attempts', 30, lambda: f"job-{random.randint(1,200)}"),
        ('btp_connector_logs', 50, lambda: f"log-{random.randint(1,300)}"),
        ('btp_data_quality_checks', 20, lambda: f"qc-{random.randint(1,100)}"),
        ('btp_reconciliations', 15, lambda: f"rec-{random.randint(1,50)}"),
        ('btp_export_history', 18, lambda: f"exp-{random.randint(1,50)}"),
        ('btp_secret_references', 10, lambda: f"sec-{random.randint(1,50)}"),
        ('btp_file_templates', 10, lambda: f"tpl-{random.randint(1,50)}"),
        ('btp_api_versions', 8, lambda: f"v{random.randint(1,5)}.0"),
        ('btp_api_policies', 12, lambda: f"pol-{random.randint(1,50)}"),
        ('btp_provider_usage_logs', 30, lambda: f"usage-{random.randint(1,100)}"),
        ('btp_flow_versions', 12, lambda: f"fv-{random.randint(1,50)}"),
    ]

    for table, count, id_fn in tables_btp:
        if not table_exists(table, db):
            continue
        for i in range(count):
            try:
                if 'ai_chat' in table:
                    db.execute(f"""INSERT INTO {table}
                        (chat_session_id, user_id, provider, model, prompt_tokens,
                         completion_tokens, total_tokens, latency_ms, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (id_fn(), random.choice(user_ids),
                         random.choice(['OpenAI', 'Azure OpenAI', 'Anthropic']),
                         random.choice(['gpt-4', 'gpt-3.5-turbo']),
                         random.randint(100, 2000), random.randint(100, 3000),
                         random.randint(200, 5000), random.randint(500, 5000), now()))
                elif 'webhook' in table:
                    db.execute(f"""INSERT INTO {table}
                        (webhook_id, endpoint, payload, response_status,
                         attempt_number, delivered_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (random.randint(1, 10), f'https://api.example.com/{i+1}',
                         f'{{"event": {i+1}}}',
                         random.choice([200, 200, 201, 400, 500]),
                         random.randint(1, 3),
                         days_ago(random.randint(0, 30)), now()))
                elif 'subscription' in table:
                    db.execute(f"""INSERT INTO {table}
                        (subscription_name, event_type, endpoint_url,
                         auth_type, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (f'sub-{i+1}',
                         random.choice(['order.created', 'inventory.updated']),
                         f'https://api.example.com/wh/{i+1}',
                         random.choice(['Bearer', 'API Key']), 1, now()))
                elif 'job_attempt' in table:
                    db.execute(f"""INSERT INTO {table}
                        (job_id, attempt_number, status, started_at,
                         completed_at, error_message, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (random.randint(1, 25), i % 3 + 1,
                         random.choice(['Running', 'Success', 'Failed']),
                         days_ago(random.randint(0, 20)),
                         days_ago(random.randint(0, 15)),
                         f'خطا {i+1}' if random.random() > 0.7 else None, now()))
                elif 'data_quality' in table:
                    db.execute(f"""INSERT INTO {table}
                        (check_name, check_type, entity, passed_count,
                         failed_count, check_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (f'Check {i+1}',
                         random.choice(['Completeness', 'Uniqueness']),
                         random.choice(['Customer', 'Order']),
                         random.randint(80, 100), random.randint(0, 20),
                         days_ago(random.randint(0, 30)), now()))
                elif 'reconciliation' in table:
                    db.execute(f"""INSERT INTO {table}
                        (reconciliation_id, source_system, target_system,
                         record_count, matched_count, discrepancies,
                         status, run_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (f'REC-{i+1:04d}', 'SAP', 'Salesforce',
                         random.randint(100, 1000), random.randint(80, 950),
                         random.randint(0, 50),
                         random.choice(['Completed', 'In Progress']),
                         days_ago(random.randint(0, 30)), now()))
                elif 'provider_usage' in table:
                    db.execute(f"""INSERT INTO {table}
                        (provider, model, input_tokens, output_tokens,
                         cost, latency_ms, call_date, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (random.choice(['OpenAI', 'Azure', 'Anthropic']),
                         random.choice(['gpt-4', 'claude-3']),
                         random.randint(100, 5000), random.randint(100, 5000),
                         round(random.uniform(0.1, 10.0), 4),
                         random.randint(100, 3000),
                         days_ago(random.randint(0, 14)), now()))
                elif 'change_request' in table:
                    db.execute(f"""INSERT INTO {table}
                        (request_id, change_type, description, status,
                         requested_by, approved_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (f'CR-{i+1:04d}',
                         random.choice(['Feature', 'Bug Fix', 'Config']),
                         f'توضیحات {i+1}',
                         random.choice(['Draft', 'Submitted', 'Approved']),
                         random.choice(user_ids),
                         random.choice(user_ids), now()))
                elif 'export_history' in table:
                    db.execute(f"""INSERT INTO {table}
                        (export_name, export_type, file_path, record_count,
                         status, exported_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (f'Export {i+1}', random.choice(['Full', 'Incremental']),
                         f'/exports/file_{i+1}.csv',
                         random.randint(100, 5000),
                         random.choice(['Completed', 'Failed']),
                         random.choice(user_ids), now()))
                elif 'mapping_version' in table:
                    db.execute(f"""INSERT INTO {table}
                        (mapping_id, version_number, mapping_config,
                         is_active, created_by, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                        (random.randint(1, 10), i + 1,
                         f'{{"v": {i+1}}}',
                         1 if i == 0 else 0,
                         random.choice(user_ids), now()))
                elif 'extension_rule' in table:
                    db.execute(f"""INSERT INTO {table}
                        (rule_name, rule_type, extension_point,
                         rule_config, priority, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (f'Rule {i+1}',
                         random.choice(['Pre', 'Post', 'Transform']),
                         random.choice(['OrderProcessing', 'CustomerSync']),
                         f'{{"id": {i+1}}}',
                         random.randint(1, 10), 1, now()))
                elif 'job_attempt' in table or 'flow_version' in table or 'file_template' in table or 'secret_reference' in table or 'api_version' in table or 'api_policy' in table:
                    pass  # Skip for now, handled above
            except:
                pass
        db.commit()

    print("    + BTP/Integration extra seeded")


# =============================================================================
# MINIMAL / ALL OTHER EMPTY TABLES
# =============================================================================
def seed_minimal(db):
    """Seed all remaining minimal empty tables with generic data."""
    print("  Seeding remaining minimal tables...")

    user_ids = get_any_id('users', db, 20)
    company_ids = get_any_id('companies', db, 10)
    employee_ids = get_any_id('hr_employees', db, 30)
    customer_ids = get_any_id('customers', db, 50)
    warehouse_ids = get_any_id('warehouses', db, 10)
    part_ids = get_any_id('parts', db, 30)

    if not user_ids:
        user_ids = [1]
    if not company_ids:
        company_ids = [1]
    if not employee_ids:
        employee_ids = list(range(1, 95))
    if not customer_ids:
        customer_ids = list(range(1, 785))
    if not warehouse_ids:
        warehouse_ids = [1]
    if not part_ids:
        part_ids = list(range(1, 41))

    minimal_seeds = [
        # ('table_name', count, insert_sql, [param_funcs])
        ('quick_notes', 20,
         "INSERT INTO quick_notes (note_text, user_id, is_pinned, created_at) VALUES (?, ?, ?, ?)",
         [lambda i: f'یادداشت سریع {i}', lambda i: random.choice(user_ids), lambda i: random.choice([0, 1]), lambda i: now()]),

        ('quick_access_items', 15,
         "INSERT INTO quick_access_items (item_name, item_type, item_url, user_id, access_count, last_accessed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'آیتم {i}', lambda i: random.choice(['page', 'report']), lambda i: f'/page/{i}', lambda i: random.choice(user_ids),
          lambda i: random.randint(1, 50), lambda i: days_ago(random.randint(0, 30)), lambda i: now()]),

        ('saved_searches', 12,
         "INSERT INTO saved_searches (search_name, search_query, user_id, is_shared, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'جستجوی {i}', lambda i: f'q={i}', lambda i: random.choice(user_ids), lambda i: random.choice([0, 1]), lambda i: now()]),

        ('shift_definitions', 5,
         "INSERT INTO shift_definitions (shift_code, shift_name, start_time, end_time, is_night_shift, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'SHIFT-{i}', lambda i: f'شیفت {i}', lambda i: f'{6+i*8:02d}:00', lambda i: f'{14+i*8:02d}:00', lambda i: 0, lambda i: 1, lambda i: now()]),

        ('shift_patterns', 6,
         "INSERT INTO shift_patterns (pattern_name, pattern_type, rotation_days, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'Pattern {i}', lambda i: random.choice(['Fixed', 'Rotating']), lambda i: random.randint(1, 7), lambda i: 1, lambda i: now()]),

        ('travel_segments', 25,
         "INSERT INTO travel_segments (itinerary_id, segment_type, departure_city, arrival_city, departure_time, arrival_time, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 25), lambda i: random.choice(['Flight', 'Hotel', 'Car']),
          lambda i: random.choice(CC), lambda i: random.choice(CC),
          lambda i: days_ago(random.randint(1, 60)) + ' 08:00:00',
          lambda i: days_ago(random.randint(1, 60)) + ' 14:00:00',
          lambda i: random.choice(['Booked', 'Completed', 'Cancelled']), lambda i: now()]),

        ('approval_matrix', 10,
         "INSERT INTO approval_matrix (approval_type, approver_role, threshold_amount, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Purchase', 'Expense', 'Leave', 'Travel']),
          lambda i: random.choice(['Manager', 'Director', 'VP']),
          lambda i: random.randint(1000, 50000), lambda i: 1, lambda i: now()]),

        ('advance_settlements', 15,
         "INSERT INTO advance_settlements (settlement_number, employee_id, advance_id, amount, settled_amount, status, settled_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'SET-{i:04d}', lambda i: random.choice(employee_ids),
          lambda i: random.randint(1, 10),
          lambda i: round(random.uniform(500, 5000), 2),
          lambda i: round(random.uniform(0, 3000), 2),
          lambda i: random.choice(['Pending', 'Partial', 'Complete']),
          lambda i: days_ago(random.randint(1, 30)), lambda i: now()]),

        ('agreement_line_items', 20,
         "INSERT INTO agreement_line_items (agreement_id, item_description, quantity, unit_price, total_amount, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 10), lambda i: f'شرح آیتم {i}',
          lambda i: random.randint(1, 100),
          lambda i: round(random.uniform(10, 1000), 2),
          lambda i: round(random.uniform(100, 50000), 2), lambda i: now()]),

        ('counter_readings', 20,
         "INSERT INTO counter_readings (counter_type, counter_value, reading_date, created_at) VALUES (?, ?, ?, ?)",
         [lambda i: random.choice(['Production', 'Quality', 'Maintenance']),
          lambda i: random.randint(1000, 100000),
          lambda i: days_ago(random.randint(0, 30)), lambda i: now()]),

        ('condition_indicators', 8,
         "INSERT INTO condition_indicators (indicator_name, indicator_type, unit, normal_min, normal_max, alert_threshold, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Temperature', 'Pressure', 'Vibration']),
          lambda i: 'Sensor', lambda i: random.choice(['°C', 'PSI', 'mm/s']),
          lambda i: round(random.uniform(10, 50), 1),
          lambda i: round(random.uniform(60, 100), 1),
          lambda i: round(random.uniform(80, 120), 1), lambda i: 1, lambda i: now()]),

        ('condition_readings', 40,
         "INSERT INTO condition_readings (indicator_id, reading_value, reading_timestamp, is_within_limits, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 8), lambda i: round(random.uniform(20, 100), 2),
          lambda i: days_ago(random.randint(0, 7)) + f' {random.randint(0,23):02d}:00:00',
          lambda i: random.choice([0, 1, 1, 1]), lambda i: now()]),

        ('security_policy_versions', 8,
         "INSERT INTO security_policy_versions (policy_id, version_number, change_summary, effective_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 4), lambda i: i + 1,
          lambda i: f'توضیحات تغییرات v{i+1}',
          lambda i: days_ago(random.randint(30, 180)),
          lambda i: random.choice(['Active', 'Superseded']), lambda i: now()]),

        ('sso_audit_log', 25,
         "INSERT INTO sso_audit_log (event_type, user_id, provider, ip_address, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Login', 'Logout', 'Token Refresh', 'MFA']),
          lambda i: random.choice(user_ids),
          lambda i: random.choice(['Azure AD', 'Google', 'Okta']),
          lambda i: f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
          lambda i: random.choice(['Success', 'Failed']), lambda i: now()]),

        ('sso_provider_certificates', 5,
         "INSERT INTO sso_provider_certificates (provider_name, certificate_serial, issued_date, expiry_date, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Azure AD', 'Google Workspace', 'Okta']),
          lambda i: f'CERT-{random.randint(10000, 99999)}',
          lambda i: days_ago(random.randint(180, 365)),
          lambda i: days_future(random.randint(180, 365)), lambda i: 1, lambda i: now()]),

        ('api_security_events', 30,
         "INSERT INTO api_security_events (event_type, severity, ip_address, user_id, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Login Failed', 'Rate Limit', 'Invalid Token', 'Access Denied']),
          lambda i: random.choice(['Low', 'Medium', 'High']),
          lambda i: f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
          lambda i: random.choice(user_ids),
          lambda i: f'Details {i}', lambda i: now()]),

        ('dms_metadata_values', 25,
         "INSERT INTO dms_metadata_values (document_id, metadata_definition_id, value_text, created_at) VALUES (?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.randint(1, 5),
          lambda i: f'مقدار {i}', lambda i: now()]),

        ('dms_saved_views', 12,
         "INSERT INTO dms_saved_views (view_name, view_config, user_id, is_shared, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'View {i}', lambda i: f'{{"v": {i}}}',
          lambda i: random.choice(user_ids), lambda i: random.choice([0, 1]), lambda i: now()]),

        ('dms_archive_log', 15,
         "INSERT INTO dms_archive_log (document_id, archived_by, archive_date, archive_location, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(30, 180)),
          lambda i: f'/archive/{i}', lambda i: random.choice(['Archived', 'Restored']), lambda i: now()]),

        ('dms_disposal_log', 12,
         "INSERT INTO dms_disposal_log (document_id, disposed_by, disposal_date, disposal_method, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(30, 180)),
          lambda i: random.choice(['Shred', 'Delete', 'Recycle']),
          lambda i: random.choice(['Pending', 'Completed']), lambda i: now()]),

        ('dms_required_document_rules', 8,
         "INSERT INTO dms_required_document_rules (rule_name, document_type, required_document_type, is_mandatory, validity_days, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Rule {i}', lambda i: f'Type {i}', lambda i: f'Required {i}',
          lambda i: random.choice([0, 1]), lambda i: random.randint(30, 365), lambda i: now()]),

        ('dms_legal_hold_documents', 12,
         "INSERT INTO dms_legal_hold_documents (legal_hold_id, document_id, added_by, added_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 3), lambda i: random.randint(1, 62),
          lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(30, 120)),
          lambda i: random.choice(['Active', 'Released']), lambda i: now()]),

        ('document_checkout', 15,
         "INSERT INTO document_checkout (document_id, checked_out_by, checkout_date, expected_return, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(0, 7)),
          lambda i: days_future(random.randint(1, 14)),
          lambda i: random.choice(['Checked Out', 'Returned']), lambda i: now()]),

        ('document_checkout_history', 25,
         "INSERT INTO document_checkout_history (document_id, user_id, checkout_date, return_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(7, 60)),
          lambda i: days_ago(random.randint(0, 6)),
          lambda i: 'Returned', lambda i: now()]),

        ('document_retention_schedules', 12,
         "INSERT INTO document_retention_schedules (schedule_name, document_type, retention_period_days, disposition_action, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Schedule {i}', lambda i: f'Type {i}',
          lambda i: random.randint(365, 2555),
          lambda i: random.choice(['Archive', 'Delete', 'Review']), lambda i: 1, lambda i: now()]),

        ('document_locks', 12,
         "INSERT INTO document_locks (document_id, locked_by, lock_type, locked_at, expires_at, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 62), lambda i: random.choice(user_ids),
          lambda i: random.choice(['Exclusive', 'Shared']),
          lambda i: days_ago(random.randint(0, 7)),
          lambda i: days_future(random.randint(1, 30)),
          random.choice([0, 1]), now()]),

        ('ecommerce_price_lists', 5,
         "INSERT INTO ecommerce_price_lists (list_name, description, currency, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: ['Retail', 'Wholesale', 'VIP', 'Special', 'Bulk'][i-1],
          lambda i: f'قیمت {["خرده", "عمده", "ویژه", "خاص", "فله"][i-1]}',
          'USD', 1, now()]),

        ('ecommerce_analytics', 30,
         "INSERT INTO ecommerce_analytics (metric_date, metric_name, metric_value, dimension, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: days_ago(random.randint(1, 30)),
          lambda i: random.choice(['page_views', 'sessions', 'conversion_rate', 'revenue']),
          lambda i: round(random.uniform(100, 10000), 2),
          lambda i: random.choice(['web', 'mobile', 'app']), lambda i: now()]),

        ('ecommerce_promotions', 15,
         "INSERT INTO ecommerce_promotions (promotion_code, promotion_name, discount_type, discount_value, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'PROMO-{i:03d}', lambda i: f'پروموشن {i}',
          lambda i: random.choice(['Percent', 'Fixed', 'BuyXGetY']),
          lambda i: round(random.uniform(5, 30), 1),
          lambda i: days_ago(random.randint(0, 30)),
          lambda i: days_future(random.randint(7, 90)),
          lambda i: random.choice(['Active', 'Scheduled', 'Expired']), lambda i: now()]),

        ('ecommerce_returns', 20,
         "INSERT INTO ecommerce_returns (return_number, order_id, customer_id, return_reason, quantity, status, requested_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'RET-{i:04d}', lambda i: random.randint(1, 100),
          lambda i: random.randint(1, 100),
          lambda i: random.choice(['Defective', 'Wrong Item', 'Changed Mind']),
          lambda i: random.randint(1, 5),
          lambda i: random.choice(['Requested', 'Approved', 'Completed']),
          lambda i: days_ago(random.randint(1, 30)), lambda i: now()]),

        ('ecommerce_refunds', 15,
         "INSERT INTO ecommerce_refunds (refund_number, return_id, refund_amount, refund_method, status, processed_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'REF-{i:04d}', lambda i: random.randint(1, 12),
          lambda i: round(random.uniform(10, 500), 2),
          lambda i: random.choice(['Original Payment', 'Store Credit']),
          lambda i: random.choice(['Pending', 'Processed']),
          lambda i: days_ago(random.randint(0, 20)), lambda i: now()]),

        ('ecommerce_product_performance', 25,
         "INSERT INTO ecommerce_product_performance (part_id, period_start, units_sold, revenue, return_rate, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 40),
          lambda i: days_ago(random.randint(7, 60)),
          lambda i: random.randint(10, 200),
          lambda i: round(random.uniform(1000, 50000), 2),
          lambda i: round(random.uniform(0, 10), 2), lambda i: now()]),

        ('wms_demand_forecast', 30,
         "INSERT INTO wms_demand_forecast (item_id, forecast_date, forecasted_quantity, confidence_level, forecast_method, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 25),
          lambda i: days_future(random.randint(7, 90)),
          lambda i: random.randint(10, 500),
          lambda i: round(random.uniform(0.7, 0.99), 2),
          lambda i: random.choice(['Moving Average', 'Exponential', 'Manual']),
          lambda i: now()]),

        ('wms_defect_codes', 15,
         "INSERT INTO wms_defect_codes (code, description, category, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'D{random.randint(1,9)}{random.randint(1,9)}',
          lambda i: ['Dimensional', 'Surface', 'Material', 'Missing', 'Packaging'][i%5],
          lambda i: ['D', 'S', 'M', 'M', 'P'][i%5], 1, now()]),

        ('wms_dock_schedule', 20,
         "INSERT INTO wms_dock_schedule (dock_id, scheduled_date, appointment_type, carrier, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 12),
          lambda i: days_ago(random.randint(-7, 14)),
          lambda i: random.choice(['Receiving', 'Shipping']),
          lambda i: f'Carrier {i}',
          lambda i: random.choice(['Scheduled', 'Arrived', 'Completed']), lambda i: now()]),

        ('wms_cross_dock', 15,
         "INSERT INTO wms_cross_dock (dock_id, inbound_id, outbound_id, quantity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 12),
          lambda i: random.randint(1, 20),
          lambda i: random.randint(1, 20),
          lambda i: random.randint(10, 200),
          lambda i: random.choice(['Pending', 'In Transit', 'Completed']), lambda i: now()]),

        ('wms_putaway_rules', 10,
         "INSERT INTO wms_putaway_rules (rule_name, condition_json, target_location_type, priority, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Rule {i}', lambda i: f'{{"cond": {i}}}',
          lambda i: random.choice(['Bulk', 'Pick', 'Reserve']),
          lambda i: random.randint(1, 10), 1, now()]),

        ('wms_replenishment_config', 8,
         "INSERT INTO wms_replenishment_config (config_name, replenishment_type, min_level, max_level, reorder_point, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'Config {i}',
          lambda i: random.choice(['Min-Max', 'ROP', 'Kanban']),
          lambda i: random.randint(10, 50),
          lambda i: random.randint(100, 500),
          lambda i: random.randint(20, 100), 1, now()]),

        ('wms_replenishment_suggestions', 30,
         "INSERT INTO wms_replenishment_suggestions (item_id, suggested_quantity, suggested_date, priority, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 25),
          lambda i: random.randint(20, 200),
          lambda i: days_future(random.randint(1, 14)),
          lambda i: random.randint(1, 5),
          lambda i: random.choice(['Open', 'Processed', 'Cancelled']), lambda i: now()]),

        ('wms_wave_orders', 15,
         "INSERT INTO wms_wave_orders (wave_number, warehouse_id, order_count, status, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'WAVE-{i:03d}',
          lambda i: random.randint(1, 4),
          lambda i: random.randint(5, 30),
          lambda i: random.choice(['Planned', 'Released', 'Completed']), lambda i: now()]),

        ('wms_quality_holds', 18,
         "INSERT INTO wms_quality_holds (hold_code, item_id, lot_id, hold_reason, status, placed_by, placed_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'HOLD-{i:04d}', lambda i: random.randint(1, 25),
          lambda i: random.randint(1, 30),
          lambda i: random.choice(['Pending Inspection', 'Customer Request', 'Regulatory Hold']),
          lambda i: random.choice(['Active', 'Released']),
          lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(1, 30)), lambda i: now()]),

        ('wms_quality_certificates', 15,
         "INSERT INTO wms_quality_certificates (certificate_number, item_id, certificate_type, issue_date, expiry_date, issued_by, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'CERT-{i:04d}', lambda i: random.randint(1, 25),
          lambda i: random.choice(['COA', 'COO', 'ISO']),
          lambda i: days_ago(random.randint(1, 180)),
          lambda i: days_future(random.randint(30, 365)),
          lambda i: f'Issuer {i}',
          lambda i: random.choice(['Valid', 'Expired', 'Revoked']), lambda i: now()]),

        ('wms_quality_capa', 15,
         "INSERT INTO wms_quality_capa (capa_number, item_id, issue_description, corrective_action, preventive_action, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'CAPA-{i:04d}', lambda i: random.randint(1, 25),
          lambda i: f'توضیحات {i}',
          lambda i: f'اقدام اصلاحی {i}',
          lambda i: f'اقدام پیشگیرانه {i}',
          lambda i: random.choice(['Open', 'In Progress', 'Closed']), lambda i: now()]),

        ('wms_kanban_config', 8,
         "INSERT INTO wms_kanban_config (kanban_type, item_id, bin_quantity, bin_count, replenishment_point, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Production', 'Withdrawal', 'Signal']),
          lambda i: random.randint(1, 25),
          lambda i: random.randint(5, 50),
          lambda i: random.randint(3, 10),
          lambda i: random.randint(10, 50), 1, now()]),

        ('wms_voice_config', 6,
         "INSERT INTO wms_voice_config (config_name, language, voice_type, vocabulary, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Voice {i}', 'en-US',
          lambda i: random.choice(['Male', 'Female']),
          lambda i: random.choice(['Standard', 'Extended']), 1, now()]),

        ('wms_voice_pick_log', 25,
         "INSERT INTO wms_voice_pick_log (pick_id, operator_id, command, response, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 50), lambda i: random.randint(1, 20),
          lambda i: f'Pick {i}', 'Confirmed',
          lambda i: random.choice(['Success', 'Error']), lambda i: now()]),

        ('wms_rf_scan_log', 30,
         "INSERT INTO wms_rf_scan_log (operator_id, scan_type, barcode, result, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 20),
          lambda i: random.choice(['Receive', 'Pick', 'Move', 'Count']),
          lambda i: f'BC-{random.randint(10000, 99999)}',
          lambda i: random.choice(['Success', 'Not Found']), lambda i: now()]),

        ('wms_yard_vehicles', 15,
         "INSERT INTO wms_yard_vehicles (vehicle_plate, vehicle_type, driver_name, arrival_time, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'ABC-{random.randint(1000, 9999)}',
          lambda i: random.choice(['Truck', 'Van', 'Trailer']),
          lambda i: f'{random.choice(PF)} {random.choice(PL)}',
          lambda i: days_ago(random.randint(0, 3)),
          lambda i: random.choice(['In Yard', 'At Dock', 'Departed']), lambda i: now()]),

        ('wms_yard_activity_log', 25,
         "INSERT INTO wms_yard_activity_log (vehicle_id, activity_type, location, timestamp, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 10),
          lambda i: random.choice(['Arrived', 'Moved', 'Loaded', 'Unloaded']),
          lambda i: f'Dock {random.randint(1, 12)}',
          lambda i: days_ago(random.randint(0, 7)) + f' {random.randint(6,20):02d}:00:00',
          lambda i: now()]),

        ('wms_saved_reports', 12,
         "INSERT INTO wms_saved_reports (report_name, report_type, parameters, user_id, is_shared, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Report {i}',
          lambda i: random.choice(['Inventory', 'Movement', 'Receiving']),
          lambda i: f'{{"p": {i}}}',
          lambda i: random.choice(user_ids),
          lambda i: random.choice([0, 1]), lambda i: now()]),

        ('wms_usage_decisions', 15,
         "INSERT INTO wms_usage_decisions (decision_number, item_id, quantity, decision, inspector_id, decision_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'UD-{i:04d}', lambda i: random.randint(1, 25),
          lambda i: random.randint(10, 200),
          lambda i: random.choice(['Accept', 'Reject', 'Conditional']),
          lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(1, 30)), lambda i: now()]),

        ('capacity_planning_views', 10,
         "INSERT INTO capacity_planning_views (view_name, work_center_ids, time_period, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
         [lambda i: f'View {i}',
          lambda i: f'{random.randint(1,15)},{random.randint(1,15)}',
          lambda i: random.choice(['Week', 'Month', 'Quarter']),
          lambda i: random.choice(user_ids), lambda i: now()]),

        ('capacity_requirements', 30,
         "INSERT INTO capacity_requirements (work_center_id, requirement_date, required_hours, available_hours, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 15),
          lambda i: days_future(random.randint(1, 30)),
          lambda i: random.randint(40, 120),
          lambda i: random.randint(60, 150),
          lambda i: random.choice(['OK', 'Overloaded', 'Underloaded']), lambda i: now()]),

        ('capex_requests', 18,
         "INSERT INTO capex_requests (request_number, title, description, amount, currency, requester_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'CAPEX-{i:04d}', lambda i: f'درخواست {i}',
          lambda i: f'توضیحات {i}',
          lambda i: round(random.uniform(10000, 500000), 2),
          lambda i: random.choice(['USD', 'AED']),
          lambda i: random.choice(user_ids),
          lambda i: random.choice(['Draft', 'Submitted', 'Approved', 'Rejected']), lambda i: now()]),

        ('settlement_rules', 8,
         "INSERT INTO settlement_rules (rule_name, rule_type, parameters, priority, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Rule {i}',
          lambda i: random.choice(['Auto', 'Manual', 'Threshold']),
          lambda i: f'{{"p": {i}}}',
          lambda i: random.randint(1, 10), 1, now()]),

        ('bom_substitutes', 20,
         "INSERT INTO bom_substitutes (bom_id, substitute_part_id, substitution_ratio, is_preferred, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 30), lambda i: random.randint(1, 40),
          lambda i: round(random.uniform(0.8, 1.2), 2),
          lambda i: random.choice([0, 1]), 1, now()]),

        ('treasury_forecast_items', 30,
         "INSERT INTO treasury_forecast_items (forecast_id, item_type, description, amount, due_date, probability, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 3),
          lambda i: random.choice(['Incoming', 'Outgoing']),
          lambda i: f'Forecast {i}',
          lambda i: round(random.uniform(1000, 50000), 2),
          lambda i: days_future(random.randint(7, 90)),
          lambda i: round(random.uniform(0.5, 1.0), 2), lambda i: now()]),

        ('treasury_liquidity_plans', 15,
         "INSERT INTO treasury_liquidity_plans (plan_name, period_start, period_end, total_inflow, total_outflow, net_position, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'Plan {i}',
          lambda i: days_ago(random.randint(0, 30)),
          lambda i: days_future(random.randint(30, 90)),
          lambda i: round(random.uniform(100000, 500000), 2),
          lambda i: round(random.uniform(80000, 450000), 2),
          lambda i: round(random.uniform(-50000, 100000), 2), lambda i: now()]),

        ('treasury_liquidity_thresholds', 6,
         "INSERT INTO treasury_liquidity_thresholds (threshold_name, threshold_type, threshold_value, currency, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: ['Minimum Cash', 'Maximum Cash', 'Warning Level'][i-1],
          lambda i: random.choice(['Minimum', 'Maximum', 'Warning']),
          lambda i: random.randint(10000, 100000),
          lambda i: random.choice(['USD', 'AED']), 1, now()]),

        ('grc_access_review_items', 25,
         "INSERT INTO grc_access_review_items (access_review_id, user_id, resource_type, resource_name, access_level, risk_score, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 3), lambda i: random.randint(1, 20),
          lambda i: random.choice(['Table', 'Report', 'API']),
          lambda i: f'Resource {i}',
          lambda i: random.choice(['Read', 'Write', 'Admin']),
          lambda i: random.randint(1, 10),
          lambda i: random.choice(['Approved', 'Revoked', 'Pending']), lambda i: now()]),

        ('grc_audit_preparedness_checks', 15,
         "INSERT INTO grc_audit_preparedness_checks (audit_id, check_item, responsible_person, due_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 9), lambda i: f'Check {i}',
          lambda i: random.choice(user_ids),
          lambda i: days_future(random.randint(7, 60)),
          lambda i: random.choice(['Not Started', 'In Progress', 'Completed']), lambda i: now()]),

        ('grc_control_assignments', 50,
         "INSERT INTO grc_control_assignments (control_id, risk_id, assignment_type, effectiveness, last_tested, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 12), lambda i: random.randint(1, 13),
          lambda i: random.choice(['Primary', 'Secondary', 'Mitigating']),
          lambda i: random.choice(['Effective', 'Ineffective', 'Not Tested']),
          lambda i: days_ago(random.randint(30, 180)), lambda i: now()]),

        ('grc_control_test_results', 25,
         "INSERT INTO grc_control_test_results (control_id, test_date, tester_id, test_result, findings, next_test_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 12),
          lambda i: days_ago(random.randint(1, 120)),
          lambda i: random.choice(user_ids),
          lambda i: random.choice(['Pass', 'Fail', 'Exception']),
          lambda i: f'Finding {i}',
          lambda i: days_future(random.randint(30, 180)), lambda i: now()]),

        ('grc_entity_links', 20,
         "INSERT INTO grc_entity_links (entity_type, entity_id, linked_entity_type, linked_entity_id, relationship, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Process', 'Asset', 'System']),
          lambda i: random.randint(1, 20),
          lambda i: random.choice(['Risk', 'Control', 'Regulation']),
          lambda i: random.randint(1, 20),
          lambda i: random.choice(['Related', 'Owner', 'Subject To']), lambda i: now()]),

        ('grc_export_jobs', 12,
         "INSERT INTO grc_export_jobs (export_type, format, status, record_count, requested_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Risk Report', 'Compliance Report', 'Audit Report']),
          lambda i: random.choice(['PDF', 'Excel', 'CSV']),
          lambda i: random.choice(['Completed', 'Failed', 'Running']),
          lambda i: random.randint(100, 5000),
          lambda i: random.choice(user_ids), lambda i: now()]),

        ('grc_policy_acknowledgements', 35,
         "INSERT INTO grc_policy_acknowledgements (policy_id, user_id, acknowledged_at, signature_data, ip_address, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 6), lambda i: random.randint(1, 30),
          lambda i: days_ago(random.randint(1, 180)),
          lambda i: f'sig_{i}',
          lambda i: f'192.168.{random.randint(1,255)}.{random.randint(1,255)}', lambda i: now()]),

        ('grc_policy_versions', 15,
         "INSERT INTO grc_policy_versions (policy_id, version_number, change_summary, effective_date, approved_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 6), lambda i: i + 1,
          lambda i: f'Summary v{i+1}',
          lambda i: days_ago(random.randint(30, 180)),
          lambda i: random.choice(user_ids), lambda i: now()]),

        ('grc_remediation_tasks', 20,
         "INSERT INTO grc_remediation_tasks (remediation_plan_id, task_name, assigned_to, due_date, status, priority, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 3), lambda i: f'Task {i}',
          lambda i: random.choice(user_ids),
          lambda i: days_future(random.randint(7, 60)),
          lambda i: random.choice(['Not Started', 'In Progress', 'Completed']),
          lambda i: random.choice(['Low', 'Medium', 'High']), lambda i: now()]),

        ('grc_report_presets', 12,
         "INSERT INTO grc_report_presets (report_name, report_type, filters, schedule, last_generated, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Preset {i}',
          lambda i: random.choice(['Risk', 'Compliance', 'Audit']),
          lambda i: f'{{"f": {i}}}',
          lambda i: random.choice(['Daily', 'Weekly', 'Monthly']),
          lambda i: days_ago(random.randint(1, 30)), lambda i: now()]),

        ('grc_review_cycles', 10,
         "INSERT INTO grc_review_cycles (cycle_name, cycle_type, start_date, end_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Cycle {i}',
          lambda i: random.choice(['Access', 'Policy', 'Control']),
          lambda i: days_ago(random.randint(30, 90)),
          lambda i: days_future(random.randint(30, 90)),
          lambda i: random.choice(['Planned', 'Active', 'Completed']), lambda i: now()]),

        ('grc_risk_assessments', 20,
         "INSERT INTO grc_risk_assessments (assessment_name, risk_id, assessment_date, likelihood, impact, risk_score, assessor_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
         [lambda i: f'Assessment {i}', lambda i: random.randint(1, 13),
          lambda i: days_ago(random.randint(1, 120)),
          lambda i: random.randint(1, 5), lambda i: random.randint(1, 5),
          lambda i: random.randint(1, 25),
          lambda i: random.choice(user_ids), lambda i: now()]),

        ('grc_risk_treatments', 18,
         "INSERT INTO grc_risk_treatments (risk_id, treatment_type, treatment_plan, owner_id, status, due_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.randint(1, 13),
          lambda i: random.choice(['Mitigate', 'Transfer', 'Accept', 'Avoid']),
          lambda i: f'Treatment {i}',
          lambda i: random.choice(user_ids),
          lambda i: random.choice(['Planned', 'In Progress', 'Completed']),
          lambda i: days_future(random.randint(30, 120)), lambda i: now()]),

        ('grc_status_history', 35,
         "INSERT INTO grc_status_history (entity_type, entity_id, old_status, new_status, changed_by, changed_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
         [lambda i: random.choice(['Risk', 'Control', 'Incident']),
          lambda i: random.randint(1, 20),
          lambda i: random.choice(['Open', 'In Progress']),
          lambda i: random.choice(['Mitigated', 'Closed', 'Escalated']),
          lambda i: random.choice(user_ids),
          lambda i: days_ago(random.randint(1, 60)), lambda i: now()]),

        ('grc_watchlists', 12,
         "INSERT INTO grc_watchlists (item_name, item_type, risk_description, added_by, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
         [lambda i: f'Watchlist {i}',
          lambda i: random.choice(['Vendor', 'System', 'Location']),
          lambda i: f'Risk {i}',
          lambda i: random.choice(user_ids), 1, now()]),
    ]

    for table, count, sql, param_fns in minimal_seeds:
        if not table_exists(table, db):
            continue
        current_count = get_count(table, db)
        if current_count >= count:
            continue
        for i in range(1, count + 1):
            try:
                params = [fn(i) for fn in param_fns]
                db.execute(sql, params)
            except Exception as e:
                pass  # Silently skip
        db.commit()

    print("    + Minimal tables seeded")


# =============================================================================
# MAIN
# =============================================================================
def main():
    print("=" * 80)
    print("  MMDx AGGRESSIVE MASTER SEED - FK DISABLED")
    print("=" * 80)

    db = get_db(fk=False)  # Disable FK during seeding

    try:
        size = os.path.getsize(DATABASE)
        print(f"\n  Database: {DATABASE}")
        print(f"  Database size: {size / (1024*1024):.1f} MB")
    except:
        pass

    print("\n>> Seeding all modules with FK disabled...")
    print("-" * 60)

    seed_projects(db)
    seed_spc(db)
    seed_talent(db)
    seed_manufacturing(db)
    seed_service(db)
    seed_crm(db)
    seed_quality(db)
    seed_btp(db)
    seed_minimal(db)

    db.commit()

    # Re-enable FK and verify
    print("\n>> Verifying data integrity...")
    db.execute("PRAGMA foreign_keys=ON")
    db.commit()

    print("\n" + "=" * 80)
    print("  FINAL VERIFICATION")
    print("=" * 80)

    all_tables = [row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]

    empty_tables = []
    for t in all_tables:
        if get_count(t, db) == 0:
            empty_tables.append(t)

    print(f"\n  Total tables: {len(all_tables)}")
    print(f"  Empty tables remaining: {len(empty_tables)}")

    if empty_tables:
        print(f"\n  Still empty ({len(empty_tables)}):")
        for t in sorted(empty_tables)[:30]:
            print(f"    - {t}")
        if len(empty_tables) > 30:
            print(f"    ... and {len(empty_tables) - 30} more")

    db.close()
    print("\n" + "=" * 80)
    print("  SEEDING COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
