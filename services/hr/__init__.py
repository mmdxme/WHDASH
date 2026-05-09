"""
HR Service Layer
================
Business logic extracted from the monolithic hr_routes.py (5023 lines, 203 KB).

Sub-services:
- employee_service: Employee CRUD, employment records
- attendance_service: Attendance tracking, reports
- leave_service: Leave management, balances
- payroll_service: Payroll processing, salary calculations
- recruitment_service: Job requisitions, applicants, hiring
- training_service: Training programs, enrollment
- reports_service: HR analytics and report generation
"""

from services.hr.employee_service import HREmployeeService
from services.hr.attendance_service import HRAttendanceService
from services.hr.leave_service import HRLeaveService
from services.hr.recruitment_service import HRRecruitmentService
from services.hr.training_service import HRTrainingService
from services.hr.reports_service import HRReportsService

__all__ = [
    'HREmployeeService',
    'HRAttendanceService',
    'HRLeaveService',
    'HRRecruitmentService',
    'HRTrainingService',
    'HRReportsService',
]
