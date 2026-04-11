import re
import urllib.request
import urllib.parse
import http.cookiejar

# Patterns found from testing
patterns_to_fix = [
    # (wrong, correct)
    ('maintenance_equipment', 'maintenance.equipment_list'),
    ('maintenance_facilities', 'maintenance.facilities_list'),
    ('maintenance_facility_requests', 'maintenance.facility_requests_list'),
    ('maintenance_pm_plans', 'maintenance.pm_plans'),
    ('maintenance_pm_schedules', 'maintenance.pm_schedules'),
    ('maintenance_requests', 'maintenance.corrective_requests'),
    ('maintenance_work_orders', 'maintenance.work_orders'),
    ('maintenance_parts_usage', 'maintenance.parts_usage'),
    ('maintenance_labor_logs', 'maintenance.labor_logs'),
    ('maintenance_downtime', 'maintenance.downtime_list'),
    ('maintenance_inspections', 'maintenance.inspections_list'),
    ('maintenance_checklists', 'maintenance.checklist_templates'),
    ('maintenance_technicians', 'maintenance.technicians_list'),
    ('maintenance_reports', 'maintenance.reports'),
    ('maintenance_settings', 'maintenance.settings'),
]

# Read and fix all_menus.html
with open('templates/all_menus.html', 'r') as f:
    content = f.read()

for wrong, correct in patterns_to_fix:
    old_pattern = f"url_for('{wrong}')"
    new_pattern = f"url_for('{correct}')"
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f'Fixed {wrong} -> {correct} in all_menus.html')

    old_pattern2 = f"request.endpoint == '{wrong}'"
    new_pattern2 = f"request.endpoint == '{correct}'"
    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern2)
        print(f'Fixed endpoint check {wrong} -> {correct} in all_menus.html')

with open('templates/all_menus.html', 'w') as f:
    f.write(content)

# Read and fix menu_macros.html
with open('templates/menu_macros.html', 'r') as f:
    content = f.read()

for wrong, correct in patterns_to_fix:
    old_pattern = f"url_for('{wrong}')"
    new_pattern = f"url_for('{correct}')"
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f'Fixed {wrong} -> {correct} in menu_macros.html')

    old_pattern2 = f"request.endpoint == '{wrong}'"
    new_pattern2 = f"request.endpoint == '{correct}'"
    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern2)
        print(f'Fixed endpoint check {wrong} -> {correct} in menu_macros.html')

with open('templates/menu_macros.html', 'w') as f:
    f.write(content)

print('Done!')