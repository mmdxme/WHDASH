"""Fix remaining 27 Persian keys."""
with open('C:/Users/sdads/WHDASH/translations.py', 'r', encoding='utf-8') as f:
    lines = f.read().split('\n')

# Remaining Persian translations
FA_REMAINING = {
    'flow_host': 'میزبان',
    'flow_invite': 'دعوت',
    'flow_media_hint': 'رسانه‌های به اشتراک گذاشته شده در گفتگوهای شما اینجا نمایش داده می‌شود',
    'flow_meetings': 'جلسات',
    'flow_member': 'عضو',
    'flow_no_reminders': 'یادآوری فعالی نیست',
    'flow_no_shared_media': 'رسانه به اشتراک گذاشته شده‌ای نیست',
    'flow_owner': 'صاحب',
    'flow_participants': 'شرکت‌کنندگان',
    'flow_private_channel': 'کانال خصوصی',
    'flow_private_group': 'گروه خصوصی',
    'flow_public_channel': 'کانال عمومی',
    'flow_public_group': 'گروه عمومی',
    'flow_share_screen': 'اشتراک‌گذاری صفحه',
    'flow_stop_sharing': 'توقف اشتراک‌گذاری',
    'flow_subtitle': 'ارتباطات سازمانی',
    'flow_try_different': 'کلمات یا فیلترهای دیگری امتحان کنید',
    'flow_type_message': 'پیام خود را بنویسید...',
    'flow_visibility': 'دید',
    'quick_issue': 'مشکل سریع',
    'quick_nav': 'ناوبری سریع',
    'quick_note': 'یادداشت سریع',
    'quick_notes': 'یادداشت‌های سریع',
    'quick_reminder': 'یادآوری سریع',
    'quick_task': 'وظیفه سریع',
    'quick_tools': 'ابزارهای سریع',
    'quick_tools_panel': 'پنل ابزارهای سریع',
}

fa_start = None
for i, line in enumerate(lines):
    if line.strip().startswith("'fa':"):
        fa_start = i
        break

changes = 0
for i in range(fa_start, min(fa_start + 1000, len(lines))):
    line = lines[i]
    stripped = line.strip()
    for key, persian_val in FA_REMAINING.items():
        if stripped.startswith(f"'{key}':"):
            indent = len(line) - len(line.lstrip())
            new_line = f"{' ' * indent}'{key}': '{persian_val}',"
            lines[i] = new_line
            changes += 1
            break
    if "'ar':" in lines[i] or "'ru':" in lines[i]:
        break

print(f"Fixed {changes} remaining Persian keys")

with open('C:/Users/sdads/WHDASH/translations.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))