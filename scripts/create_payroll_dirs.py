import os
base = r"c:\Users\sdads\WHDASH"
dirs = [
    "templates/payroll/dashboard",
    "templates/payroll/setup/components",
    "templates/payroll/setup/groups",
    "templates/payroll/setup/profiles",
    "templates/payroll/setup/calendar",
    "templates/payroll/periods",
    "templates/payroll/processing",
    "templates/payroll/review",
    "templates/payroll/payslips",
    "templates/payroll/loans",
    "templates/payroll/advances",
    "templates/payroll/retro",
    "templates/payroll/arrears",
    "templates/payroll/compliance",
    "templates/payroll/finance",
    "templates/payroll/hr_integration",
    "templates/payroll/reports",
    "templates/payroll/approvals",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)
    print(f"Created: {d}")
print("All directories created!")
