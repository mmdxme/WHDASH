"""
Talent Management Sample Data Seed Script
========================================
This script populates the Talent Management module with realistic sample data.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_talent_data():
    """Seed comprehensive talent management sample data."""
    conn = get_db()
    try:
        print("Seeding Talent Management data...")
        
        # Seed competency categories
        seed_competency_categories(conn)
        
        # Seed competencies
        seed_competencies(conn)
        
        # Seed talent profiles for existing employees
        seed_talent_profiles(conn)
        
        # Seed employee competencies
        seed_employee_competencies(conn)
        
        # Seed talent pools
        seed_talent_pools(conn)
        
        # Seed critical roles
        seed_critical_roles(conn)
        
        # Seed succession plans
        seed_succession_plans(conn)
        
        # Seed development plans
        seed_development_plans(conn)
        
        # Seed talent reviews
        seed_talent_reviews(conn)
        
        # Seed mentoring assignments
        seed_mentoring_assignments(conn)
        
        # Seed career paths
        seed_career_paths(conn)
        
        # Seed talent settings
        seed_talent_settings(conn)
        
        conn.commit()
        print("Talent Management data seeded successfully!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error seeding talent data: {e}")
        return False
    finally:
        conn.close()


def seed_competency_categories(conn):
    """Seed competency categories."""
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


def seed_competencies(conn):
    """Seed competencies."""
    competencies = [
        ('Strategic Thinking', 'التفكير الاستراتيجي', 'تفکر استراتژیک', 'Strategic Thinking', 'रणनीतिक सोच', 'Pensamiento Estratégico', '战略思维', 'Strategisches Denken', 1, 'Strategic ability to see the big picture', 1, 1, 1, 1.5, 'Assessment Center', 1),
        ('Team Leadership', 'قيادة الفريق', 'رهبری تیم', 'Team Leadership', 'टीम लीडरशिप', 'Liderazgo de Equipo', '团队领导', 'Teamführung', 1, 'Lead teams effectively', 1, 1, 1, 1.3, '360 Feedback', 1),
        ('Decision Making', 'اتخاذ القرارات', 'تصمیم‌گیری', 'Decision Making', 'निर्णय लेना', 'Toma de Decisiones', '决策能力', 'Entscheidungsfindung', 1, 'Make effective decisions', 1, 1, 0, 1.2, 'Case Study', 1),
        ('Change Management', 'إدارة التغيير', 'مدیریت تغییر', 'Change Management', 'परिवर्तन प्रबंधन', 'Gestión del Cambio', '变革管理', 'Veränderungsmanagement', 1, 'Lead change initiatives', 1, 1, 1, 1.1, 'Workshop Assessment', 1),
        ('Coaching & Mentoring', 'التدريب والإرشاد', 'مربیگری', 'Coaching & Mentoring', 'कोचिंग और मेंटरिंग', 'Coaching y Mentoría', '辅导与指导', 'Coaching & Mentoring', 1, 'Develop others', 1, 0, 1, 1.0, '360 Feedback', 1),
        ('Data Analysis', 'تحليل البيانات', 'تحلیل داده‌ها', 'Data Analysis', 'डेटा विश्लेषण', 'Análisis de Datos', '数据分析', 'Datenanalyse', 2, 'Analyze data effectively', 1, 1, 0, 1.4, 'Technical Test', 1),
        ('Technical Expertise', 'الخبرة التقنية', 'تخصص فنی', 'Technical Expertise', 'तकनीकी विशेषज्ञता', 'Experiencia Técnica', '专业技术', 'Technische Expertise', 2, 'Deep technical knowledge', 1, 1, 0, 1.6, 'Portfolio Review', 1),
        ('Digital Literacy', 'المحو الحرية الرقمية', 'سواد دیجیتال', 'Digital Literacy', 'डिजिटल साक्षरता', 'Alfabetización Digital', '数字化素养', 'Digitalkompetenz', 2, 'Proficiency with digital tools', 1, 0, 0, 1.1, 'Self-Assessment', 1),
        ('Financial Literacy', 'اللمام المالي', 'سواد مالی', 'Financial Literacy', 'वित्तीय साक्षरता', 'Alfabetización Financiera', '财务素养', 'Finanzwissen', 3, 'Understanding financial principles', 1, 1, 0, 1.3, 'Business Case Analysis', 1),
        ('Market Awareness', 'الوعي بالسوق', 'آگاهی از بازار', 'Market Awareness', 'बाजार जागरूकता', 'Conciencia del Mercado', '市场意识', 'Marktbewusstsein', 3, 'Know market trends', 1, 1, 0, 1.2, 'Market Analysis', 1),
        ('Verbal Communication', 'التواصل اللفظي', 'ارتباط کلامی', 'Verbal Communication', 'मौखिक संचार', 'Comunicación Verbal', '口头沟通', 'Mündliche Kommunikation', 4, 'Communicate verbally', 1, 0, 0, 1.0, 'Presentation Assessment', 1),
        ('Written Communication', 'التواصل الكتابي', 'ارتباط کتبی', 'Written Communication', 'लिखित संचार', 'Comunicación Escrita', '书面沟通', 'Schriftliche Kommunikation', 4, 'Write effectively', 1, 0, 0, 1.0, 'Writing Sample', 1),
        ('Analytical Thinking', 'التفكير التحليلي', 'تفکر تحلیلی', 'Analytical Thinking', 'विश्लेषणात्मक सोच', 'Pensamiento Analítico', '分析思维', 'Analytisches Denken', 5, 'Break down complex problems', 1, 1, 0, 1.3, 'Case Study', 1),
        ('Creativity', 'الإبداع', 'خلاقیت', 'Creativity', 'रचनात्मकता', 'Creatividad', '创造力', 'Kreativität', 5, 'Generate innovative solutions', 1, 0, 0, 1.1, 'Innovation Workshop', 1),
        ('Collaboration', 'التعاون', 'همکاری', 'Collaboration', 'सहयोग', 'Colaboración', '协作能力', 'Zusammenarbeit', 6, 'Work effectively with others', 1, 0, 0, 1.0, 'Team Activity', 1),
        ('Conflict Resolution', 'حل النزاعات', 'حل تعارض', 'Conflict Resolution', 'संघर्ष समाधान', 'Resolución de Conflictos', '冲突解决', 'Konfliktlösung', 6, 'Resolve conflicts', 1, 1, 0, 1.0, 'Behavioral Interview', 1),
        ('Innovation Mindset', 'عقلية الابتكار', 'ذهن نوآوری', 'Innovation Mindset', 'नवाचार मानसिकता', 'Mentalidad de Innovación', '创新思维', 'Innovations mindset', 7, 'Embrace new ideas', 1, 0, 1, 1.1, 'Innovation Assessment', 1),
        ('Customer Orientation', 'التوجه نحو العميل', 'تمرکز بر مشتری', 'Customer Orientation', 'ग्राहक उन्मुखीकरण', 'Orientación al Cliente', '客户导向', 'Kundenorientierung', 8, 'Meet customer needs', 1, 0, 0, 1.2, 'Customer Scenario', 1),
    ]
    
    for comp in competencies:
        conn.execute("""
            INSERT OR IGNORE INTO tm_competencies 
            (name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, category_id, description, 
             is_technical, is_leadership, is_core, weight_factor, assessment_method, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, comp)


def seed_talent_profiles(conn):
    """Seed talent profiles for active employees."""
    # Get active employees
    employees = conn.execute("""
        SELECT id FROM hr_employees WHERE status = 'Active' LIMIT 50
    """).fetchall()
    
    potential_ratings = ['Very High', 'High', 'Medium', 'Low']
    performance_ratings = ['Exceeds', 'Meets', 'Below']
    readiness_levels = ['Ready Now', '6 Months', '1 Year', '2 Years', '3+ Years']
    
    for emp in employees:
        employee_id = emp['id']
        
        # Check if profile already exists
        existing = conn.execute("""
            SELECT id FROM tm_talent_profiles WHERE employee_id = ?
        """, (employee_id,)).fetchone()
        
        if existing:
            continue
        
        # Assign random ratings with weighting toward middle values
        import random
        potential = random.choices(
            potential_ratings, 
            weights=[15, 35, 40, 10]
        )[0]
        
        performance = random.choices(
            performance_ratings,
            weights=[30, 55, 15]
        )[0]
        
        readiness = random.choices(
            readiness_levels,
            weights=[15, 20, 30, 25, 10]
        )[0]
        
        hi_po = potential in ['Very High', 'High']
        succession_candidate = readiness in ['Ready Now', '6 Months', '1 Year'] and performance in ['Exceeds', 'Meets']
        flight_risk = random.random() < 0.05  # 5% flight risk
        
        conn.execute("""
            INSERT INTO tm_talent_profiles 
            (employee_id, potential_rating, potential_score, readiness_level, readiness_score,
             performance_rating, performance_score, risk_level, flight_risk, hi_po, 
             succession_candidate, development_priority, profile_completeness, last_reviewed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id,
            potential, {'Very High': 5, 'High': 4, 'Medium': 3, 'Low': 2}.get(potential, 3),
            readiness, {'Ready Now': 5, '6 Months': 4, '1 Year': 3, '2 Years': 2, '3+ Years': 1}.get(readiness, 3),
            performance, {'Exceeds': 5, 'Meets': 4, 'Below': 3}.get(performance, 3),
            'Medium' if flight_risk else 'Low',
            1 if flight_risk else 0,
            1 if hi_po else 0,
            1 if succession_candidate else 0,
            2 if potential in ['Very High', 'High'] else 3,
            random.randint(50, 100),
            datetime.now().date().isoformat()
        ))
    
    print(f"Seeded talent profiles for {len(employees)} employees")


def seed_employee_competencies(conn):
    """Seed employee competency assessments."""
    employees = conn.execute("SELECT id FROM hr_employees WHERE status = 'Active' LIMIT 30").fetchall()
    competencies = conn.execute("SELECT id FROM tm_competencies").fetchall()
    assessors = conn.execute("SELECT id FROM hr_employees LIMIT 5").fetchall()
    
    if not competencies:
        return
    
    for emp in employees:
        # Assign 5-10 random competencies per employee
        num_comps = random.randint(5, min(10, len(competencies)))
        assigned = random.sample(competencies, num_comps)
        
        for comp in assigned:
            # Check if already assessed
            existing = conn.execute("""
                SELECT id FROM tm_employee_competencies 
                WHERE employee_id = ? AND competency_id = ?
            """, (emp['id'], comp['id'])).fetchone()
            
            if existing:
                continue
            
            current_level = random.randint(2, 5)
            required_level = random.randint(3, 5)
            gap = current_level - required_level
            
            assessor = random.choice(assessors)['id'] if assessors else None
            
            conn.execute("""
                INSERT INTO tm_employee_competencies 
                (employee_id, competency_id, proficiency_level, proficiency_name, required_level, gap_score,
                 assessed_by, assessment_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
            """, (
                emp['id'], comp['id'],
                current_level, f'Level {current_level}',
                required_level, gap,
                assessor,
                datetime.now().date().isoformat()
            ))


def seed_talent_pools(conn):
    """Seed talent pools."""
    pools = [
        ('High Potential Pool', ' pools', 'Future Leaders', 'High potential employees being developed', '{"performance_min": 4, "potential_min": 3}', '#8b5cf6', 'fa-star', 1, 0),
        ('Successor Pool', ' pools', 'Succession', 'Employees being prepared as successors', '{"succession_candidate": 1}', '#10b981', 'fa-user-clock', 1, 1),
        ('Critical Role Backup', ' pools', 'Critical', 'Backup for critical positions', '{"is_backup_candidate": 1}', '#f59e0b', 'fa-shield-alt', 1, 1),
        ('Future Leaders', ' pools', 'Leadership', 'High-performers for executive roles', '{"performance_min": 4}', '#6366f1', 'fa-crown', 1, 0),
        ('Specialist Talent', ' pools', 'Specialist', 'Technical specialists and SMEs', '{"technical_expertise": 4}', '#ec4899', 'fa-gem', 1, 0),
    ]
    
    for pool in pools:
        conn.execute("""
            INSERT OR IGNORE INTO tm_talent_pools 
            (name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de, pool_type, description, 
             criteria_json, color_code, icon_class, is_active, requires_approval)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pool)
    
    # Add some Hi-Po employees to pools
    hipo_employees = conn.execute("""
        SELECT employee_id FROM tm_talent_profiles WHERE hi_po = 1 LIMIT 10
    """).fetchall()
    
    hipo_pool = conn.execute("SELECT id FROM tm_talent_pools WHERE pool_type = 'HiPo'").fetchone()
    successor_pool = conn.execute("SELECT id FROM tm_talent_pools WHERE pool_type = 'Succession'").fetchone()
    
    if hipo_pool and successor_pool:
        for emp in hipo_employees:
            # Add to Hi-Po pool
            conn.execute("""
                INSERT OR IGNORE INTO tm_talent_pool_members 
                (pool_id, employee_id, joined_date, status, membership_type)
                VALUES (?, ?, date('now'), 'Active', 'Manual')
            """, (hipo_pool['id'], emp['employee_id']))
            
            # Add to Successor pool if succession candidate
            is_successor = conn.execute("""
                SELECT succession_candidate FROM tm_talent_profiles WHERE employee_id = ?
            """, (emp['employee_id'],)).fetchone()
            
            if is_successor and is_successor['succession_candidate']:
                conn.execute("""
                    INSERT OR IGNORE INTO tm_talent_pool_members 
                    (pool_id, employee_id, joined_date, status, membership_type)
                    VALUES (?, ?, date('now'), 'Active', 'Manual')
                """, (successor_pool['id'], emp['employee_id']))


def seed_critical_roles(conn):
    """Seed critical roles."""
    # Get positions to designate as critical
    positions = conn.execute("""
        SELECT p.id, p.title, d.id as dept_id, e.id as incumbent_id
        FROM hr_positions p
        LEFT JOIN hr_departments d ON p.department_id = d.id
        LEFT JOIN hr_employee_employment ee ON p.id = ee.position_id AND ee.is_primary = 1
        LEFT JOIN hr_employees e ON ee.employee_id = e.id
        WHERE p.status = 'Active'
        LIMIT 10
    """).fetchall()
    
    criticality_levels = ['Critical', 'High', 'Medium']
    
    for i, pos in enumerate(positions[:6]):  # Mark first 6 as critical
        # Check if already exists
        existing = conn.execute("""
            SELECT id FROM tm_critical_roles WHERE position_id = ?
        """, (pos['id'],)).fetchone()
        
        if existing:
            continue
        
        criticality = criticality_levels[0] if i < 2 else criticality_levels[1] if i < 4 else criticality_levels[2]
        
        conn.execute("""
            INSERT INTO tm_critical_roles 
            (position_id, department_id, incumbent_id, role_type, criticality_level, 
             backup_required, status, last_reviewed)
            VALUES (?, ?, ?, 'Critical', ?, 1, 'Active', ?)
        """, (
            pos['id'], pos['dept_id'], pos['incumbent_id'],
            criticality,
            datetime.now().date().isoformat()
        ))


def seed_succession_plans(conn):
    """Seed succession plans for critical roles."""
    critical_roles = conn.execute("SELECT id FROM tm_critical_roles WHERE status = 'Active'").fetchall()
    
    if not critical_roles:
        return
    
    # Get potential successors (high performers with good potential)
    successors = conn.execute("""
        SELECT tp.employee_id, tp.potential_rating, tp.readiness_level
        FROM tm_talent_profiles tp
        JOIN hr_employees e ON tp.employee_id = e.id
        WHERE e.status = 'Active' 
        AND tp.potential_rating IN ('Very High', 'High')
        LIMIT 20
    """).fetchall()
    
    readiness_map = {
        'Ready Now': ('Ready Now', 4),
        '6 Months': ('6 Months', 3),
        '1 Year': ('1 Year', 2),
        '2 Years': ('2 Years', 1)
    }
    
    for i, cr in enumerate(critical_roles[:4]):  # Create plans for first 4 critical roles
        if i < len(successors):
            successor = successors[i]
            readiness = successor['readiness_level'] or '1 Year'
            readiness_info = readiness_map.get(readiness, ('1 Year', 2))
            
            conn.execute("""
                INSERT INTO tm_succession_plans 
                (critical_role_id, employee_id, successor_id, readiness_level, readiness_score,
                 readiness_horizon, status, effective_from)
                VALUES (?, ?, ?, ?, ?, ?, 'Approved', date('now'))
            """, (
                cr['id'],
                successor['employee_id'],
                successor['employee_id'],
                readiness_info[0], readiness_info[1],
                readiness,
                'Approved'
            ))
    
    print(f"Seeded succession plans for {min(4, len(critical_roles))} critical roles")


def seed_development_plans(conn):
    """Seed development plans."""
    employees = conn.execute("""
        SELECT tp.employee_id, e.first_name
        FROM tm_talent_profiles tp
        JOIN hr_employees e ON tp.employee_id = e.id
        WHERE e.status = 'Active'
        LIMIT 15
    """).fetchall()
    
    managers = conn.execute("SELECT id FROM hr_employees LIMIT 5").fetchall()
    
    goals_titles = [
        'Executive Leadership Program',
        'Strategic Planning Certification',
        'Advanced Technical Training',
        'Cross-Functional Project Leadership',
        'Presentation Skills Workshop',
        'Industry Conference Speaking',
        'Mentoring Certification',
        'Data Analytics Certification'
    ]
    
    for emp in employees[:10]:
        manager = random.choice(managers)['id'] if managers else None
        
        conn.execute("""
            INSERT INTO tm_development_plans 
            (employee_id, plan_year, plan_title, manager_id, status, priority_level,
             start_date, end_date, total_goals, completed_goals, completion_percentage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            emp['employee_id'],
            2026,
            f"IDP - {emp['first_name']}",
            manager,
            random.choice(['Draft', 'In Progress', 'Completed']),
            'Medium',
            '2026-01-01',
            '2026-12-31',
            random.randint(3, 6),
            random.randint(0, 3),
            random.randint(0, 100)
        ))
        
        # Add some goals
        plan = conn.execute("SELECT last_insert_rowid() as id").fetchone()
        num_goals = random.randint(3, 5)
        for j in range(num_goals):
            conn.execute("""
                INSERT INTO tm_development_goals 
                (plan_id, goal_title, goal_description, priority, status, target_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                plan['id'],
                random.choice(goals_titles),
                f"Development goal {j+1} description",
                random.choice(['High', 'Medium', 'Low']),
                random.choice(['Not Started', 'In Progress', 'Completed']),
                f"2026-{random.randint(6, 12):02d}-{random.randint(1, 28):02d}"
            ))
    
    print(f"Seeded development plans for {len(employees[:10])} employees")


def seed_talent_reviews(conn):
    """Seed talent review cycles."""
    # Check if review already exists
    existing = conn.execute("""
        SELECT id FROM tm_talent_reviews WHERE cycle_name LIKE '%2026%'
    """).fetchone()
    
    if not existing:
        conn.execute("""
            INSERT INTO tm_talent_reviews 
            (cycle_name, period_start, period_end, status, review_type,
             calibration_date, participants_count, completed_count, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            '2026 Annual Talent Review',
            '2025-01-01',
            '2025-12-31',
            'In Progress',
            'Annual',
            '2026-03-15',
            10,
            7,
            1
        ))
        
        review_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()['id']
        
        # Add participants
        employees = conn.execute("""
            SELECT tp.employee_id, tp.potential_rating, tp.performance_rating, tp.readiness_level
            FROM tm_talent_profiles tp
            JOIN hr_employees e ON tp.employee_id = e.id
            WHERE e.status = 'Active'
            LIMIT 10
        """).fetchall()
        
        for emp in employees:
            manager = conn.execute("""
                SELECT reporting_to_id FROM hr_employee_employment 
                WHERE employee_id = ? AND is_primary = 1
            """, (emp['employee_id'],)).fetchone()
            
            conn.execute("""
                INSERT INTO tm_talent_review_participants 
                (review_id, employee_id, manager_id, potential_rating, performance_rating,
                 readiness_rating, status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id,
                emp['employee_id'],
                manager['reporting_to_id'] if manager else None,
                emp['potential_rating'],
                emp['performance_rating'],
                emp['readiness_level'],
                random.choice(['Pending', 'Submitted']),
                datetime.now().date().isoformat() if random.random() > 0.3 else None
            ))
        
        print(f"Seeded talent review cycle with {len(employees)} participants")


def seed_mentoring_assignments(conn):
    """Seed mentoring assignments."""
    mentors = conn.execute("""
        SELECT employee_id FROM tm_talent_profiles 
        WHERE potential_rating IN ('Very High', 'High')
        LIMIT 5
    """).fetchall()
    
    mentees = conn.execute("""
        SELECT employee_id FROM tm_talent_profiles 
        WHERE potential_rating = 'Medium'
        LIMIT 8
    """).fetchall()
    
    for i, mentor in enumerate(mentors[:4]):
        if i < len(mentees):
            conn.execute("""
                INSERT INTO tm_mentoring_assignments 
                (mentor_id, mentee_id, start_date, status, objectives, sessions_planned, sessions_completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                mentor['employee_id'],
                mentees[i]['employee_id'],
                '2025-01-01',
                'Active',
                'Leadership development and career guidance',
                12,
                random.randint(3, 8)
            ))
    
    print(f"Seeded mentoring assignments for {min(4, len(mentors))} mentors")


def seed_career_paths(conn):
    """Seed career paths."""
    positions = conn.execute("""
        SELECT id, title FROM hr_positions WHERE status = 'Active' LIMIT 10
    """).fetchall()
    
    if len(positions) >= 3:
        paths = [
            (positions[0]['id'], positions[1]['id'], 'Promotion', 36),
            (positions[1]['id'], positions[2]['id'], 'Promotion', 36),
            (positions[2]['id'], positions[3]['id'] if len(positions) > 3 else positions[0]['id'], 'Promotion', 48),
        ]
        
        for path in paths:
            conn.execute("""
                INSERT OR IGNORE INTO tm_career_paths 
                (name, name_ar, path_type, from_position_id, to_position_id, avg_duration_months, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                f"Path: {positions[0]['title']} to {positions[1]['title']}",
                'مسار ترقية',
                path[2],
                path[0],
                path[1],
                path[3]
            ))
    
    print("Seeded career paths")


def seed_talent_settings(conn):
    """Seed default talent settings."""
    settings = [
        ('potential_rating_scale', '3', 'String', 'Talent', 'Scale for potential ratings', 0),
        ('readiness_horizons', 'Ready Now,6 Months,1 Year,2 Years,3+ Years', 'String', 'Talent', 'Available readiness horizons', 0),
        ('talent_segments', 'High Performer High Potential,High Performer Low Potential,Low Performer High Potential,Low Performer Low Potential', 'String', 'Talent', 'Talent segmentation', 0),
        ('default_review_cycle', 'Annual', 'String', 'Review', 'Default review cycle type', 0),
        ('hi_po_criteria_performance', '4', 'Integer', 'HiPo', 'Min performance for Hi-Po', 0),
        ('hi_po_criteria_potential', '3', 'Integer', 'HiPo', 'Min potential for Hi-Po', 0),
        ('succession_coverage_target', '2', 'Integer', 'Succession', 'Target successors per critical role', 0),
        ('idp_default_duration_months', '12', 'Integer', 'Development', 'Default IDP duration', 0),
        ('competency_scale_min', '1', 'Integer', 'Competency', 'Min competency level', 0),
        ('competency_scale_max', '5', 'Integer', 'Competency', 'Max competency level', 0),
        ('mentoring_max_assignments', '3', 'Integer', 'Mentoring', 'Max mentees per mentor', 0),
        ('approval_workflow_enabled', '1', 'Boolean', 'Workflow', 'Enable approval workflows', 0),
        ('export_max_rows', '10000', 'Integer', 'Export', 'Max rows per export', 0),
        ('audit_retention_days', '2555', 'Integer', 'Audit', 'Audit log retention', 0),
    ]
    
    for setting in settings:
        conn.execute("""
            INSERT OR IGNORE INTO tm_talent_settings 
            (setting_key, setting_value, setting_type, category, description, is_editable)
            VALUES (?, ?, ?, ?, ?, ?)
        """, setting)
    
    print("Seeded talent settings")


if __name__ == '__main__':
    success = seed_talent_data()
    exit(0 if success else 1)
