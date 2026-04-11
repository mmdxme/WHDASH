"""Seed HR recruitment data."""
import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def seed_recruitment_data():
    """Seed sample recruitment data."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    cursor = conn.cursor()

    # Check if we already have requisitions
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM hr_job_requisitions").fetchone()['cnt']
    if existing > 0:
        print(f"Already have {existing} requisitions, skipping seed.")
        conn.close()
        return

    # Get departments and positions
    departments = cursor.execute("SELECT id, name FROM hr_departments").fetchall()
    positions = cursor.execute("SELECT id, title FROM hr_positions").fetchall()
    users = cursor.execute("SELECT id, username FROM users").fetchall()

    if not departments:
        print("No departments found. Please create departments first.")
        conn.close()
        return

    # Sample requisitions
    requisitions = [
        {
            'title': 'Senior Software Engineer',
            'description': 'We are looking for an experienced software engineer to join our development team. You will be responsible for designing, developing, and maintaining software applications.',
            'requirements': '- 5+ years of experience\n- Proficiency in Python/Java\n- Experience with cloud platforms\n- Strong problem-solving skills',
            'salary_min': 80000,
            'salary_max': 120000,
            'vacancy_count': 2,
            'employment_type': 'Full-time',
            'status': 'Open'
        },
        {
            'title': 'Product Manager',
            'description': 'Join our product team to drive product strategy and roadmap. Work closely with engineering, design, and stakeholders.',
            'requirements': '- 3+ years of product management experience\n- Technical background preferred\n- Excellent communication skills\n- Data-driven decision making',
            'salary_min': 90000,
            'salary_max': 130000,
            'vacancy_count': 1,
            'employment_type': 'Full-time',
            'status': 'Open'
        },
        {
            'title': 'UX Designer',
            'description': 'Create intuitive and engaging user experiences for our products. Collaborate with product and engineering teams.',
            'requirements': '- 4+ years of UX design experience\n- Proficiency in Figma/Sketch\n- Portfolio required\n- User research experience',
            'salary_min': 70000,
            'salary_max': 100000,
            'vacancy_count': 1,
            'employment_type': 'Full-time',
            'status': 'In Review'
        },
        {
            'title': 'DevOps Engineer',
            'description': 'Build and maintain our CI/CD pipelines and infrastructure. Ensure high availability and performance.',
            'requirements': '- 3+ years DevOps experience\n- Kubernetes/Docker expertise\n- AWS/Azure experience\n- Infrastructure as Code',
            'salary_min': 85000,
            'salary_max': 115000,
            'vacancy_count': 1,
            'employment_type': 'Full-time',
            'status': 'Open'
        },
        {
            'title': 'Marketing Coordinator',
            'description': 'Support marketing initiatives and campaigns. Help grow our brand presence and customer engagement.',
            'requirements': '- 2+ years marketing experience\n- Social media expertise\n- Content creation skills\n- Analytics experience',
            'salary_min': 45000,
            'salary_max': 60000,
            'vacancy_count': 1,
            'employment_type': 'Part-time',
            'status': 'Pending Approval'
        },
        {
            'title': 'Data Analyst',
            'description': 'Analyze data to drive business decisions. Create reports and dashboards for various stakeholders.',
            'requirements': '- 3+ years data analysis experience\n- SQL expertise\n- Python/R skills\n- Visualization tools proficiency',
            'salary_min': 65000,
            'salary_max': 85000,
            'vacancy_count': 2,
            'employment_type': 'Full-time',
            'status': 'Open'
        },
        {
            'title': 'Customer Success Manager',
            'description': 'Build relationships with customers and ensure their success with our products. Drive adoption and retention.',
            'requirements': '- 3+ years CS experience\n- SaaS experience preferred\n- Strong interpersonal skills\n- Technical aptitude',
            'salary_min': 60000,
            'salary_max': 80000,
            'vacancy_count': 1,
            'employment_type': 'Full-time',
            'status': 'Approved'
        },
        {
            'title': 'Frontend Developer',
            'description': 'Build responsive and performant web applications. Work with React/Vue and modern web technologies.',
            'requirements': '- 3+ years frontend experience\n- React/Vue expertise\n- TypeScript knowledge\n- CSS/Styling skills',
            'salary_min': 75000,
            'salary_max': 105000,
            'vacancy_count': 3,
            'employment_type': 'Remote',
            'status': 'Open'
        }
    ]

    requisition_ids = []
    for req in requisitions:
        dept = random.choice(departments) if departments else None
        pos = random.choice(positions) if positions else None
        user = random.choice(users) if users else None

        cursor.execute("""
            INSERT INTO hr_job_requisitions
            (title, department_id, position_id, vacancy_count, employment_type,
             salary_min, salary_max, description, requirements, status, requested_by_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req['title'], dept['id'] if dept else None, pos['id'] if pos else None,
            req['vacancy_count'], req['employment_type'],
            req['salary_min'], req['salary_max'],
            req['description'], req['requirements'], req['status'],
            user['id'] if user else None
        ))
        requisition_ids.append(cursor.lastrowid)

    conn.commit()

    # Sample candidates
    first_names = ['Sarah', 'Michael', 'Emma', 'James', 'Sophia', 'William', 'Olivia', 'Benjamin',
                   'Isabella', 'Lucas', 'Mia', 'Henry', 'Charlotte', 'Alexander', 'Amelia', 'Daniel']
    last_names = ['Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez',
                  'Martinez', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Jackson', 'Martin', 'Lee']
    sources = ['Website', 'LinkedIn', 'Referral', 'Agency', 'Job Fair']
    stages = ['Applied', 'Screening', 'Interview', 'Technical', 'Offer', 'Hired', 'Rejected']
    statuses = ['Active', 'Active', 'Active', 'Inactive']

    candidates = [
        {'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah.johnson@email.com', 'phone': '+1-555-0101', 'position_applied': 'Senior Software Engineer', 'source': 'LinkedIn', 'stage': 'Technical', 'score': 4.5},
        {'first_name': 'Michael', 'last_name': 'Williams', 'email': 'michael.w@email.com', 'phone': '+1-555-0102', 'position_applied': 'Product Manager', 'source': 'Referral', 'stage': 'Interview', 'score': 4.0},
        {'first_name': 'Emma', 'last_name': 'Brown', 'email': 'emma.brown@email.com', 'phone': '+1-555-0103', 'position_applied': 'UX Designer', 'source': 'Website', 'stage': 'Offer', 'score': 4.8},
        {'first_name': 'James', 'last_name': 'Jones', 'email': 'james.jones@email.com', 'phone': '+1-555-0104', 'position_applied': 'DevOps Engineer', 'source': 'LinkedIn', 'stage': 'Screening', 'score': 3.5},
        {'first_name': 'Sophia', 'last_name': 'Garcia', 'email': 'sophia.g@email.com', 'phone': '+1-555-0105', 'position_applied': 'Data Analyst', 'source': 'Agency', 'stage': 'Interview', 'score': 4.2},
        {'first_name': 'William', 'last_name': 'Miller', 'email': 'will.miller@email.com', 'phone': '+1-555-0106', 'position_applied': 'Frontend Developer', 'source': 'Website', 'stage': 'Applied', 'score': None},
        {'first_name': 'Olivia', 'last_name': 'Davis', 'email': 'olivia.davis@email.com', 'phone': '+1-555-0107', 'position_applied': 'Senior Software Engineer', 'source': 'Referral', 'stage': 'Hired', 'score': 5.0},
        {'first_name': 'Benjamin', 'last_name': 'Rodriguez', 'email': 'ben.rodriguez@email.com', 'phone': '+1-555-0108', 'position_applied': 'Customer Success Manager', 'source': 'LinkedIn', 'stage': 'Interview', 'score': 3.8},
        {'first_name': 'Isabella', 'last_name': 'Martinez', 'email': 'isabella.m@email.com', 'phone': '+1-555-0109', 'position_applied': 'Marketing Coordinator', 'source': 'Job Fair', 'stage': 'Screening', 'score': 3.2},
        {'first_name': 'Lucas', 'last_name': 'Anderson', 'email': 'lucas.a@email.com', 'phone': '+1-555-0110', 'position_applied': 'Data Analyst', 'source': 'Website', 'stage': 'Rejected', 'score': 2.5},
        {'first_name': 'Mia', 'last_name': 'Taylor', 'email': 'mia.taylor@email.com', 'phone': '+1-555-0111', 'position_applied': 'UX Designer', 'source': 'Agency', 'stage': 'Technical', 'score': 4.3},
        {'first_name': 'Henry', 'last_name': 'Thomas', 'email': 'henry.thomas@email.com', 'phone': '+1-555-0112', 'position_applied': 'Frontend Developer', 'source': 'LinkedIn', 'stage': 'Interview', 'score': 4.0},
    ]

    for c in candidates:
        req_id = random.choice(requisition_ids) if requisition_ids else None
        user = random.choice(users) if users else None

        cursor.execute("""
            INSERT INTO hr_candidates
            (requisition_id, first_name, last_name, email, phone, position_applied,
             source, current_stage, interview_score, status, assigned_recruiter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)
        """, (
            req_id, c['first_name'], c['last_name'], c['email'], c['phone'],
            c['position_applied'], c['source'], c['stage'], c['score'],
            user['id'] if user else None
        ))

    conn.commit()
    print(f"Seeded {len(requisitions)} job requisitions and {len(candidates)} candidates.")

    conn.close()


if __name__ == '__main__':
    seed_recruitment_data()
