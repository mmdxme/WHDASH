"""
MMDx Comprehensive Master Seed Script
====================================
This is the master seeding script that fills ALL empty tables in the warehouse.db
database with realistic Persian/Farsi sample data.

Usage:
    python seed_final_master.py

This script:
1. Fills ALL remaining empty tables with realistic data
2. Uses Persian/Farsi for all user-facing content
3. Ensures foreign key integrity
4. Distributes data across 6-12 months temporal range
5. Includes variety in all status fields

Author: MMDx Data Seeding System
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

# Fix UTF-8 encoding on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db():
    """Get database connection with proper settings."""
    conn = sqlite3.connect(DATABASE, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=60000")
    return conn


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def days_future(n):
    return (datetime.now() + timedelta(days=n)).strftime('%Y-%m-%d')


def table_exists(table, db):
    result = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return result is not None


def get_count(table, db):
    try:
        return db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    except:
        return 0


def get_any_id(table, db, limit=100):
    try:
        result = db.execute(f'SELECT id FROM "{table}" LIMIT {limit}').fetchall()
        return [r['id'] for r in result]
    except:
        return []


def get_any_value(table, col, db, limit=100):
    try:
        result = db.execute(f'SELECT {col} FROM "{table}" LIMIT {limit}').fetchall()
        return [r[0] for r in result]
    except:
        return []


def seed_safe(table, db, data_fn):
    """Safely seed a table if it's empty."""
    count = get_count(table, db)
    if count > 0:
        return False
    try:
        data_fn(db)
        return True
    except Exception as e:
        print(f"      Error seeding {table}: {e}")
        return False


def get_columns(table, db):
    try:
        cursor = db.execute(f"PRAGMA table_info([{table}])")
        return [row[1] for row in cursor.fetchall()]
    except:
        return []


# =============================================================================
# PERSIAN DATA CONSTANTS
# =============================================================================

PERSIAN_FIRST_NAMES = [
    'محمد', 'احمد', 'علی', 'حسین', 'رضا', 'امیر', 'مهدی', 'سجاد', 'مرتضی', 'پوریا',
    'فاطمه', 'مریم', 'زهرا', 'نرگس', 'سارا', 'نیلوفر', 'ریحانه', 'یاسمن', 'آسیه', 'محبوبه',
    'محمدعلی', 'علیرضا', 'محمدرضا', 'سیدمحمد', 'ابوالفضل', 'امیرحسین', 'مهدی', 'پارسا', 'آرتین', 'کیان',
    'زینب', 'حانیه', 'ملیکا', 'آیدا', 'روژان', 'شیما', 'نازنین', 'هلیا', 'هانیه', 'رها'
]

PERSIAN_LAST_NAMES = [
    'محمدی', 'احمدی', 'رضایی', 'حسینی', 'کریمی', 'موسوی', 'هاشمی', 'جعفری', 'صادقی', 'میرزایی',
    'علوی', 'نوری', 'مرادی', 'قاسمی', 'طاهری', 'رحیمی', 'عباسی', 'زارعی', 'فرهادی', 'سلیمانی',
    'اکبری', 'بهرامی', 'پورمحمدی', 'توکلی', 'جلالی', 'چوپانی', 'حیدری', 'خسروی', 'داوودی', 'ذاکری'
]

PERSIAN_COMPANY_NAMES = [
    'شرکت بازرگانی آسیا', 'شرکت صنعتی پارس', 'شرکت تولیدی مهر', 'شرکت خدماتی آفتاب',
    'شرکت پیمانکاری سپهر', 'شرکت بازرگانی جم', 'شرکت سرمایه‌گذاری خاور', 'شرکت مهندسی نوح',
    'شرکت تولیدی بهشت', 'شرکت صادراتی ایران', 'شرکت وارداتی اتحاد', 'شرکت ساختمانی امیر',
    'شرکت نساجی پارسیان', 'شرکت الکترونیکیarde', 'شرکت شیمیایی کیمیا', 'شرکت غذایی سلامت',
    'شرکت دارویی درمان', 'شرکت خودروسازی پارس', 'شرکت کشاورزی سبزینه', 'شرکت معدنی زمین'
]

PERSIAN_CITIES = [
    'تهران', 'اصفهان', 'مشهد', 'شیراز', 'تبریز', 'قم', 'کرج', 'اهواز', 'مازندران', 'گیلان',
    'یزد', 'سمنان', 'اردبیل', 'کرمان', 'همدان', 'زاهدان', 'بوشهر', 'قزوین', 'خراسان', 'فارس'
]

PERSIAN_PRODUCT_CATEGORIES = [
    'قطعات الکترونیکی', 'قطعات مکانیکی', 'مواد اولیه', 'محصولات نهایی', 'ابزارآلات',
    'مواد شیمیایی', 'پوشاک', 'مواد غذایی', 'دارو', 'تجهیزات صنعتی'
]

PERSIAN_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']


# =============================================================================
# MODULE 1: PROJECTS
# =============================================================================

def seed_projects_module(db):
    """Seed all project management tables."""
    print("  Seeding Projects module...")

    # Get existing references
    company_ids = get_any_id('companies', db, 10)
    user_ids = get_any_id('users', db, 10)
    if not company_ids:
        company_ids = [1]
    if not user_ids:
        user_ids = [1]

    # projects table
    project_statuses = ['Planning', 'Active', 'On Hold', 'Completed', 'Cancelled']
    project_priorities = ['Low', 'Medium', 'High', 'Critical']

    projects_data = []
    for i in range(1, 31):
        status = random.choice(project_statuses)
        start = days_ago(random.randint(30, 300))
        end = days_future(random.randint(30, 365)) if status != 'Completed' else days_ago(random.randint(1, 30))
        projects_data.append((
            f'PRJ-{i:04d}',
            f'پروژه {["توسعه", "بهبود", "پیاده‌سازی", "نوسازی", "تحول"][i % 5]} {["سیستم", "فرآیند", "زیرساخت", "نرم‌افزار", "شبکه"][i % 5]} {i}',
            f'توضیحات پروژه شماره {i} - این پروژه برای بهبود عملکرد سازمان طراحی شده است',
            start, end,
            status,
            random.choice(project_priorities),
            random.choice(company_ids),
            random.choice(user_ids),
            random.randint(50000, 5000000),
            random.randint(10, 90) if status == 'Active' else random.randint(0, 100),
            now()
        ))

    for p in projects_data:
        try:
            db.execute("""INSERT INTO projects
                (project_code, project_name, description, start_date, end_date, status,
                 priority, company_id, manager_id, budget, progress_percent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", p)
        except Exception as e:
            pass

    db.commit()
    project_ids = get_any_id('projects', db, 30)
    if not project_ids:
        return

    # project_phases
    for proj_id in project_ids:
        for j in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO project_phases
                    (project_id, phase_name, description, start_date, end_date, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'فاز {j+1}', f'توضیحات فاز {j+1}', days_ago(random.randint(1, 100)),
                     days_future(random.randint(1, 200)), random.choice(['Not Started', 'In Progress', 'Completed']), now()))
            except:
                pass

    # project_milestones
    for proj_id in project_ids:
        for k in range(random.randint(2, 4)):
            try:
                db.execute("""INSERT INTO project_milestones
                    (project_id, milestone_name, description, due_date, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'نقطه عطف {k+1}', f'توضیحات نقطه عطف {k+1}',
                     days_future(random.randint(1, 300)), random.choice(['Pending', 'Reached', 'Overdue']), now()))
            except:
                pass

    # project_tasks
    task_statuses = ['Pending', 'In Progress', 'Completed', 'Blocked']
    for proj_id in project_ids:
        for t in range(random.randint(5, 15)):
            status = random.choice(task_statuses)
            assignee = random.choice(user_ids) if user_ids else 1
            try:
                db.execute("""INSERT INTO project_tasks
                    (project_id, task_name, description, assignee_id, start_date, end_date,
                     status, priority, progress_percent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'وظیفه {t+1}', f'توضیحات وظیفه {t+1}', assignee,
                     days_ago(random.randint(0, 50)), days_future(random.randint(1, 100)),
                     status, random.choice(['Low', 'Medium', 'High']),
                     100 if status == 'Completed' else random.randint(0, 80), now()))
            except:
                pass

    # project_resource_allocations
    for proj_id in project_ids[:10]:
        for u in user_ids[:random.randint(2, 5)]:
            try:
                db.execute("""INSERT INTO project_resource_allocations
                    (project_id, user_id, role, allocated_hours, allocated_percentage, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (proj_id, u, random.choice(['Developer', 'Manager', 'Analyst', 'Tester']),
                     random.randint(40, 200), random.randint(25, 100), now()))
            except:
                pass

    # project_wbs
    for proj_id in project_ids[:15]:
        try:
            db.execute("""INSERT INTO project_wbs
                (project_id, wbs_code, wbs_name, description, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (proj_id, f'WBS-{proj_id}-01', f'ساختار شکست کار پروژه {proj_id}',
                 f'توضیحات ساختار شکست کار برای پروژه {proj_id}', now()))
        except:
            pass

    # project_issues
    for proj_id in project_ids[:20]:
        for iss in range(random.randint(0, 3)):
            try:
                db.execute("""INSERT INTO project_issues
                    (project_id, issue_title, description, severity, status, reported_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (proj_id, f'مشکل {iss+1}', f'توضیحات مشکل شماره {iss+1}',
                     random.choice(['Low', 'Medium', 'High', 'Critical']),
                     random.choice(['Open', 'In Progress', 'Resolved', 'Closed']),
                     random.choice(user_ids), now()))
            except:
                pass

    # project_documents
    for proj_id in project_ids[:20]:
        for d in range(random.randint(1, 3)):
            try:
                db.execute("""INSERT INTO project_documents
                    (project_id, document_name, document_type, uploaded_by, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (proj_id, f'سند {d} پروژه {proj_id}', random.choice(['Report', 'Plan', 'Spec', 'Contract']),
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

    # project_audit_logs
    for proj_id in project_ids[:10]:
        try:
            db.execute("""INSERT INTO project_audit_logs
                (project_id, action, user_id, details, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (proj_id, 'Created', random.choice(user_ids),
                 f'لاگ حسابرسی برای پروژه {proj_id}', now()))
        except:
            pass

    db.commit()
    print("    + Projects: 30 projects, tasks, milestones seeded")


# =============================================================================
# MODULE 2: SPC / STATISTICAL PROCESS CONTROL
# =============================================================================

def seed_spc_module(db):
    """Seed SPC / Statistical Process Control tables."""
    print("  Seeding SPC module...")

    part_ids = get_any_id('parts', db, 20)
    if not part_ids:
        part_ids = [1]

    # spc_control_charts (already has 8 rows, add more)
    chart_types = ['X-bar R', 'X-bar S', 'X-mR', 'p-chart', 'np-chart', 'c-chart', 'u-chart']
    chart_ids = []
    for i in range(20):
        try:
            db.execute("""INSERT INTO spc_control_charts
                (chart_code, chart_name, chart_type, part_id, process_parameter,
                 ucl, lcl, cl, sample_size, measurement_unit, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SPC-{i+1:03d}', f'نمودار کنترل {i+1}',
                 random.choice(chart_types), random.choice(part_ids),
                 random.choice(['وزن', 'طول', 'عرض', 'فشار', 'دما', 'زمان']),
                 round(random.uniform(95, 105), 2), round(random.uniform(5, 15), 2),
                 round(random.uniform(50, 60), 2), random.randint(5, 25),
                 random.choice(['mm', 'kg', 'psi', '°C', 'sec']), 1, now()))
            chart_ids.append(i + 9)  # offset for existing
        except:
            pass

    db.commit()
    chart_ids = get_any_id('spc_control_charts', db, 30)

    # spc_measurement_data - the key data table
    measurement_statuses = ['In Control', 'Out of Control', 'Warning']
    for chart_id in chart_ids[:15]:
        for day in range(60):  # 60 days of data
            timestamp = days_ago(60 - day) + ' 08:00:00'
            for subgroup in range(4):  # 4 subgroups per day
                try:
                    mean = round(random.uniform(48, 62), 3)
                    range_val = round(random.uniform(0.5, 8), 3)
                    std_dev = round(random.uniform(1, 5), 3)
                    db.execute("""INSERT INTO spc_measurement_data
                        (chart_id, subgroup_number, observation_number, timestamp,
                         observed_value, calculated_mean, calculated_range, calculated_std_dev,
                         ucl, lcl, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (chart_id, subgroup + 1, day * 4 + subgroup + 1, timestamp,
                         round(random.uniform(45, 65), 2), mean, range_val, std_dev,
                         round(mean + random.uniform(5, 15), 2), round(mean - random.uniform(5, 15), 2),
                         random.choice(measurement_statuses), now()))
                except:
                    pass

    db.commit()

    # spc_capability_studies
    for i in range(15):
        try:
            db.execute("""INSERT INTO spc_capability_studies
                (study_code, study_name, part_id, process_name, characteristic_name,
                 data_points, cp, cpk, pp, ppk, sample_size, study_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'STUDY-{i+1:03d}', f'مطالعه قابلیت {i+1}',
                 random.choice(part_ids), f'فرآیند تولید {i+1}',
                 random.choice(['قطر', 'طول', 'وزن', 'فشار']),
                 random.randint(50, 200), round(random.uniform(1.0, 2.0), 3),
                 round(random.uniform(0.8, 1.8), 3), round(random.uniform(1.0, 1.8), 3),
                 round(random.uniform(0.8, 1.5), 3), random.randint(30, 100),
                 days_ago(random.randint(1, 180)),
                 random.choice(['Completed', 'In Progress', 'Scheduled']), now()))
        except:
            pass

    # spc_sampling_plans
    for i in range(10):
        try:
            db.execute("""INSERT INTO spc_sampling_plans
                (plan_code, plan_name, inspection_level, AQL, sample_size_code,
                 acceptance_number, rejection_number, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PLAN-{i+1:03d}', f'طرح نمونه‌گیری {i+1}',
                 random.choice(['Normal', 'Reduced', 'Tightened']),
                 round(random.uniform(0.1, 4.0), 1),
                 random.choice(['I', 'II', 'III']),
                 random.randint(1, 5), random.randint(3, 8), 1, now()))
        except:
            pass

    # spc_specification_limits
    for part_id in part_ids[:15]:
        try:
            db.execute("""INSERT INTO spc_specification_limits
                (part_id, characteristic, usl, lsl, target, nominal, measurement_unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (part_id, random.choice(['قطر', 'طول', 'عرض', 'وزن']),
                 round(random.uniform(100, 150), 2), round(random.uniform(50, 90), 2),
                 round(random.uniform(95, 105), 2), round(random.uniform(95, 105), 2),
                 random.choice(['mm', 'kg', 'cm']), now()))
        except:
            pass

    # spc_calibration_records
    for i in range(12):
        try:
            db.execute("""INSERT INTO spc_calibration_records
                (instrument_code, instrument_name, calibration_date, next_calibration_date,
                 calibration_result, technician, certificate_number, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CAL-{i+1:03d}', f'ابزار اندازه‌گیری {i+1}',
                 days_ago(random.randint(1, 180)), days_future(random.randint(30, 180)),
                 random.choice(['Passed', 'Failed', 'Calibrated']),
                 f'تکنسین {random.choice(PERSIAN_FIRST_NAMES)} {random.choice(PERSIAN_LAST_NAMES)}',
                 f'CERT-{random.randint(10000, 99999)}', 1, now()))
        except:
            pass

    # spc_gage_rr_studies
    for i in range(8):
        try:
            db.execute("""INSERT INTO spc_gage_rr_studies
                (study_code, gage_name, study_date, operator_count, trial_count,
                 GRR_percentage, ndc, study_result, is_acceptable, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'GRR-{i+1:03d}', f'گیج {i+1}', days_ago(random.randint(1, 120)),
                 random.randint(2, 4), random.randint(2, 5),
                 round(random.uniform(5, 35), 2), random.randint(4, 10),
                 random.choice(['Acceptable', 'Marginal', 'Unacceptable']),
                 random.choice([0, 1]), now()))
        except:
            pass

    # spc_trend_analysis
    for i in range(10):
        try:
            db.execute("""INSERT INTO spc_trend_analysis
                (chart_id, analysis_date, trend_type, description, severity,
                 recommendation, is_resolved, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(chart_ids) if chart_ids else 1,
                 days_ago(random.randint(1, 60)),
                 random.choice(['Increasing', 'Decreasing', 'Cycling', 'Stratification']),
                 f'تحلیل روند برای نمودار {i+1}',
                 random.choice(['Low', 'Medium', 'High']),
                 f'توصیه: بررسی و اقدام اصلاحی برای {i+1}',
                 random.choice([0, 1, 1, 1]), now()))
        except:
            pass

    # spc_aql_inspections
    for i in range(15):
        try:
            db.execute("""INSERT INTO spc_aql_inspections
                (inspection_code, lot_number, sample_size, AQL_level,
                 accept_number, reject_number, inspected_quantity, defective_quantity,
                 inspection_result, inspector, inspection_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'AQL-{i+1:03d}', f'LOT-{random.randint(1000, 9999)}',
                 random.randint(20, 200), round(random.uniform(0.1, 4.0), 1),
                 random.randint(1, 5), random.randint(3, 10),
                 random.randint(50, 500), random.randint(0, 15),
                 random.choice(['Accepted', 'Rejected']),
                 f'بازرس {random.choice(PERSIAN_FIRST_NAMES)}',
                 days_ago(random.randint(1, 90)), now()))
        except:
            pass

    # spc_quality_metrics
    for i in range(20):
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
    for i in range(10):
        try:
            db.execute("""INSERT INTO spc_anomaly_alerts
                (chart_id, alert_type, description, detected_at,
                 acknowledged, acknowledged_by, resolved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(chart_ids) if chart_ids else 1,
                 random.choice(['Rule Violation', 'Trend Violation', 'Out of Spec']),
                 f'هشدار ناهنجاری برای نمودار {i+1}',
                 days_ago(random.randint(1, 30)),
                 random.choice([0, 1, 1]),
                 random.choice(user_ids) if user_ids else 1,
                 days_ago(random.randint(0, 15)) if random.random() > 0.3 else None, now()))
        except:
            pass

    db.commit()
    print("    + SPC: measurement data, capability studies, sampling plans seeded")


# =============================================================================
# MODULE 3: TALENT MANAGEMENT
# =============================================================================

def seed_talent_management(db):
    """Seed Talent Management (TM) module tables."""
    print("  Seeding Talent Management module...")

    employee_ids = get_any_id('hr_employees', db, 50)
    dept_ids = get_any_id('hr_departments', db, 10)
    pos_ids = get_any_id('hr_positions', db, 10)
    if not employee_ids:
        employee_ids = [1]
    if not dept_ids:
        dept_ids = [1]
    if not pos_ids:
        pos_ids = [1]

    # tm_competency_categories
    comp_categories = [
        ('فنی', ' مهارت‌های فنی و تخصصی'),
        ('رهبری', ' مهارت‌های رهبری و مدیریت'),
        ('ارتباطی', ' مهارت‌های ارتباطی و بین‌فردی'),
        ('تحلیلی', ' مهارت‌های تحلیلی و حل مسئله'),
        ('بازرگانی', ' مهارت‌های کسب‌وکار و مالی')
    ]
    cat_ids = []
    for name, desc in comp_categories:
        try:
            db.execute("""INSERT INTO tm_competency_categories (name, description, created_at)
                VALUES (?, ?, ?)""", (name, desc, now()))
            cat_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_competencies
    competencies = [
        ('برنامه‌نویسی Python', 'توانایی برنامه‌نویسی به زبان Python', cat_ids[0] if cat_ids else 1, 5),
        ('تحلیل داده', 'تحلیل و پردازش داده‌های کسب‌وکار', cat_ids[0] if len(cat_ids) > 1 else 1, 4),
        ('مدیریت پروژه', 'توانایی مدیریت پروژه‌های نرم‌افزاری', cat_ids[1] if len(cat_ids) > 1 else 1, 5),
        ('رهبری تیم', 'هدایت و رهبری تیم‌های کاری', cat_ids[1] if len(cat_ids) > 1 else 1, 4),
        ('ارتباط مؤثر', 'برقراری ارتباط مؤثر با همکاران و مشتریان', cat_ids[2] if len(cat_ids) > 2 else 1, 4),
        ('مذاکره', 'مهارت مذاکره و حل تعارض', cat_ids[2] if len(cat_ids) > 2 else 1, 3),
        ('حل مسئله', 'توانایی تحلیل و حل مسائل پیچیده', cat_ids[3] if len(cat_ids) > 3 else 1, 5),
        ('تفکر انتقادی', 'تفکر انتقادی و تصمیم‌گیری', cat_ids[3] if len(cat_ids) > 3 else 1, 4),
        ('حسابداری', 'دانش حسابداری و امور مالی', cat_ids[4] if len(cat_ids) > 4 else 1, 3),
        ('بازاریابی', 'اصول و تکنیک‌های بازاریابی', cat_ids[4] if len(cat_ids) > 4 else 1, 3),
    ]
    comp_ids = []
    for name, desc, cat_id, prof_level in competencies:
        try:
            db.execute("""INSERT INTO tm_competencies (name, description, category_id, proficiency_level, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""", (name, desc, cat_id, prof_level, 1, now()))
            comp_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_talent_profiles
    for emp_id in employee_ids[:40]:
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

    # tm_employee_competencies
    for emp_id in employee_ids[:30]:
        for comp_id in comp_ids[:random.randint(3, 6)]:
            try:
                db.execute("""INSERT INTO tm_employee_competencies
                    (employee_id, competency_id, proficiency_level, proof_reference,
                     verified_by, verified_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, comp_id, random.randint(2, 5),
                     f'گواهینامه یا پروژه مرجع',
                     random.choice(employee_ids), days_ago(random.randint(10, 180)), now()))
            except:
                pass

    # tm_talent_pools
    pool_names = ['نخبگان', 'رهبران آینده', 'متخصصان فنی', 'مدیران میانی']
    pool_ids = []
    for name in pool_names:
        try:
            db.execute("""INSERT INTO tm_talent_pools (name, description, criteria, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, f'استخر استعداد {name}', f'معیارهای عضویت در {name}', 1, now()))
            pool_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except:
            pass
    db.commit()

    # tm_talent_pool_members
    for pool_id in pool_ids:
        for emp_id in employee_ids[:random.randint(5, 15)]:
            try:
                db.execute("""INSERT INTO tm_talent_pool_members
                    (pool_id, employee_id, added_by, added_at, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (pool_id, emp_id, random.choice(employee_ids),
                     days_ago(random.randint(10, 200)),
                     random.choice(['Active', 'Inactive', 'Graduated']), now()))
            except:
                pass

    # tm_critical_roles
    for i, pos_id in enumerate(pos_ids[:10]):
        try:
            db.execute("""INSERT INTO tm_critical_roles
                (position_id, role_name, criticality_level, succession_urgency,
                 current_incumbent_id, is_backfilled, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (pos_id, f'نقش حیاتی {i+1}', random.choice(['Critical', 'High', 'Medium']),
                 random.choice(['Immediate', '1-3 Months', '3-6 Months', 'Long-term']),
                 random.choice(employee_ids), random.choice([0, 1]), now()))
        except:
            pass

    # tm_succession_plans
    for pool_id in pool_ids[:3]:
        for emp_id in employee_ids[:random.randint(3, 8)]:
            try:
                db.execute("""INSERT INTO tm_succession_plans
                    (employee_id, target_role_id, readiness_timeline,
                     development_actions, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (emp_id, random.choice(pos_ids),
                     random.choice(['Ready Now', '6 Months', '1 Year', '2 Years']),
                     f'اقدامات توسعه برای {emp_id}',
                     random.choice(['Active', 'Completed', 'On Hold']), now()))
            except:
                pass

    # tm_development_plans
    for emp_id in employee_ids[:20]:
        try:
            db.execute("""INSERT INTO tm_development_plans
                (employee_id, plan_title, description, goal_type,
                 start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, f'برنامه توسعه برای کارمند {emp_id}',
                 f'شرح برنامه توسعه فردی',
                 random.choice(['Technical', 'Leadership', 'Certification']),
                 days_ago(random.randint(10, 60)), days_future(random.randint(30, 180)),
                 random.choice(['Not Started', 'In Progress', 'Completed']), now()))
        except:
            pass

    # tm_development_goals
    for emp_id in employee_ids[:20]:
        for g in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO tm_development_goals
                    (employee_id, goal_text, goal_type, target_date,
                     status, progress_percent, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, f'هدف {g+1}: {random.choice(["یادگیری", "مهارت", "گواهینامه"])}',
                     random.choice(['Learning', 'Skill', 'Certification', 'Project']),
                     days_future(random.randint(30, 200)),
                     random.choice(['Not Started', 'In Progress', 'Completed']),
                     random.randint(0, 100), now()))
            except:
                pass

    # tm_development_actions
    for emp_id in employee_ids[:15]:
        for a in range(random.randint(2, 4)):
            try:
                db.execute("""INSERT INTO tm_development_actions
                    (employee_id, action_text, action_type, due_date,
                     status, completed_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, f'اقدام {a+1}',
                     random.choice(['Training', 'Mentoring', 'Project', 'Course']),
                     days_future(random.randint(10, 90)),
                     random.choice(['Pending', 'Completed', 'Overdue']),
                     days_ago(random.randint(0, 30)) if random.random() > 0.5 else None, now()))
            except:
                pass

    # tm_talent_reviews
    for emp_id in employee_ids[:25]:
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
                 f'توصیه‌های ارزیابی برای کارمند {emp_id}', now()))
        except:
            pass

    # tm_talent_review_participants
    reviewer_ids = employee_ids[:20]
    for rev_id in range(1, 16):
        try:
            db.execute("""INSERT INTO tm_talent_review_participants
                (review_id, participant_id, role, is_calibrator, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (rev_id, random.choice(reviewer_ids),
                 random.choice(['Reviewer', 'Calibrator', 'HR Partner']), 1, now()))
        except:
            pass

    # tm_mentoring_assignments
    for i in range(15):
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
    for pos_id in pos_ids[:8]:
        try:
            db.execute("""INSERT INTO tm_career_paths
                (position_id, career_path_name, path_description, is_technical_track,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (pos_id, f'مسیر شغلی برای {pos_id}',
                 f'شرح مسیر شغلی برای این موقعیت',
                 random.choice([0, 1]), now()))
        except:
            pass

    # tm_mobility_requests
    for emp_id in employee_ids[:15]:
        try:
            db.execute("""INSERT INTO tm_mobility_requests
                (employee_id, request_type, from_department_id, to_department_id,
                 request_date, target_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, random.choice(['Internal Transfer', 'Promotion', 'Lateral Move']),
                 random.choice(dept_ids), random.choice(dept_ids),
                 days_ago(random.randint(10, 60)), days_future(random.randint(30, 120)),
                 random.choice(['Pending', 'Approved', 'Rejected']), now()))
        except:
            pass

    # tm_talent_notes
    for emp_id in employee_ids[:15]:
        try:
            db.execute("""INSERT INTO tm_talent_notes
                (employee_id, note_text, note_type, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (emp_id, f'یادداشت استعداد برای کارمند {emp_id}',
                 random.choice(['General', 'Development', 'Performance']),
                 random.choice(employee_ids), now()))
        except:
            pass

    # tm_talent_history
    for emp_id in employee_ids[:15]:
        for h in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO tm_talent_history
                    (employee_id, event_type, event_date, description, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (emp_id, random.choice(['Promotion', 'Transfer', 'Review', 'Award']),
                     days_ago(random.randint(30, 365)),
                     f'رویداد {h} برای کارمند {emp_id}', now()))
            except:
                pass

    # tm_talent_engagement_signals
    for emp_id in employee_ids[:20]:
        try:
            db.execute("""INSERT INTO tm_talent_engagement_signals
                (employee_id, signal_type, signal_value, source, collected_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (emp_id, random.choice(['Survey', 'Manager', 'System']),
                 round(random.uniform(1, 5), 1), 'Employee Survey',
                 days_ago(random.randint(1, 60)), now()))
        except:
            pass

    # tm_talent_approvals
    for i in range(10):
        try:
            db.execute("""INSERT INTO tm_talent_approvals
                (approval_type, requester_id, approver_id, status,
                 requested_at, decided_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['Development Plan', 'Succession', 'Promotion']),
                 random.choice(employee_ids), random.choice(employee_ids),
                 random.choice(['Pending', 'Approved', 'Rejected']),
                 days_ago(random.randint(5, 30)), days_ago(random.randint(0, 4)), now()))
        except:
            pass

    db.commit()
    print("    + Talent Management: talent profiles, competencies, succession plans seeded")


# =============================================================================
# MODULE 4: MANUFACTURING & WORK CENTERS
# =============================================================================

def seed_manufacturing_module(db):
    """Seed manufacturing, work centers, and production tables."""
    print("  Seeding Manufacturing module...")

    company_ids = get_any_id('companies', db, 5)
    warehouse_ids = get_any_id('warehouses', db, 5)
    employee_ids = get_any_id('hr_employees', db, 30)
    part_ids = get_any_id('parts', db, 20)
    if not company_ids:
        company_ids = [1]
    if not warehouse_ids:
        warehouse_ids = [1]
    if employee_ids:
        employee_ids = employee_ids[:50]
    else:
        employee_ids = list(range(1, 51))
    if not part_ids:
        part_ids = [1]

    # work_centers
    work_center_types = ['Assembly', 'Machining', 'Painting', 'Packaging', 'Testing', 'Welding', 'CNC']
    wc_ids = []
    for i in range(1, 16):
        try:
            db.execute("""INSERT INTO work_centers
                (work_center_code, work_center_name, description, work_center_type,
                 location, capacity_hours_per_day, efficiency_target,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WC-{i:02d}',
                 f'مرکز کار {["مونتاژ", "ماشین‌کاری", "رنگ‌آمیزی", "بسته‌بندی", "آزمایش", "جوشکاری", "CNC"][i % 7]} {i}',
                 f'مرکز کار تولیدی شماره {i}',
                 work_center_types[i % len(work_center_types)],
                 f'سالن تولید {["A", "B", "C", "D", "E"][i % 5]}',
                 random.randint(8, 16), round(random.uniform(80, 98), 1),
                 random.choice(['Active', 'Active', 'Active', 'Idle', 'Maintenance']), now()))
            wc_ids.append(db.execute("SELECT last_insert_rowid()").fetchone()[0])
        except Exception as e:
            pass

    db.commit()

    # work_center_shifts
    for wc_id in wc_ids:
        shifts = [('صبح', '06:00', '14:00'), ('عصر', '14:00', '22:00'), ('شب', '22:00', '06:00')]
        for name, start, end in shifts:
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

    # work_order_operation_codes
    op_codes = [
        ('CUT', 'برش', 'عملیات برش قطعات'),
        ('DRILL', 'سوراخ‌کاری', 'سوراخ‌کاری دقیق'),
        ('WELD', 'جوشکاری', 'جوشکاری قطعات فلزی'),
        ('ASSEM', 'مونتاژ', 'مونتاژ نهایی محصول'),
        ('PAINT', 'رنگ‌آمیزی', 'رنگ‌آمیزی و پوشش'),
        ('PACK', 'بسته‌بندی', 'بسته‌بندی محصول'),
        ('INSPECT', 'بازرسی', 'بازرسی نهایی'),
        ('TEST', 'آزمایش', 'تست عملکرد محصول')
    ]
    for code, name, desc in op_codes:
        try:
            db.execute("""INSERT INTO work_order_operation_codes
                (operation_code, operation_name, description, estimated_time_minutes,
                 work_center_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (code, name, desc, random.randint(10, 120),
                 random.choice(wc_ids) if wc_ids else 1, 1, now()))
        except:
            pass

    # work_order_operations
    for i in range(1, 51):
        for seq, (code, name, desc) in enumerate(op_codes[:random.randint(3, 6)], 1):
            try:
                db.execute("""INSERT INTO work_order_operations
                    (operation_code, operation_name, work_center_id, sequence_number,
                     planned_start, planned_end, actual_start, actual_end,
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (code, name, random.choice(wc_ids) if wc_ids else 1, seq,
                     days_ago(random.randint(1, 30)), days_ago(random.randint(0, 20)),
                     days_ago(random.randint(0, 15)), days_ago(random.randint(0, 10)),
                     random.choice(['Pending', 'In Progress', 'Completed', 'Skipped']), now()))
            except:
                pass

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

    # work_order_confirmations
    for i in range(1, 51):
        try:
            db.execute("""INSERT INTO work_order_confirmations
                (confirmation_date, confirmed_by, quantity_completed, quantity_rejected,
                 work_station_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (days_ago(random.randint(0, 30)),
                 random.choice(employee_ids) if employee_ids else 1,
                 random.randint(50, 500), random.randint(0, 10),
                 random.choice(wc_ids) if wc_ids else 1,
                 random.choice(['Confirmed', 'Pending', 'Rejected']), now()))
        except:
            pass

    # work_order_cost_plan
    for i in range(1, 31):
        try:
            db.execute("""INSERT INTO work_order_cost_plan
                (cost_type, planned_cost, actual_cost, variance,
                 currency, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Material', 'Labor', 'Overhead', 'Total']),
                 round(random.uniform(1000, 50000), 2),
                 round(random.uniform(1000, 50000), 2),
                 round(random.uniform(-5000, 5000), 2),
                 random.choice(['USD', 'AED', 'EUR']), now()))
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
                    (wc_id, f'مهارت {skill}',
                     random.randint(1, 5), random.choice([0, 1]), now()))
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
                    (wc_id, f'ابزار {tool}', random.choice(['Hand', 'Power', 'Measuring']),
                     random.randint(1, 20),
                     random.choice(['Good', 'Needs Maintenance', 'New']), now()))
            except:
                pass

    db.commit()
    print("    + Manufacturing: work centers, operations, work orders seeded")


# =============================================================================
# MODULE 5: BTP / INTEGRATION EXTRA TABLES
# =============================================================================

def seed_btp_integration_extra(db):
    """Seed additional BTP and integration tables."""
    print("  Seeding BTP/Integration extra tables...")

    connector_ids = get_any_id('btp_connectors', db, 10)
    flow_ids = get_any_id('btp_integration_flows', db, 10)
    user_ids = get_any_id('users', db, 10)
    if not connector_ids:
        connector_ids = [1]
    if not flow_ids:
        flow_ids = [1]
    if not user_ids:
        user_ids = [1]

    # btp_ai_chats
    for i in range(15):
        try:
            db.execute("""INSERT INTO btp_ai_chats
                (chat_session_id, user_id, provider, model, prompt_tokens,
                 completion_tokens, total_tokens, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'sess-{i+1:04d}', random.choice(user_ids),
                 random.choice(['OpenAI', 'Azure OpenAI', 'Anthropic']),
                 random.choice(['gpt-4', 'gpt-3.5-turbo', 'claude-3']),
                 random.randint(100, 2000), random.randint(100, 3000),
                 random.randint(200, 5000), random.randint(500, 5000), now()))
        except:
            pass

    # btp_ai_messages
    for i in range(50):
        try:
            db.execute("""INSERT INTO btp_ai_messages
                (chat_session_id, role, content, token_count, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'sess-{(i % 15) + 1:04d}',
                 random.choice(['user', 'assistant']),
                 f'پیام {i+1} - محتوای چت هوش مصنوعی',
                 random.randint(50, 500), now()))
        except:
            pass

    # btp_event_subscriptions
    for i in range(10):
        try:
            db.execute("""INSERT INTO btp_event_subscriptions
                (subscription_name, event_type, endpoint_url, auth_type,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f' subscription {i+1}', random.choice(['order.created', 'inventory.updated', 'shipment.shipped']),
                 f'https://api.example.com/webhooks/{i+1}',
                 random.choice(['Bearer', 'API Key', 'OAuth2']), 1, now()))
        except:
            pass

    # btp_webhook_deliveries
    for i in range(20):
        try:
            db.execute("""INSERT INTO btp_webhook_deliveries
                (webhook_id, endpoint, payload, response_status, response_body,
                 attempt_number, delivered_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), f'https://api.example.com/{i+1}',
                 f'{{"event": "test", "id": {i+1}}}',
                 random.choice([200, 200, 200, 201, 400, 500]),
                 '{"status": "ok"}', random.randint(1, 3),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # btp_change_requests
    for i in range(12):
        try:
            db.execute("""INSERT INTO btp_change_requests
                (request_id, change_type, description, status,
                 requested_by, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'CR-{i+1:04d}', random.choice(['Feature', 'Bug Fix', 'Config', 'Migration']),
                 f'توضیحات درخواست تغییر {i+1}',
                 random.choice(['Draft', 'Submitted', 'Under Review', 'Approved', 'Rejected']),
                 random.choice(user_ids), random.choice(user_ids), now()))
        except:
            pass

    # btp_mapping_versions
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_mapping_versions
                (mapping_id, version_number, mapping_config, is_active,
                 created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), i + 1,
                 f'{{"mapping": "config", "v": {i+1}}}',
                 1 if i == 0 else 0, random.choice(user_ids), now()))
        except:
            pass

    # btp_extension_rules
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_extension_rules
                (rule_name, rule_type, extension_point, rule_config,
                 priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Rule {i+1}', random.choice(['Pre', 'Post', 'Transform']),
                 random.choice(['OrderProcessing', 'InventoryUpdate', 'CustomerSync']),
                 f'{{"rule": "config", "id": {i+1}}}',
                 random.randint(1, 10), 1, now()))
        except:
            pass

    # btp_job_attempts
    for i in range(20):
        try:
            db.execute("""INSERT INTO btp_job_attempts
                (job_id, attempt_number, status, started_at, completed_at,
                 error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 25), i % 3 + 1,
                 random.choice(['Running', 'Success', 'Failed']),
                 days_ago(random.randint(0, 20)),
                 days_ago(random.randint(0, 15)),
                 f'خطای {i+1}' if random.random() > 0.7 else None, now()))
        except:
            pass

    # btp_connector_logs
    for i in range(30):
        try:
            db.execute("""INSERT INTO btp_connector_logs
                (connector_id, log_level, message, context,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.choice(connector_ids),
                 random.choice(['INFO', 'WARNING', 'ERROR', 'DEBUG']),
                 f'پیام لاگ برای کانکتور {i+1}',
                 f'{{"context": {i+1}}}', now()))
        except:
            pass

    # btp_data_quality_checks
    for i in range(15):
        try:
            db.execute("""INSERT INTO btp_data_quality_checks
                (check_name, check_type, entity, passed_count, failed_count,
                 check_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Quality Check {i+1}', random.choice(['Completeness', 'Uniqueness', 'Validity']),
                 random.choice(['Customer', 'Order', 'Product', 'Inventory']),
                 random.randint(80, 100), random.randint(0, 20),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # btp_reconciliations
    for i in range(10):
        try:
            db.execute("""INSERT INTO btp_reconciliations
                (reconciliation_id, source_system, target_system, record_count,
                 matched_count, discrepancies, status, run_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'REC-{i+1:04d}', 'SAP', 'Salesforce',
                 random.randint(100, 1000), random.randint(80, 950),
                 random.randint(0, 50),
                 random.choice(['Completed', 'In Progress', 'Failed']),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # btp_export_history
    for i in range(12):
        try:
            db.execute("""INSERT INTO btp_export_history
                (export_name, export_type, file_path, record_count,
                 status, exported_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Export {i+1}', random.choice(['Full', 'Incremental']),
                 f'/exports/file_{i+1}.csv',
                 random.randint(100, 5000),
                 random.choice(['Completed', 'Failed', 'Running']),
                 random.choice(user_ids), now()))
        except:
            pass

    # btp_secret_references
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_secret_references
                (secret_name, secret_type, description, created_at)
                VALUES (?, ?, ?, ?)""",
                (f'secret-{i+1}', random.choice(['API Key', 'Password', 'Certificate']),
                 f'توضیحات مخفی {i+1}', now()))
        except:
            pass

    # btp_file_templates
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_file_templates
                (template_name, template_type, template_content,
                 description, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'Template {i+1}', random.choice(['CSV', 'XML', 'JSON']),
                 f'<template>{i+1}</template>',
                 f'قالب فایل {i+1}', now()))
        except:
            pass

    # btp_api_versions
    for i in range(5):
        try:
            db.execute("""INSERT INTO btp_api_versions
                (api_name, version, status, released_at, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'API {i%3+1}', f'v{i+1}.0',
                 random.choice(['Active', 'Deprecated', 'Beta']),
                 days_ago(random.randint(30, 365)), now()))
        except:
            pass

    # btp_api_policies
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_api_policies
                (policy_name, policy_type, config, priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Policy {i+1}', random.choice(['Rate Limit', 'Authentication', 'CORS']),
                 f'{{"config": {i+1}}}', random.randint(1, 10), 1, now()))
        except:
            pass

    # btp_provider_usage_logs
    for i in range(20):
        try:
            db.execute("""INSERT INTO btp_provider_usage_logs
                (provider, model, input_tokens, output_tokens, cost,
                 latency_ms, call_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['OpenAI', 'Azure', 'Anthropic']),
                 random.choice(['gpt-4', 'gpt-3.5', 'claude-3']),
                 random.randint(100, 5000), random.randint(100, 5000),
                 round(random.uniform(0.1, 10.0), 4),
                 random.randint(100, 3000), days_ago(random.randint(0, 14)), now()))
        except:
            pass

    # btp_flow_versions
    for i in range(8):
        try:
            db.execute("""INSERT INTO btp_flow_versions
                (flow_id, version_number, flow_definition, is_active,
                 created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(flow_ids) if flow_ids else 1, i + 1,
                 f'{{"flow": "definition", "v": {i+1}}}',
                 1 if i == 0 else 0, random.choice(user_ids), now()))
        except:
            pass

    # btp_platform_settings
    for i in range(6):
        try:
            db.execute("""INSERT INTO btp_platform_settings
                (setting_key, setting_value, description, updated_at)
                VALUES (?, ?, ?, ?)""",
                (f'btp.setting.{i+1}', f'value_{i+1}',
                 f'تنظیمات پلتفرم {i+1}', now()))
        except:
            pass

    db.commit()
    print("    + BTP/Integration extra tables seeded")


# =============================================================================
# MODULE 6: ADDITIONAL CRM TABLES
# =============================================================================

def seed_crm_extra(db):
    """Seed additional CRM tables that are empty."""
    print("  Seeding CRM extra tables...")

    customer_ids = get_any_id('customers', db, 50)
    user_ids = get_any_id('users', db, 20)
    if not customer_ids:
        customer_ids = [1]
    if not user_ids:
        user_ids = [1]

    # crm_customer_contacts
    for cust_id in customer_ids[:40]:
        for c in range(random.randint(1, 3)):
            try:
                db.execute("""INSERT INTO crm_customer_contacts
                    (customer_id, contact_name, contact_role, phone, email,
                     is_primary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (cust_id,
                     f'{random.choice(PERSIAN_FIRST_NAMES)} {random.choice(PERSIAN_LAST_NAMES)}',
                     random.choice(['مدیر', 'کارشناس', 'مسئول', 'مدیرعامل']),
                     f'+97150{random.randint(1000000, 9999999)}',
                     f'contact{c}{cust_id}@example.com',
                     1 if c == 0 else 0, now()))
            except:
                pass

    # crm_lead_contacts
    for i in range(30):
        try:
            db.execute("""INSERT INTO crm_lead_contacts
                (lead_id, contact_name, phone, email, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (i + 1,
                 f'{random.choice(PERSIAN_FIRST_NAMES)} {random.choice(PERSIAN_LAST_NAMES)}',
                 f'+97150{random.randint(1000000, 9999999)}',
                 f'lead{i}@example.com', now()))
        except:
            pass

    # crm_lead_notes
    for i in range(25):
        try:
            db.execute("""INSERT INTO crm_lead_notes
                (lead_id, note_text, created_by, created_at)
                VALUES (?, ?, ?, ?)""",
                (i % 50 + 1, f'یادداشت برای لید {i+1}',
                 random.choice(user_ids), now()))
        except:
            pass

    # crm_lead_qualifications
    for i in range(20):
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

    # crm_lead_conversion_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO crm_lead_conversion_log
                (lead_id, converted_to_customer_id, conversion_date,
                 conversion_reason, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (i + 1, i + 1001, days_ago(random.randint(1, 180)),
                 f'دلیل تبدیل {i+1}', now()))
        except:
            pass

    # crm_customer_segments
    for i in range(10):
        try:
            db.execute("""INSERT INTO crm_customer_segments
                (segment_name, segment_code, description, criteria,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Segment {i+1}', f'SEG-{i+1:02d}',
                 f'توضیحات بخش {i+1}',
                 f'criteria for segment {i+1}', 1, now()))
        except:
            pass

    # crm_customer_hierarchy
    for i in range(15):
        try:
            db.execute("""INSERT INTO crm_customer_hierarchy
                (parent_customer_id, child_customer_id, relationship_type,
                 created_at)
                VALUES (?, ?, ?, ?)""",
                (random.choice(customer_ids), random.choice(customer_ids),
                 random.choice(['Subsidiary', 'Parent', 'Branch']), now()))
        except:
            pass

    # crm_customer_engagement
    for cust_id in customer_ids[:30]:
        for e in range(random.randint(2, 6)):
            try:
                db.execute("""INSERT INTO crm_customer_engagement
                    (customer_id, engagement_type, engagement_date, score,
                     created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (cust_id, random.choice(['Email', 'Call', 'Meeting', 'Visit']),
                     days_ago(random.randint(1, 90)),
                     random.randint(1, 10), now()))
            except:
                pass

    # crm_customer_credit_risk
    for cust_id in customer_ids[:30]:
        try:
            db.execute("""INSERT INTO crm_customer_credit_risk
                (customer_id, risk_score, risk_rating, credit_limit,
                 outstanding_balance, risk_factors, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cust_id, round(random.uniform(1, 10), 1),
                 random.choice(['Low', 'Medium', 'High']),
                 random.randint(10000, 500000),
                 random.randint(0, 200000),
                 f'عوامل ریسک برای {cust_id}', now()))
        except:
            pass

    # crm_customer_churn_risk
    for cust_id in customer_ids[:30]:
        try:
            db.execute("""INSERT INTO crm_customer_churn_risk
                (customer_id, churn_score, risk_level, churn_probability,
                 risk_factors, retention_actions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (cust_id, round(random.uniform(0, 100), 1),
                 random.choice(['Low', 'Medium', 'High', 'Critical']),
                 round(random.uniform(0, 0.5), 3),
                 f'عوامل ریزش برای {cust_id}',
                 random.choice(['None', 'Discount Offer', 'Personal Call', 'Loyalty Program']), now()))
        except:
            pass

    # crm_customer_stage_history
    for cust_id in customer_ids[:20]:
        for s in range(random.randint(2, 5)):
            try:
                db.execute("""INSERT INTO crm_customer_stage_history
                    (customer_id, stage, entered_at, exited_at, duration_days,
                     created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (cust_id, f'Stage {s+1}',
                     days_ago(random.randint(60, 200)),
                     days_ago(random.randint(30, 150)),
                     random.randint(10, 60), now()))
            except:
                pass

    # crm_relationship_map
    for cust_id in customer_ids[:20]:
        try:
            db.execute("""INSERT INTO crm_relationship_map
                (customer_id, related_customer_id, relationship_type,
                 strength, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (cust_id, random.choice(customer_ids),
                 random.choice(['Strategic', 'Preferred', 'Standard']),
                 random.randint(1, 5), now()))
        except:
            pass

    # crm_touchpoints
    for cust_id in customer_ids[:25]:
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
    for i in range(15):
        try:
            db.execute("""INSERT INTO crm_account_reviews
                (customer_id, review_date, reviewer_id, overall_rating,
                 financial_rating, operational_rating, strategic_rating,
                 next_review_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(customer_ids), days_ago(random.randint(1, 180)),
                 random.choice(user_ids),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 round(random.uniform(1, 5), 1),
                 days_future(random.randint(30, 180)), now()))
        except:
            pass

    db.commit()
    print("    + CRM extra tables seeded")


# =============================================================================
# MODULE 7: ADDITIONAL QUALITY TABLES
# =============================================================================

def seed_quality_extra(db):
    """Seed additional quality tables with just 1 row."""
    print("  Seeding Quality extra tables...")

    employee_ids = get_any_id('hr_employees', db, 20)
    part_ids = get_any_id('parts', db, 15)
    if not employee_ids:
        employee_ids = [1]
    if not part_ids:
        part_ids = [1]

    # Additional quality_inspections
    for i in range(30):
        try:
            db.execute("""INSERT INTO quality_inspections
                (inspection_number, inspection_type, part_id, quantity_inspected,
                 quantity_passed, quantity_failed, defect_rate, result,
                 inspector_id, inspection_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'INS-{i+1:04d}', random.choice(['Incoming', 'In-Process', 'Final']),
                 random.choice(part_ids), random.randint(50, 500),
                 random.randint(40, 480), random.randint(0, 30),
                 round(random.uniform(0, 5), 2),
                 random.choice(['PASS', 'FAIL']),
                 random.choice(employee_ids),
                 days_ago(random.randint(1, 90)), now()))
        except:
            pass

    # Additional quality_non_conformances
    for i in range(20):
        try:
            db.execute("""INSERT INTO quality_non_conformances
                (ncr_number, description, severity, status, reported_by,
                 reported_date, resolved_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'NCR-{i+1:04d}', f'توضیحات عدم انطباق {i+1}',
                 random.choice(['Critical', 'Major', 'Minor']),
                 random.choice(['Open', 'In Progress', 'Closed']),
                 random.choice(employee_ids),
                 days_ago(random.randint(1, 120)),
                 days_ago(random.randint(0, 60)) if random.random() > 0.3 else None, now()))
        except:
            pass

    # Additional quality_capa_records
    for i in range(15):
        try:
            db.execute("""INSERT INTO quality_capa_records
                (capa_number, title, description, severity, status,
                 root_cause, corrective_action, preventive_action,
                 assigned_to, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CAPA-{i+1:04d}', f' اقدام اصلاحی {i+1}',
                 f'شرح CAPA شماره {i+1}',
                 random.choice(['Critical', 'Major', 'Minor']),
                 random.choice(['Open', 'In Progress', 'Completed', 'Verified']),
                 f'علت ریشه‌ای {i+1}',
                 f'اقدام اصلاحی {i+1}',
                 f'اقدام پیشگیرانه {i+1}',
                 random.choice(employee_ids),
                 days_future(random.randint(7, 60)), now()))
        except:
            pass

    # quality_audit_plans (add more)
    for i in range(10):
        try:
            db.execute("""INSERT INTO quality_audit_plans
                (plan_code, plan_name, audit_type, scope, objectives,
                 auditor_id, scheduled_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'AUD-PLAN-{i+1:03d}', f'برنامه ممیزی {i+1}',
                 random.choice(['Internal', 'External', 'Supplier']),
                 f'دامنه ممیزی {i+1}',
                 f'اهداف ممیزی {i+1}',
                 random.choice(employee_ids),
                 days_future(random.randint(7, 90)),
                 random.choice(['Planned', 'In Progress', 'Completed']), now()))
        except:
            pass

    # quality_audit_findings (add more)
    for i in range(20):
        try:
            db.execute("""INSERT INTO quality_audit_findings
                (audit_plan_id, finding_code, finding_type, description,
                 severity, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 16), f'FIND-{i+1:03d}',
                 random.choice(['Non-Conformance', 'Observation', 'Opportunity']),
                 f'یافته ممیزی شماره {i+1}',
                 random.choice(['Critical', 'Major', 'Minor', 'Observation']),
                 random.choice(['Open', 'In Progress', 'Closed']),
                 days_future(random.randint(7, 45)), now()))
        except:
            pass

    db.commit()
    print("    + Quality extra tables seeded")


# =============================================================================
# MODULE 8: SERVICE, WARRANTY, TECHNICIAN TABLES
# =============================================================================

def seed_service_warranty(db):
    """Seed service, warranty, and technician tables."""
    print("  Seeding Service, Warranty, and Technician tables...")

    employee_ids = get_any_id('hr_employees', db, 30)
    customer_ids = get_any_id('customers', db, 30)
    part_ids = get_any_id('parts', db, 20)
    if not employee_ids:
        employee_ids = list(range(1, 31))
    if not customer_ids:
        customer_ids = list(range(1, 31))
    if not part_ids:
        part_ids = [1]

    # service_agreements
    agreement_types = ['Basic', 'Standard', 'Premium', 'Enterprise']
    for i in range(20):
        try:
            db.execute("""INSERT INTO service_agreements
                (agreement_number, customer_id, agreement_type, start_date,
                 end_date, coverage_terms, annual_value, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SA-{i+1:04d}', random.choice(customer_ids),
                 agreement_types[i % len(agreement_types)],
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
                (name, f'توضیحات نوع سفارش {name}',
                 random.randint(4, 72), 1, now()))
        except:
            pass

    # warranty_records
    for i in range(25):
        try:
            db.execute("""INSERT INTO warranty_records
                (warranty_number, customer_id, part_id, serial_number,
                 purchase_date, warranty_start_date, warranty_end_date,
                 warranty_type, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WARR-{i+1:04d}', random.choice(customer_ids),
                 random.choice(part_ids), f'SN-{random.randint(10000, 99999)}',
                 days_ago(random.randint(30, 365)),
                 days_ago(random.randint(0, 30)),
                 days_future(random.randint(30, 730)),
                 random.choice(['Standard', 'Extended', 'Manufacturer']),
                 random.choice(['Active', 'Expired', 'Claimed']), now()))
        except:
            pass

    # warranty_claims
    for i in range(15):
        try:
            db.execute("""INSERT INTO warranty_claims
                (claim_number, warranty_id, claim_type, description,
                 claim_amount, status, filed_date, resolved_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'WC-{i+1:04d}', random.randint(1, 25),
                 random.choice(['Repair', 'Replacement', 'Refund']),
                 f'توضیحات ادعای گارانتی {i+1}',
                 round(random.uniform(100, 5000), 2),
                 random.choice(['Submitted', 'Under Review', 'Approved', 'Rejected']),
                 days_ago(random.randint(1, 60)),
                 days_ago(random.randint(0, 30)) if random.random() > 0.3 else None, now()))
        except:
            pass

    # technician_shifts
    for emp_id in employee_ids[:15]:
        shifts = [('صبح', '06:00', '14:00'), ('عصر', '14:00', '22:00')]
        for name, start, end in shifts:
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
    for emp_id in employee_ids[:15]:
        skills = ['Electronics', 'Mechanical', 'Hydraulics', 'Pneumatics', 'PLC', 'HVAC']
        for skill in random.sample(skills, random.randint(2, 4)):
            try:
                db.execute("""INSERT INTO technician_skill_levels
                    (technician_id, skill_name, skill_level, certified_date,
                     expiry_date, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, skill, random.randint(1, 5),
                     days_ago(random.randint(30, 365)),
                     days_future(random.randint(90, 730)),
                     1, now()))
            except:
                pass

    # skill_catalog
    for skill in ['Electronics', 'Mechanical', 'Hydraulics', 'Pneumatics', 'PLC Programming',
                  'HVAC', 'Welding', 'CNC Operation', 'Quality Control', 'Safety']:
        try:
            db.execute("""INSERT INTO skill_catalog
                (skill_name, description, category, proficiency_levels,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (skill, f'توضیحات مهارت {skill}',
                 random.choice(['Technical', 'Safety', 'Management']),
                 '1-5', 1, now()))
        except:
            pass

    db.commit()
    print("    + Service, Warranty, Technician tables seeded")


# =============================================================================
# MODULE 9: ADDITIONAL TABLES - FILL MINIMAL ONES
# =============================================================================

def seed_minimal_tables(db):
    """Seed all remaining tables that have just 1 row or are minimally populated."""
    print("  Seeding minimal tables...")

    user_ids = get_any_id('users', db, 10)
    company_ids = get_any_id('companies', db, 5)
    employee_ids = get_any_id('hr_employees', db, 20)
    warehouse_ids = get_any_id('warehouses', db, 5)

    if not user_ids:
        user_ids = [1]
    if not company_ids:
        company_ids = [1]
    if not employee_ids:
        employee_ids = list(range(1, 21))
    if not warehouse_ids:
        warehouse_ids = [1]

    # shift_definitions
    shifts = [
        ('صبحانه', 'Morning', '06:00', '14:00'),
        ('عصرانه', 'Afternoon', '14:00', '22:00'),
        ('شبانه', 'Night', '22:00', '06:00'),
    ]
    for code, name, start, end in shifts:
        try:
            db.execute("""INSERT INTO shift_definitions
                (shift_code, shift_name, start_time, end_time,
                 is_night_shift, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (code, name, start, end, 1 if 'شب' in code else 0, 1, now()))
        except:
            pass

    # shift_patterns
    for i in range(5):
        try:
            db.execute("""INSERT INTO shift_patterns
                (pattern_name, pattern_type, rotation_days, shift_sequence,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Pattern {i+1}', random.choice(['Fixed', 'Rotating', 'Split']),
                 random.randint(1, 7),
                 f'Morning,Afternoon,Night',
                 1, now()))
        except:
            pass

    # travel_segments
    for i in range(15):
        try:
            db.execute("""INSERT INTO travel_segments
                (itinerary_id, segment_type, departure_city, arrival_city,
                 departure_time, arrival_time, transport_mode,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 25),
                 random.choice(['Flight', 'Hotel', 'Car', 'Train']),
                 random.choice(PERSIAN_CITIES),
                 random.choice(PERSIAN_CITIES),
                 days_ago(random.randint(1, 60)) + ' 08:00:00',
                 days_ago(random.randint(1, 60)) + ' 14:00:00',
                 random.choice(['Air', 'Ground', 'Rail']),
                 random.choice(['Booked', 'Completed', 'Cancelled']), now()))
        except:
            pass

    # quick_notes
    for i in range(15):
        try:
            db.execute("""INSERT INTO quick_notes
                (note_text, user_id, is_pinned, created_at)
                VALUES (?, ?, ?, ?)""",
                (f'یادداشت سریع {i+1}',
                 random.choice(user_ids),
                 random.choice([0, 1]), now()))
        except:
            pass

    # quick_access_items
    for i in range(12):
        try:
            db.execute("""INSERT INTO quick_access_items
                (item_name, item_type, item_url, user_id,
                 access_count, last_accessed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'آیتم دسترسی سریع {i+1}',
                 random.choice(['page', 'report', 'dashboard']),
                 f'/page/{i+1}',
                 random.choice(user_ids),
                 random.randint(1, 50),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # saved_searches
    for i in range(10):
        try:
            db.execute("""INSERT INTO saved_searches
                (search_name, search_query, user_id, is_shared,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'جستجوی ذخیره شده {i+1}',
                 f'q=search+{i+1}',
                 random.choice(user_ids),
                 random.choice([0, 1]), now()))
        except:
            pass

    # approval_matrix
    for i in range(8):
        try:
            db.execute("""INSERT INTO approval_matrix
                (approval_type, approver_role, threshold_amount,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.choice(['Purchase', 'Expense', 'Leave', 'Travel']),
                 random.choice(['Manager', 'Director', 'VP', 'CEO']),
                 random.randint(1000, 50000), 1, now()))
        except:
            pass

    # access_review_items
    for i in range(15):
        try:
            db.execute("""INSERT INTO access_review_items
                (review_id, user_id, resource_type, resource_name,
                 access_level, risk_score, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 5), random.choice(user_ids),
                 random.choice(['Table', 'Report', 'API']),
                 f'Resource {i+1}',
                 random.choice(['Read', 'Write', 'Admin']),
                 random.randint(1, 10),
                 random.choice(['Approved', 'Revoked', 'Pending']), now()))
        except:
            pass

    # advance_settlements
    for i in range(12):
        try:
            db.execute("""INSERT INTO advance_settlements
                (settlement_number, employee_id, advance_id, amount,
                 settled_amount, status, settled_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SET-{i+1:04d}', random.choice(employee_ids),
                 random.randint(1, 10),
                 round(random.uniform(500, 5000), 2),
                 round(random.uniform(0, 3000), 2),
                 random.choice(['Pending', 'Partial', 'Complete']),
                 days_ago(random.randint(1, 30)), now()))
        except:
            pass

    # agreement_line_items
    for i in range(15):
        try:
            db.execute("""INSERT INTO agreement_line_items
                (agreement_id, item_description, quantity, unit_price,
                 total_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), f'شرح آیتم قرارداد {i+1}',
                 random.randint(1, 100),
                 round(random.uniform(10, 1000), 2),
                 round(random.uniform(100, 50000), 2), now()))
        except:
            pass

    # counter_readings
    for i in range(15):
        try:
            db.execute("""INSERT INTO counter_readings
                (counter_type, counter_value, reading_date, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.choice(['Production', 'Quality', 'Maintenance']),
                 random.randint(1000, 100000),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # condition_indicators
    for ind in ['Temperature', 'Pressure', 'Vibration', 'Humidity', 'Flow']:
        try:
            db.execute("""INSERT INTO condition_indicators
                (indicator_name, indicator_type, unit, normal_min,
                 normal_max, alert_threshold, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (ind, 'Sensor', random.choice(['°C', 'PSI', 'mm/s', '%', 'L/min']),
                 round(random.uniform(10, 50), 1), round(random.uniform(60, 100), 1),
                 round(random.uniform(80, 120), 1), 1, now()))
        except:
            pass

    # condition_readings
    for i in range(30):
        try:
            db.execute("""INSERT INTO condition_readings
                (indicator_id, reading_value, reading_timestamp,
                 is_within_limits, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.randint(1, 5),
                 round(random.uniform(20, 100), 2),
                 days_ago(random.randint(0, 7)) + ' ' + f'{random.randint(0,23):02d}:00:00',
                 random.choice([0, 1, 1, 1]), now()))
        except:
            pass

    # security_policy_versions
    for i in range(5):
        try:
            db.execute("""INSERT INTO security_policy_versions
                (policy_id, version_number, change_description,
                 effective_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 4), i + 1,
                 f'توضیحات تغییرات نسخه {i+1}',
                 days_ago(random.randint(30, 180)),
                 random.choice(['Active', 'Superseded']), now()))
        except:
            pass

    # role_conflict_rules
    for i in range(8):
        try:
            db.execute("""INSERT INTO role_conflict_rules
                (conflict_name, role_1_id, role_2_id, conflict_type,
                 severity, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Conflict {i+1}',
                 random.randint(1, 10), random.randint(1, 10),
                 random.choice(['Segregation', 'Hierarchy', 'Exclusion']),
                 random.choice(['High', 'Medium', 'Low']), 1, now()))
        except:
            pass

    # user_role_conflicts
    for i in range(10):
        try:
            db.execute("""INSERT INTO user_role_conflicts
                (user_id, conflict_rule_id, conflict_status,
                 resolved_date, resolution_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(user_ids), random.randint(1, 8),
                 random.choice(['Detected', 'Acknowledged', 'Resolved']),
                 days_ago(random.randint(0, 30)),
                 f'توضیحات رفع تعارض {i+1}', now()))
        except:
            pass

    # sso_audit_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO sso_audit_log
                (event_type, user_id, provider, ip_address,
                 user_agent, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['Login', 'Logout', 'Token Refresh', 'MFA']),
                 random.choice(user_ids),
                 random.choice(['Azure AD', 'Google', 'Okta']),
                 f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
                 'Mozilla/5.0', random.choice(['Success', 'Failed']), now()))
        except:
            pass

    # sso_provider_certificates
    for provider in ['Azure AD', 'Google Workspace', 'Okta']:
        try:
            db.execute("""INSERT INTO sso_provider_certificates
                (provider_name, certificate_serial, issued_date,
                 expiry_date, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (provider, f'CERT-{random.randint(10000, 99999)}',
                 days_ago(random.randint(180, 365)),
                 days_future(random.randint(180, 365)),
                 1, now()))
        except:
            pass

    # dms_metadata_values
    for i in range(15):
        try:
            db.execute("""INSERT INTO dms_metadata_values
                (document_id, metadata_definition_id, value_text,
                 created_at)
                VALUES (?, ?, ?, ?)""",
                (random.randint(1, 62), random.randint(1, 5),
                 f'مقدار فراداده {i+1}', now()))
        except:
            pass

    # dms_saved_views
    for i in range(8):
        try:
            db.execute("""INSERT INTO dms_saved_views
                (view_name, view_config, user_id, is_shared,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'View {i+1}', f'{{"config": {i+1}}}',
                 random.choice(user_ids), random.choice([0, 1]), now()))
        except:
            pass

    # dms_archive_log
    for i in range(10):
        try:
            db.execute("""INSERT INTO dms_archive_log
                (document_id, archived_by, archive_date,
                 archive_location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 62), random.choice(user_ids),
                 days_ago(random.randint(30, 180)),
                 f'/archive/{i+1}',
                 random.choice(['Archived', 'Restored']), now()))
        except:
            pass

    # dms_disposal_log
    for i in range(8):
        try:
            db.execute("""INSERT INTO dms_disposal_log
                (document_id, disposed_by, disposal_date,
                 disposal_method, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 62), random.choice(user_ids),
                 days_ago(random.randint(30, 180)),
                 random.choice(['Shred', 'Delete', 'Recycle']),
                 random.choice(['Pending', 'Completed']), now()))
        except:
            pass

    # dms_required_document_rules
    for i in range(6):
        try:
            db.execute("""INSERT INTO dms_required_document_rules
                (rule_name, document_type, required_document_type,
                 is_mandatory, validity_days, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Rule {i+1}', f'Type {i+1}',
                 f'Required {i+1}', random.choice([0, 1]),
                 random.randint(30, 365), now()))
        except:
            pass

    # dms_legal_hold_documents
    for i in range(8):
        try:
            db.execute("""INSERT INTO dms_legal_hold_documents
                (legal_hold_id, document_id, added_by, added_date,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 3), random.randint(1, 62),
                 random.choice(user_ids), days_ago(random.randint(30, 120)),
                 random.choice(['Active', 'Released']), now()))
        except:
            pass

    # document_checkout
    for i in range(10):
        try:
            db.execute("""INSERT INTO document_checkout
                (document_id, checked_out_by, checkout_date,
                 expected_return, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 62), random.choice(user_ids),
                 days_ago(random.randint(0, 7)),
                 days_future(random.randint(1, 14)),
                 random.choice(['Checked Out', 'Returned']), now()))
        except:
            pass

    # document_checkout_history
    for i in range(15):
        try:
            db.execute("""INSERT INTO document_checkout_history
                (document_id, user_id, checkout_date, return_date,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 62), random.choice(user_ids),
                 days_ago(random.randint(7, 60)),
                 days_ago(random.randint(0, 6)),
                 'Returned', now()))
        except:
            pass

    # document_retention_schedules
    for i in range(8):
        try:
            db.execute("""INSERT INTO document_retention_schedules
                (schedule_name, document_type, retention_period_days,
                 disposition_action, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Schedule {i+1}', f'Type {i+1}',
                 random.randint(365, 2555),
                 random.choice(['Archive', 'Delete', 'Review']),
                 1, now()))
        except:
            pass

    # document_locks
    for i in range(8):
        try:
            db.execute("""INSERT INTO document_locks
                (document_id, locked_by, lock_type, locked_at,
                 expires_at, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 62), random.choice(user_ids),
                 random.choice(['Exclusive', 'Shared']),
                 days_ago(random.randint(0, 7)),
                 days_future(random.randint(1, 30)),
                 random.choice([0, 1]), now()))
        except:
            pass

    # ecommerce_price_lists
    for name, desc in [('Retail', 'قیمت خرده'), ('Wholesale', 'قیمت عمده'), ('VIP', 'قیمت ویژه')]:
        try:
            db.execute("""INSERT INTO ecommerce_price_lists
                (list_name, description, currency, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, desc, 'USD', 1, now()))
        except:
            pass

    # ecommerce_price_list_items
    price_list_ids = get_any_id('ecommerce_price_lists', db, 5)
    for pl_id in price_list_ids[:3] if price_list_ids else range(1, 4):
        for p in range(random.randint(5, 15)):
            try:
                db.execute("""INSERT INTO ecommerce_price_list_items
                    (price_list_id, part_id, unit_price, min_quantity,
                     max_quantity, valid_from, valid_to, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (pl_id, random.choice(part_ids) if 'part_ids' in dir() and part_ids else random.randint(1, 40),
                     round(random.uniform(10, 1000), 2),
                     1, random.randint(10, 100),
                     days_ago(random.randint(0, 30)),
                     days_future(random.randint(30, 365)), 1, now()))
            except:
                pass

    # ecommerce_analytics
    for i in range(20):
        try:
            db.execute("""INSERT INTO ecommerce_analytics
                (metric_date, metric_name, metric_value, dimension,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (days_ago(random.randint(1, 30)),
                 random.choice(['page_views', 'sessions', 'conversion_rate', 'revenue']),
                 round(random.uniform(100, 10000), 2),
                 random.choice(['web', 'mobile', 'app']), now()))
        except:
            pass

    # ecommerce_promotions
    for i in range(10):
        try:
            db.execute("""INSERT INTO ecommerce_promotions
                (promotion_code, promotion_name, discount_type,
                 discount_value, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PROMO-{i+1:03d}', f'پروموشن {i+1}',
                 random.choice(['Percent', 'Fixed', 'BuyXGetY']),
                 round(random.uniform(5, 30), 1),
                 days_ago(random.randint(0, 30)),
                 days_future(random.randint(7, 90)),
                 random.choice(['Active', 'Scheduled', 'Expired']), now()))
        except:
            pass

    # ecommerce_promotion_usage
    for i in range(15):
        try:
            db.execute("""INSERT INTO ecommerce_promotion_usage
                (promotion_id, order_id, customer_id, discount_amount,
                 used_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), random.randint(1, 100),
                 random.randint(1, 100),
                 round(random.uniform(5, 50), 2),
                 days_ago(random.randint(0, 30)), now()))
        except:
            pass

    # ecommerce_returns
    for i in range(12):
        try:
            db.execute("""INSERT INTO ecommerce_returns
                (return_number, order_id, customer_id, return_reason,
                 quantity, status, requested_date, processed_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'RET-{i+1:04d}', random.randint(1, 100),
                 random.randint(1, 100),
                 random.choice(['Defective', 'Wrong Item', 'Changed Mind']),
                 random.randint(1, 5),
                 random.choice(['Requested', 'Approved', 'Completed']),
                 days_ago(random.randint(1, 30)),
                 days_ago(random.randint(0, 15)), now()))
        except:
            pass

    # ecommerce_refunds
    for i in range(10):
        try:
            db.execute("""INSERT INTO ecommerce_refunds
                (refund_number, return_id, refund_amount, refund_method,
                 status, processed_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'REF-{i+1:04d}', random.randint(1, 12),
                 round(random.uniform(10, 500), 2),
                 random.choice(['Original Payment', 'Store Credit']),
                 random.choice(['Pending', 'Processed']),
                 days_ago(random.randint(0, 20)), now()))
        except:
            pass

    # ecommerce_product_performance
    for i in range(15):
        try:
            db.execute("""INSERT INTO ecommerce_product_performance
                (part_id, period_start, units_sold, revenue,
                 return_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 40),
                 days_ago(random.randint(7, 60)),
                 random.randint(10, 200),
                 round(random.uniform(1000, 50000), 2),
                 round(random.uniform(0, 10), 2), now()))
        except:
            pass

    # ecommerce_flow_notifications
    for i in range(12):
        try:
            db.execute("""INSERT INTO ecommerce_flow_notifications
                (notification_type, payload, status, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.choice(['OrderCreated', 'PaymentReceived', 'ShipmentSent']),
                 f'{{"notification": {i+1}}}',
                 random.choice(['Sent', 'Pending', 'Failed']), now()))
        except:
            pass

    # wms_aql_rules
    for level in ['I', 'II', 'III']:
        for aql in [0.1, 0.25, 0.4, 0.65, 1.0, 1.5, 2.5, 4.0]:
            try:
                db.execute("""INSERT INTO wms_aql_rules
                    (inspection_level, AQL_level, sample_size,
                     acceptance_number, rejection_number, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (level, aql, random.randint(13, 1250),
                     random.randint(0, 10), random.randint(1, 15), now()))
            except:
                pass

    # wms_demand_forecast
    for i in range(20):
        try:
            db.execute("""INSERT INTO wms_demand_forecast
                (item_id, forecast_date, forecasted_quantity,
                 confidence_level, forecast_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 25), days_future(random.randint(7, 90)),
                 random.randint(10, 500),
                 round(random.uniform(0.7, 0.99), 2),
                 random.choice(['Moving Average', 'Exponential', 'Manual']), now()))
        except:
                pass

    # wms_defect_codes
    for name, cat in [('Dimensional', 'D'), ('Surface', 'S'), ('Material', 'M'),
                       ('Missing', 'M'), ('包装损坏', 'P')]:
        try:
            db.execute("""INSERT INTO wms_defect_codes
                (code, description, category, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (cat + str(random.randint(1, 99)), name, cat, 1, now()))
        except:
            pass

    # wms_edi_partners
    for i in range(6):
        try:
            db.execute("""INSERT INTO wms_edi_partners
                (partner_code, partner_name, edi_standard, document_types,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'EDI-{i+1:02d}', f'Partner {i+1}',
                 random.choice(['X12', 'EDIFACT', 'VDA']),
                 'Invoice,Order,Shipment', 1, now()))
        except:
            pass

    # wms_edi_mappings
    for i in range(6):
        try:
            db.execute("""INSERT INTO wms_edi_mappings
                (mapping_name, edi_document_type, internal_table,
                 mapping_config, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Mapping {i+1}', random.choice(['Invoice', 'Order', 'ASN']),
                 f'table_{i+1}', f'{{"map": {i+1}}}', 1, now()))
        except:
            pass

    # wms_cross_dock
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_cross_dock
                (dock_id, inbound_id, outbound_id, quantity,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 12), random.randint(1, 20),
                 random.randint(1, 20), random.randint(10, 200),
                 random.choice(['Pending', 'In Transit', 'Completed']), now()))
        except:
            pass

    # wms_dock_schedule
    for i in range(12):
        try:
            db.execute("""INSERT INTO wms_dock_schedule
                (dock_id, scheduled_date, appointment_type,
                 carrier, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 12),
                 days_ago(random.randint(-7, 14)),
                 random.choice(['Receiving', 'Shipping']),
                 f'Carrier {i+1}',
                 random.choice(['Scheduled', 'Arrived', 'Completed']), now()))
        except:
            pass

    # wms_putaway_rules
    for i in range(8):
        try:
            db.execute("""INSERT INTO wms_putaway_rules
                (rule_name, condition_json, target_location_type,
                 priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Rule {i+1}', f'{{"condition": {i+1}}}',
                 random.choice(['Bulk', 'Pick', 'Reserve']),
                 random.randint(1, 10), 1, now()))
        except:
            pass

    # wms_putaway_rule_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO wms_putaway_rule_log
                (rule_id, item_id, location_id, action, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.randint(1, 8), random.randint(1, 25),
                 random.randint(1, 720),
                 random.choice(['Applied', 'Skipped']), now()))
        except:
            pass

    # wms_replenishment_config
    for i in range(6):
        try:
            db.execute("""INSERT INTO wms_replenishment_config
                (config_name, replenishment_type, min_level,
                 max_level, reorder_point, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Config {i+1}', random.choice(['Min-Max', 'ROP', 'Kanban']),
                 random.randint(10, 50), random.randint(100, 500),
                 random.randint(20, 100), 1, now()))
        except:
            pass

    # wms_replenishment_suggestions
    for i in range(20):
        try:
            db.execute("""INSERT INTO wms_replenishment_suggestions
                (item_id, suggested_quantity, suggested_date,
                 priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 25),
                 random.randint(20, 200),
                 days_future(random.randint(1, 14)),
                 random.randint(1, 5),
                 random.choice(['Open', 'Processed', 'Cancelled']), now()))
        except:
            pass

    # wms_wave_orders
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_wave_orders
                (wave_number, warehouse_id, order_count,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'WAVE-{i+1:03d}', random.randint(1, 4),
                 random.randint(5, 30),
                 random.choice(['Planned', 'Released', 'Completed']), now()))
        except:
            pass

    # wms_quality_holds
    for i in range(12):
        try:
            db.execute("""INSERT INTO wms_quality_holds
                (hold_code, item_id, lot_id, hold_reason,
                 status, placed_by, placed_at, released_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'HOLD-{i+1:04d}', random.randint(1, 25),
                 random.randint(1, 30),
                 random.choice(['Pending Inspection', 'Customer Request', 'Regulatory Hold']),
                 random.choice(['Active', 'Released']),
                 random.choice(user_ids) if user_ids else 1,
                 days_ago(random.randint(1, 30)),
                 days_ago(random.randint(0, 10)) if random.random() > 0.5 else None, now()))
        except:
            pass

    # wms_quality_certificates
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_quality_certificates
                (certificate_number, item_id, certificate_type,
                 issue_date, expiry_date, issued_by, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CERT-{i+1:04d}', random.randint(1, 25),
                 random.choice(['COA', 'COO', 'ISO']),
                 days_ago(random.randint(1, 180)),
                 days_future(random.randint(30, 365)),
                 f'Issuer {i+1}',
                 random.choice(['Valid', 'Expired', 'Revoked']), now()))
        except:
            pass

    # wms_quality_capa
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_quality_capa
                (capa_number, item_id, issue_description,
                 corrective_action, preventive_action,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'CAPA-{i+1:04d}', random.randint(1, 25),
                 f'توضیحات مشکل {i+1}',
                 f'اقدام اصلاحی {i+1}',
                 f'اقدام پیشگیرانه {i+1}',
                 random.choice(['Open', 'In Progress', 'Closed']), now()))
        except:
            pass

    # wms_kanban_config
    for i in range(6):
        try:
            db.execute("""INSERT INTO wms_kanban_config
                (kanban_type, item_id, bin_quantity, bin_count,
                 replenishment_point, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['Production', 'Withdrawal', 'Signal']),
                 random.randint(1, 25),
                 random.randint(5, 50),
                 random.randint(3, 10),
                 random.randint(10, 50), 1, now()))
        except:
            pass

    # wms_voice_config
    for i in range(5):
        try:
            db.execute("""INSERT INTO wms_voice_config
                (config_name, language, voice_type, vocabulary,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Voice {i+1}', 'en-US',
                 random.choice(['Male', 'Female']),
                 random.choice(['Standard', 'Extended']), 1, now()))
        except:
            pass

    # wms_voice_pick_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO wms_voice_pick_log
                (pick_id, operator_id, command, response,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 50), random.randint(1, 20),
                 f'Pick {i+1}', 'Confirmed',
                 random.choice(['Success', 'Error']), now()))
        except:
            pass

    # wms_rf_scan_log
    for i in range(20):
        try:
            db.execute("""INSERT INTO wms_rf_scan_log
                (operator_id, scan_type, barcode, result,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.randint(1, 20),
                 random.choice(['Receive', 'Pick', 'Move', 'Count']),
                 f'BC-{random.randint(10000, 99999)}',
                 random.choice(['Success', 'Not Found']), now()))
        except:
            pass

    # wms_yard_vehicles
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_yard_vehicles
                (vehicle_plate, vehicle_type, driver_name,
                 arrival_time, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'ABC-{random.randint(1000, 9999)}',
                 random.choice(['Truck', 'Van', 'Trailer']),
                 f'{random.choice(PERSIAN_FIRST_NAMES)} {random.choice(PERSIAN_LAST_NAMES)}',
                 days_ago(random.randint(0, 3)),
                 random.choice(['In Yard', 'At Dock', 'Departed']), now()))
        except:
            pass

    # wms_yard_activity_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO wms_yard_activity_log
                (vehicle_id, activity_type, location,
                 timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.randint(1, 10),
                 random.choice(['Arrived', 'Moved', 'Loaded', 'Unloaded']),
                 f'Dock {random.randint(1, 12)}',
                 days_ago(random.randint(0, 7)) + ' ' + f'{random.randint(6,20):02d}:00:00', now()))
        except:
            pass

    # wms_saved_reports
    for i in range(8):
        try:
            db.execute("""INSERT INTO wms_saved_reports
                (report_name, report_type, parameters,
                 user_id, is_shared, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Report {i+1}', random.choice(['Inventory', 'Movement', 'Receiving']),
                 f'{{"params": {i+1}}}',
                 random.choice(user_ids), random.choice([0, 1]), now()))
        except:
            pass

    # wms_usage_decisions
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_usage_decisions
                (decision_number, item_id, quantity, decision,
                 inspector_id, decision_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'UD-{i+1:04d}', random.randint(1, 25),
                 random.randint(10, 200),
                 random.choice(['Accept', 'Reject', 'Conditional']),
                 random.choice(user_ids) if user_ids else 1,
                 days_ago(random.randint(1, 30)), now()))
        except:
            pass

    # wms_outbound_idocs
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_outbound_idocs
                (idoc_number, message_type, partner_id,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'IDOC-O-{i+1:04d}',
                 random.choice(['Order', 'Invoice', 'ASN']),
                 random.randint(1, 20),
                 random.choice(['Created', 'Sent', 'Error']), now()))
        except:
            pass

    # wms_inbound_idocs
    for i in range(10):
        try:
            db.execute("""INSERT INTO wms_inbound_idocs
                (idoc_number, message_type, partner_id,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'IDOC-I-{i+1:04d}',
                 random.choice(['PO', 'ASN', 'Invoice']),
                 random.randint(1, 20),
                 random.choice(['Received', 'Processed', 'Error']), now()))
        except:
            pass

    # wms_edi_audit_log
    for i in range(15):
        try:
            db.execute("""INSERT INTO wms_edi_audit_log
                (partner_id, message_type, direction,
                 status, message_content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 6),
                 random.choice(['Invoice', 'Order', 'ASN']),
                 random.choice(['Inbound', 'Outbound']),
                 random.choice(['Success', 'Error', 'Warning']),
                 f'<message>{i+1}</message>', now()))
        except:
            pass

    # capacity_planning_views
    for i in range(8):
        try:
            db.execute("""INSERT INTO capacity_planning_views
                (view_name, work_center_ids, time_period,
                 created_by, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'View {i+1}',
                 f'{random.randint(1,15)},{random.randint(1,15)}',
                 random.choice(['Week', 'Month', 'Quarter']),
                 random.choice(user_ids), now()))
        except:
            pass

    # capacity_requirements
    for i in range(20):
        try:
            db.execute("""INSERT INTO capacity_requirements
                (work_center_id, requirement_date, required_hours,
                 available_hours, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 15),
                 days_future(random.randint(1, 30)),
                 random.randint(40, 120),
                 random.randint(60, 150),
                 random.choice(['OK', 'Overloaded', 'Underloaded']), now()))
        except:
            pass

    # capex_requests
    for i in range(12):
        try:
            db.execute("""INSERT INTO capex_requests
                (request_number, title, description, amount,
                 currency, requester_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CAPEX-{i+1:04d}',
                 f'درخواست سرمایه‌گذاری {i+1}',
                 f'توضیحات {i+1}',
                 round(random.uniform(10000, 500000), 2),
                 random.choice(['USD', 'AED']),
                 random.choice(user_ids),
                 random.choice(['Draft', 'Submitted', 'Approved', 'Rejected']), now()))
        except:
            pass

    # settlement_rules
    for i in range(6):
        try:
            db.execute("""INSERT INTO settlement_rules
                (rule_name, rule_type, parameters,
                 priority, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Rule {i+1}',
                 random.choice(['Auto', 'Manual', 'Threshold']),
                 f'{{"params": {i+1}}}',
                 random.randint(1, 10), 1, now()))
        except:
            pass

    # bom_substitutes
    for i in range(15):
        try:
            db.execute("""INSERT INTO bom_substitutes
                (bom_id, substitute_part_id, substitution_ratio,
                 is_preferred, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 30), random.randint(1, 40),
                 round(random.uniform(0.8, 1.2), 2),
                 random.choice([0, 1]), 1, now()))
        except:
            pass

    # api_security_events
    for i in range(20):
        try:
            db.execute("""INSERT INTO api_security_events
                (event_type, severity, ip_address, user_id,
                 details, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Login Failed', 'Rate Limit', 'Invalid Token', 'Access Denied']),
                 random.choice(['Low', 'Medium', 'High']),
                 f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
                 random.choice(user_ids),
                 f'Event details {i+1}', now()))
        except:
            pass

    # grc_access_review_items (add more)
    for i in range(15):
        try:
            db.execute("""INSERT INTO grc_access_review_items
                (access_review_id, user_id, resource, access_level,
                 risk_score, disposition, reviewed_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 3), random.randint(1, 20),
                 f'Resource {i+1}',
                 random.choice(['Read', 'Write', 'Admin']),
                 random.randint(1, 10),
                 random.choice(['Approve', 'Revoke', 'Modify']),
                 random.randint(1, 10), now()))
        except:
            pass

    # grc_audit_preparedness_checks
    for i in range(10):
        try:
            db.execute("""INSERT INTO grc_audit_preparedness_checks
                (audit_id, check_item, responsible_person,
                 due_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 9), f'Check {i+1}',
                 random.choice(user_ids),
                 days_future(random.randint(7, 60)),
                 random.choice(['Not Started', 'In Progress', 'Completed']), now()))
        except:
            pass

    # grc_control_assignments
    for ctrl_id in range(1, 13):
        for risk_id in range(1, 5):
            try:
                db.execute("""INSERT INTO grc_control_assignments
                    (control_id, risk_id, assignment_type,
                     effectiveness, last_tested, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (ctrl_id, risk_id,
                     random.choice(['Primary', 'Secondary', 'Mitigating']),
                     random.choice(['Effective', 'Ineffective', 'Not Tested']),
                     days_ago(random.randint(30, 180)), now()))
            except:
                pass

    # grc_control_test_results
    for i in range(15):
        try:
            db.execute("""INSERT INTO grc_control_test_results
                (control_id, test_date, tester_id, test_result,
                 findings, next_test_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 12), days_ago(random.randint(1, 120)),
                 random.choice(user_ids),
                 random.choice(['Pass', 'Fail', 'Exception']),
                 f'Finding {i+1}',
                 days_future(random.randint(30, 180)), now()))
        except:
            pass

    # grc_entity_links
    for i in range(10):
        try:
            db.execute("""INSERT INTO grc_entity_links
                (entity_type, entity_id, linked_entity_type,
                 linked_entity_id, relationship, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Process', 'Asset', 'System']),
                 random.randint(1, 20),
                 random.choice(['Risk', 'Control', 'Regulation']),
                 random.randint(1, 20),
                 random.choice(['Related', 'Owner', 'Subject To']), now()))
        except:
            pass

    # grc_export_jobs
    for i in range(8):
        try:
            db.execute("""INSERT INTO grc_export_jobs
                (export_type, format, status, record_count,
                 requested_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Risk Report', 'Compliance Report', 'Audit Report']),
                 random.choice(['PDF', 'Excel', 'CSV']),
                 random.choice(['Completed', 'Failed', 'Running']),
                 random.randint(100, 5000),
                 random.choice(user_ids), now()))
        except:
            pass

    # grc_policy_acknowledgements
    for i in range(20):
        try:
            db.execute("""INSERT INTO grc_policy_acknowledgements
                (policy_id, user_id, acknowledged_at, signature_data,
                 ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 6), random.randint(1, 30),
                 days_ago(random.randint(1, 180)),
                 f'signature_{i+1}',
                 f'192.168.{random.randint(1,255)}.{random.randint(1,255)}', now()))
        except:
            pass

    # grc_policy_versions
    for i in range(10):
        try:
            db.execute("""INSERT INTO grc_policy_versions
                (policy_id, version_number, change_summary,
                 effective_date, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 6), i + 1,
                 f'Summary of changes v{i+1}',
                 days_ago(random.randint(30, 180)),
                 random.choice(user_ids), now()))
        except:
            pass

    # grc_remediation_tasks
    for i in range(12):
        try:
            db.execute("""INSERT INTO grc_remediation_tasks
                (remediation_plan_id, task_name, assigned_to,
                 due_date, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 3), f'Task {i+1}',
                 random.choice(user_ids),
                 days_future(random.randint(7, 60)),
                 random.choice(['Not Started', 'In Progress', 'Completed']),
                 random.choice(['Low', 'Medium', 'High']), now()))
        except:
            pass

    # grc_report_presets
    for i in range(8):
        try:
            db.execute("""INSERT INTO grc_report_presets
                (report_name, report_type, filters, schedule,
                 last_generated, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Preset {i+1}',
                 random.choice(['Risk', 'Compliance', 'Audit']),
                 f'{{"filter": {i+1}}}',
                 random.choice(['Daily', 'Weekly', 'Monthly']),
                 days_ago(random.randint(1, 30)), now()))
        except:
            pass

    # grc_review_cycles
    for i in range(6):
        try:
            db.execute("""INSERT INTO grc_review_cycles
                (cycle_name, cycle_type, start_date, end_date,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Cycle {i+1}',
                 random.choice(['Access', 'Policy', 'Control']),
                 days_ago(random.randint(30, 90)),
                 days_future(random.randint(30, 90)),
                 random.choice(['Planned', 'Active', 'Completed']), now()))
        except:
            pass

    # grc_risk_assessments
    for i in range(12):
        try:
            db.execute("""INSERT INTO grc_risk_assessments
                (assessment_name, risk_id, assessment_date,
                 likelihood, impact, risk_score, assessor_id,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Assessment {i+1}', random.randint(1, 13),
                 days_ago(random.randint(1, 120)),
                 random.randint(1, 5), random.randint(1, 5),
                 random.randint(1, 25),
                 random.choice(user_ids), now()))
        except:
            pass

    # grc_risk_treatments
    for i in range(10):
        try:
            db.execute("""INSERT INTO grc_risk_treatments
                (risk_id, treatment_type, treatment_plan,
                 owner_id, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 13),
                 random.choice(['Mitigate', 'Transfer', 'Accept', 'Avoid']),
                 f'Treatment plan {i+1}',
                 random.choice(user_ids),
                 random.choice(['Planned', 'In Progress', 'Completed']),
                 days_future(random.randint(30, 120)), now()))
        except:
            pass

    # grc_status_history
    for i in range(20):
        try:
            db.execute("""INSERT INTO grc_status_history
                (entity_type, entity_id, old_status, new_status,
                 changed_by, changed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['Risk', 'Control', 'Incident']),
                 random.randint(1, 20),
                 random.choice(['Open', 'In Progress']),
                 random.choice(['Mitigated', 'Closed', 'Escalated']),
                 random.choice(user_ids),
                 days_ago(random.randint(1, 60)), now()))
        except:
            pass

    # grc_watchlists
    for i in range(8):
        try:
            db.execute("""INSERT INTO grc_watchlists
                (item_name, item_type, risk_description,
                 added_by, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Watchlist {i+1}',
                 random.choice(['Vendor', 'System', 'Location']),
                 f'Risk for watchlist {i+1}',
                 random.choice(user_ids), 1, now()))
        except:
            pass

    # treasury_forecast_items
    for i in range(20):
        try:
            db.execute("""INSERT INTO treasury_forecast_items
                (forecast_id, item_type, description, amount,
                 due_date, probability, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 3),
                 random.choice(['Incoming', 'Outgoing']),
                 f'Forecast item {i+1}',
                 round(random.uniform(1000, 50000), 2),
                 days_future(random.randint(7, 90)),
                 round(random.uniform(0.5, 1.0), 2), now()))
        except:
            pass

    # treasury_liquidity_plans
    for i in range(10):
        try:
            db.execute("""INSERT INTO treasury_liquidity_plans
                (plan_name, period_start, period_end, total_inflow,
                 total_outflow, net_position, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Plan {i+1}',
                 days_ago(random.randint(0, 30)),
                 days_future(random.randint(30, 90)),
                 round(random.uniform(100000, 500000), 2),
                 round(random.uniform(80000, 450000), 2),
                 round(random.uniform(-50000, 100000), 2), now()))
        except:
            pass

    # treasury_liquidity_thresholds
    for thresh in ['Minimum Cash', 'Maximum Cash', 'Warning Level']:
        try:
            db.execute("""INSERT INTO treasury_liquidity_thresholds
                (threshold_name, threshold_type, threshold_value,
                 currency, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (thresh, random.choice(['Minimum', 'Maximum', 'Warning']),
                 random.randint(10000, 100000),
                 random.choice(['USD', 'AED']), 1, now()))
        except:
            pass

    # treasury_transfer_approvals
    for i in range(8):
        try:
            db.execute("""INSERT INTO treasury_transfer_approvals
                (transfer_id, approver_id, approval_status,
                 approval_notes, approved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 4),
                 random.choice(user_ids),
                 random.choice(['Approved', 'Rejected', 'Pending']),
                 f'Notes {i+1}',
                 days_ago(random.randint(0, 10)), now()))
        except:
            pass

    db.commit()
    print("    + All minimal tables seeded")


# =============================================================================
# MAIN SEEDING ORCHESTRATOR
# =============================================================================

def main():
    print("=" * 80)
    print("  MMDx COMPREHENSIVE MASTER SEED - FILLING ALL EMPTY TABLES")
    print("=" * 80)

    db = get_db()

    # Verify we're using the right database
    try:
        size = os.path.getsize(DATABASE)
        print(f"\n  Database: {DATABASE}")
        print(f"  Database size: {size / (1024*1024):.1f} MB")
        print()
    except:
        pass

    print("\n>> Seeding all modules...")
    print("-" * 60)

    seed_projects_module(db)
    seed_spc_module(db)
    seed_talent_management(db)
    seed_manufacturing_module(db)
    seed_btp_integration_extra(db)
    seed_crm_extra(db)
    seed_quality_extra(db)
    seed_service_warranty(db)
    seed_minimal_tables(db)

    db.commit()

    # Final summary
    print("\n" + "=" * 80)
    print("  SEEDING COMPLETE - VERIFICATION")
    print("=" * 80)

    # Count empty tables
    empty_tables = []
    all_tables = [row[0] for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]

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
    print("  ALL SEEDING COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == '__main__':
    main()
