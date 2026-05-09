# HR Module - Sample Data Guide
## WHDASH Enterprise HR Platform

---

## 1. Overview

This document describes the sample data available for the HR module, including how to seed it, what entities are created, and the relationships between them.

---

## 2. Seed Functions Overview

### 2.1 Available Seed Functions

| Function | Location | Description |
|----------|----------|-------------|
| `seed_hr_data()` | `seed_all.py` | Core HR data - departments, positions, employees, leave types |
| `seed_hr_extended()` | `seed_all.py` | Extended data - loans, bonuses, deductions |
| `seed_hr_leave_requests` | `seed_dynamic.py` | Leave requests in various states |
| `seed_hr_overtime_requests` | `seed_dynamic.py` | Overtime requests |
| `seed_hr_training_programs` | `seed_dynamic.py` | Training programs and sessions |
| `seed_hr_performance_reviews` | `seed_dynamic.py` | Performance reviews |
| `seed_comprehensive_hr()` | `seed_comprehensive.py` | Full HR dataset |

---

## 3. Core Sample Data

### 3.1 Departments

**Count:** 8 departments

| ID | Name | Code | Parent | Head ID |
|----|------|------|--------|---------|
| 1 | Executive Management | EXEC | null | 1 |
| 2 | Human Resources | HR | 1 | 2 |
| 3 | Finance | FIN | 1 | 3 |
| 4 | Operations | OPS | 1 | 4 |
| 5 | Information Technology | IT | 1 | 5 |
| 6 | Sales & Marketing | SALES | 1 | 6 |
| 7 | Supply Chain | SCM | 1 | 7 |
| 8 | Quality & Compliance | QC | 1 | 8 |

### 3.2 Positions

**Count:** 15 positions

| ID | Title | Department | Grade | Salary Band |
|----|-------|------------|-------|-------------|
| 1 | Chief Executive Officer | Executive | C1 | 50000-80000 |
| 2 | HR Director | HR | D1 | 30000-45000 |
| 3 | Finance Director | Finance | D1 | 30000-45000 |
| 4 | Operations Director | Operations | D1 | 30000-45000 |
| 5 | IT Director | IT | D1 | 30000-45000 |
| 6 | Sales Director | Sales | D1 | 30000-50000 |
| 7 | HR Manager | HR | M1 | 15000-25000 |
| 8 | HR Officer | HR | M2 | 8000-15000 |
| 9 | Finance Manager | Finance | M1 | 15000-25000 |
| 10 | Accountant | Finance | M2 | 8000-15000 |
| 11 | IT Manager | IT | M1 | 15000-25000 |
| 12 | Software Engineer | IT | M2 | 10000-20000 |
| 13 | Sales Manager | Sales | M1 | 15000-30000 |
| 14 | Sales Executive | Sales | M2 | 6000-12000 |
| 15 | Admin Assistant | HR | S1 | 4000-8000 |

### 3.3 Employees

**Count:** 15 employees

| Code | First Name | Last Name | Department | Position | Status | Hire Date |
|------|------------|-----------|------------|----------|--------|-----------|
| EMP2024001 | Ahmed | Al-Rashid | Executive | CEO | Active | 2020-01-15 |
| EMP2024002 | Sarah | Hassan | HR | HR Director | Active | 2019-03-20 |
| EMP2024003 | Mohammad | Khan | Finance | Finance Director | Active | 2018-06-10 |
| EMP2024004 | Fatima | Ali | Operations | Operations Director | Active | 2019-08-01 |
| EMP2024005 | Omar | Patel | IT | IT Director | Active | 2020-02-15 |
| EMP2024006 | Layla | Ahmed | Sales | Sales Director | Active | 2019-11-01 |
| EMP2024007 | Hassan | Mahmoud | Supply Chain | Director | Active | 2020-05-01 |
| EMP2024008 | Fatima | Malik | Quality | Director | Active | 2021-01-10 |
| EMP2024009 | Ali | Hassan | HR | HR Manager | Active | 2021-03-15 |
| EMP2024010 | Rashid | Khan | HR | HR Officer | Active | 2022-06-01 |
| EMP2024011 | Zainab | Malik | Finance | Finance Manager | Active | 2021-09-01 |
| EMP2024012 | Youssef | Ali | IT | IT Manager | Active | 2022-01-15 |
| EMP2024013 | Noor | Hassan | Sales | Sales Manager | Active | 2022-04-01 |
| EMP2024014 | Karim | Mahmoud | IT | Software Engineer | Active | 2023-02-01 |
| EMP2024015 | Samira | Patel | HR | Admin Assistant | Probation | 2024-01-15 |

### 3.4 Shifts

**Count:** 5 shifts

| Code | Name | Start | End | Grace | Hours | Working Days |
|------|------|-------|-----|-------|-------|---------------|
| MORN | Morning Shift | 08:00 | 17:00 | 15 | 8.0 | 1,2,3,4,5 |
| EVE | Evening Shift | 14:00 | 23:00 | 15 | 8.0 | 1,2,3,4,5 |
| NIGHT | Night Shift | 22:00 | 07:00 | 0 | 8.0 | 1,2,3,4,5 |
| DAY-UAE | Day Shift (UAE) | 09:00 | 18:00 | 30 | 8.0 | 1,2,3,4,5 |
| HALF | Half Day | 08:00 | 12:00 | 0 | 4.0 | 1,2,3,4,5 |

### 3.5 Leave Types

**Count:** 7 leave types

| Code | Name | Default Days | Paid | Requires Approval | Carry Forward |
|------|------|--------------|------|-------------------|---------------|
| AL | Annual Leave | 21 | Yes | Yes | Yes (5 days) |
| SL | Sick Leave | 14 | Yes | Yes | No |
| EL | Emergency Leave | 5 | Yes | Yes | No |
| UL | Unpaid Leave | 0 | No | Yes | No |
| ML | Maternity Leave | 90 | Yes | Yes | No |
| PL | Paternity Leave | 5 | Yes | Yes | No |
| HL | Hajj Leave | 10 | Yes | Yes | No |

---

## 4. Extended Sample Data

### 4.1 Attendance Records

**Coverage:** Last 30 days for all active employees

Each attendance record includes:
- `check_in`: Actual check-in time
- `check_out`: Actual check-out time
- `work_hours`: Calculated hours worked
- `late_minutes`: Minutes late (if applicable)
- `status`: Present, Absent, Late, Early Leave

### 4.2 Leave Requests

**Count:** ~20 leave requests across various states

| Employee | Leave Type | Status | Days |
|----------|------------|--------|------|
| Ahmed Al-Rashid | Annual | Approved | 5 |
| Sarah Hassan | Annual | Approved | 10 |
| Mohammad Khan | Sick | Approved | 3 |
| Fatima Ali | Emergency | Pending | 2 |
| Omar Patel | Annual | Approved | 7 |
| Layla Ahmed | Maternity | Approved | 45 |
| Hassan Mahmoud | Annual | Approved | 5 |
| Ali Hassan | Sick | Pending | 2 |
| Rashid Khan | Emergency | Rejected | 1 |
| Zainab Malik | Annual | Approved | 8 |

### 4.3 Loans

**Count:** 4 active loans

| Employee | Principal | Tenure | Monthly Installment | Status |
|----------|----------|--------|---------------------|--------|
| Mohammad Khan | 50,000 | 24 | 2,500 | Active |
| Fatima Ali | 30,000 | 12 | 2,750 | Active |
| Omar Patel | 75,000 | 36 | 2,500 | Active |
| Hassan Mahmoud | 20,000 | 6 | 3,500 | Closed |

### 4.4 Bonus Records

**Count:** Multiple bonuses per employee

Bonus types:
- `Performance Bonus` - Annual performance-based bonus
- `Festival Bonus` - Eid/Holiday bonus
- `Special Bonus` - Recognition bonus
- `Commission` - Sales commission

### 4.5 Deduction Records

**Count:** Multiple deductions per employee

Deduction types:
- `Absence Deduction` - Unpaid leave deductions
- `Late Deduction` - Late arrival penalties
- `Loan Deduction` - Monthly loan installments
- `Advance Deduction` - Salary advance repayments
- `Penalty` - Disciplinary deductions

### 4.6 Overtime Requests

**Count:** ~15 overtime requests

| Employee | Date | Hours | Type | Status |
|----------|------|-------|------|--------|
| Ali Hassan | 2024-01-15 | 3 | Regular | Approved |
| Rashid Khan | 2024-01-18 | 5 | Weekend | Approved |
| Zainab Malik | 2024-01-20 | 2 | Regular | Pending |
| Youssef Ali | 2024-01-22 | 4 | Holiday | Approved |

---

## 5. Training Sample Data

### 5.1 Training Programs

**Count:** 8 programs

| Title | Category | Type | Duration | Mandatory |
|-------|----------|------|----------|-----------|
| Corporate Ethics & Compliance | HR | Compliance | 4 hours | Yes |
| Workplace Safety | Operations | Safety | 8 hours | Yes |
| IT Security Fundamentals | IT | Technical | 6 hours | Yes |
| Customer Service Excellence | Sales | Soft Skills | 8 hours | No |
| Advanced Excel Training | Finance | Technical | 16 hours | No |
| Leadership Development | Management | Leadership | 24 hours | No |
| Harassment Prevention | HR | Compliance | 2 hours | Yes |
| First Aid & CPR | Operations | Safety | 8 hours | Yes |

### 5.2 Training Sessions

**Count:** 12 sessions (past and upcoming)

Sessions include:
- Scheduled sessions with trainer info
- Location or online link
- Start/end dates and times
- Enrollment count vs max participants
- Status: Scheduled, In Progress, Completed, Cancelled

### 5.3 Training Enrollments

**Count:** 40+ enrollments

Each enrollment tracks:
- Employee enrollment date
- Attendance status (Attended, Absent, Excused)
- Completion date
- Score and grade (if applicable)
- Certificate number (if completed)

---

## 6. Recruitment Sample Data

### 6.1 Job Requisitions

**Count:** 6 requisitions

| Title | Department | Vacancies | Status |
|-------|------------|-----------|--------|
| Senior Software Engineer | IT | 2 | Open |
| HR Officer | HR | 1 | In Review |
| Finance Manager | Finance | 1 | Pending Approval |
| Sales Executive | Sales | 3 | Open |
| Quality Inspector | QC | 1 | Closed |
| Logistics Coordinator | Supply Chain | 2 | Open |

### 6.2 Candidates

**Count:** 15 candidates

| Name | Requisition | Stage | Status |
|------|-------------|-------|--------|
| John Smith | Senior Software Engineer | Interview | Active |
| Maria Garcia | Senior Software Engineer | Screening | Active |
| Chen Wei | HR Officer | Offer | Active |
| Ahmed Youssef | Sales Executive | Applied | Active |
| Priya Sharma | Finance Manager | Interview | Active |
| David Brown | Quality Inspector | Hired | Active |
| Sarah Wilson | Logistics Coordinator | Screening | Active |
| Michael Chen | Senior Software Engineer | Applied | Active |
| Fatima Zahra | HR Officer | Interview | Active |
| Robert Taylor | Sales Executive | Rejected | Inactive |

---

## 7. Performance Review Sample Data

### 7.1 Review Cycles

| Cycle | Year | Status |
|-------|------|--------|
| Annual Performance Review | 2024 | Active |
| Mid-Year Review | 2024 | Draft |
| Q1 Check-in | 2024 | Completed |

### 7.2 Performance Reviews

**Count:** 12 reviews

Each review includes:
- Employee and reviewer
- Overall score (1-5 scale)
- KPI scores
- Strengths and areas for improvement
- Comments
- Status: Draft, Submitted, Acknowledged

---

## 8. Succession Planning Sample Data

### 8.1 Successors

**Count:** 6 succession plans

| Current Role | Successor | Readiness | Status |
|--------------|-----------|-----------|--------|
| CEO | COO | Ready in 2 years | Active |
| Finance Director | Finance Manager | Ready in 1 year | Active |
| IT Director | IT Manager | Ready Now | Active |
| Sales Director | Sales Manager | Ready in 1 year | Active |
| HR Director | HR Manager | Not Ready | Active |
| Operations Director | Operations Manager | Ready in 2 years | Active |

---

## 9. Seeding Instructions

### 9.1 Running Seeds

From Python:

```python
from seed_all import seed_all
seed_all()  # Seeds all modules including HR

# Or seed specifically HR:
from seed_all import seed_hr_data, seed_hr_extended
seed_hr_data()
seed_hr_extended()
```

From command line:

```bash
python -c "from seed_all import seed_all; seed_all()"
```

### 9.2 Resetting HR Data

```python
from hr_models import get_db
db = get_db()

# Clear HR tables (in correct order due to FK)
tables = [
    'hr_loan_installments', 'hr_loans', 'hr_bonus_records', 
    'hr_deduction_records', 'hr_overtime_requests', 
    'hr_training_enrollments', 'hr_training_sessions', 
    'hr_training_programs', 'hr_performance_reviews', 
    'hr_successors', 'hr_announcements', 'hr_candidates',
    'hr_job_requisitions', 'hr_approvals', 'hr_leave_requests',
    'hr_leave_balances', 'hr_attendance_records', 
    'hr_employee_documents', 'hr_employee_salary', 
    'hr_employee_employment', 'hr_employees',
    'hr_positions', 'hr_departments', 'hr_shifts', 
    'hr_leave_types', 'hr_payroll_periods', 'hr_payroll_records',
    'hr_payroll_components', 'hr_settings', 'hr_audit_logs'
]

for table in tables:
    db.execute(f'DELETE FROM {table}')
db.commit()
```

---

## 10. Sample Data for Testing

### 10.1 Test Scenarios

| Scenario | Data Needed |
|----------|-------------|
| Leave approval workflow | Pending leave requests |
| Overtime calculation | OT requests with various rates |
| Document expiry alerts | Documents expiring in 30 days |
| Recruitment pipeline | Candidates in all stages |
| Performance review cycle | Reviews in various states |
| Payroll processing | Employees with various earnings/deductions |
| Team conflict detection | Multiple leave requests for same dates |
| Missing punch review | Attendance records with missing check-out |

### 10.2 Generating Test Data

```python
from seed_dynamic import seed_hr_leave_requests, seed_hr_overtime_requests

# Generate leave requests in various states
seed_hr_leave_requests(count=20)

# Generate overtime requests
seed_hr_overtime_requests(count=15)
```