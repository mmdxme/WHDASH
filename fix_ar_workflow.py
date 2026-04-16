"""Fix Arabic SAME_AS_KEY entries - direct line manipulation."""
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Arabic translations for the SAME_AS_KEY entries
fixes = {
    'create_task': 'إنشاء مهمة',
    'flow_online_status': 'الحالة عبر الإنترنت',
    'flow_status_message': 'رسالة الحالة',
    'quick_task': 'مهمة سريعة',
    'show_tasks': 'عرض المهام',
    'task_assign_self': 'تعيين لنفسي',
    'task_assign_to': 'تعيين إلى',
    'task_created': 'تم إنشاء المهمة بنجاح',
    'task_description': 'الوصف',
    'task_due_date': 'تاريخ الاستحقاق',
    'task_priority': 'الأولوية',
    'task_title': 'عنوان المهمة',
    'tools_tasks': 'المهام',
}

# Find AR section start/end
ar_start = None
ar_end = None
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("'ar':"):
        ar_start = i
    if ar_start is not None and ar_end is None:
        if stripped == '},' and "'" not in stripped:
            # Check if next non-empty line starts a new lang
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].strip().startswith("'"):
                    next_key = lines[j].strip().split(':')[0].strip("'")
                    if next_key in ['ru', 'zh', 'es', 'hi', 'de', 'en', 'fa']:
                        ar_end = i
                        break

if ar_end is None:
    ar_end = ar_start + 900  # fallback

print(f"AR section: lines {ar_start+1} to {ar_end+1}")

# Find and fix the keys
changes = []
for i in range(ar_start, ar_end+1):
    line = lines[i]
    stripped = line.strip()
    for key, arabic_val in fixes.items():
        if stripped.startswith(f"'{key}':"):
            indent = len(line) - len(line.lstrip())
            new_line = f"{' ' * indent}'{key}': '{arabic_val}',"
            lines[i] = new_line
            changes.append(f"Line {i+1}: {key}")

print(f"Fixed {len(changes)} keys")
for c in changes:
    print(f"  {c}")

with open('C:/Users/sdads/WHDASH/translations.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# Verify
exec(compile(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read(), 'translations.py', 'exec'))
ar = TRANSLATIONS['ar']
for key in fixes:
    print(f"  {key}: {ar.get(key, 'MISSING')}")