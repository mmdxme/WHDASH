"""Check Arabic Workflow terminology."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

en = TRANSLATIONS['en']
ar = TRANSLATIONS['ar']

# Workflow keys
wf_keys = [k for k in en.keys() if any(x in k for x in ['workflow', 'task', 'escalat', 'delegat', 'approv', 'status', 'pending', 'overdue'])]
print(f"=== Arabic Workflow keys ({len(wf_keys)} total) ===")
with open('C:/Users/sdads/WHDASH/ar_workflow_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"=== Arabic Workflow keys ({len(wf_keys)} total) ===\n\n")
    for k in sorted(wf_keys):
        ar_val = ar.get(k, 'MISSING')
        en_val = en.get(k, 'MISSING')
        status = "OK" if ar_val != 'MISSING' and ar_val != k else "MISSING" if ar_val == 'MISSING' else "SAME_AS_KEY"
        out.write(f"  [{status}] {k}\n")
        if ar_val != en_val and ar_val != 'MISSING':
            out.write(f"      EN: {en_val}\n")
            out.write(f"      AR: {ar_val}\n")
    out.write("\nDone.\n")
print("Report written to ar_workflow_report.txt")