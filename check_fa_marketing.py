"""Check Persian Marketing terminology against EN."""
import sys
sys.path.insert(0, "C:/Users/sdads/WHDASH")
exec(open("C:/Users/sdads/WHDASH/translations.py", encoding="utf-8").read())

en = TRANSLATIONS['en']
fa = TRANSLATIONS['fa']

mkt_keys = [k for k in en.keys() if any(x in k for x in ['campaign', 'lead', 'funnel', 'marketing', 'advertisement', 'content', 'sales'])]

with open('C:/Users/sdads/WHDASH/fa_marketing_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"=== Persian Marketing keys ({len(mkt_keys)} total) ===\n\n")
    for k in sorted(mkt_keys):
        fa_val = fa.get(k, 'MISSING')
        en_val = en.get(k, 'MISSING')
        status = "OK" if fa_val != 'MISSING' and fa_val != k else "MISSING" if fa_val == 'MISSING' else "SAME_AS_KEY"
        out.write(f"  [{status}] {k}\n")
        if fa_val != en_val and fa_val != 'MISSING':
            out.write(f"      EN: {en_val}\n")
            out.write(f"      FA: {fa_val}\n")
    out.write("\nDone.\n")
print("Report written to fa_marketing_report.txt")