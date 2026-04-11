# Script to create a fixed quality_models.py
import re

with open('quality_models_backup.py', 'r') as f:
    content = f.read()

# The issue is with the f""" strings that have embedded {where_sql}
# Replace problematic f-strings with standard string formatting

# Fix get_supplier_quality_report - it uses query = """ with % formatting already
# But the issue is it has an unclosed f-string somewhere earlier

# Let's find and fix the specific problematic patterns
# Replace f""" ... WHERE {where_sql} ... """ with """ ... WHERE %s ... """ % where_sql

# Pattern 1: f""" followed by WHERE {where_sql}
# This affects multiple functions

# Let's do a targeted fix for each function with the issue

# Fix get_ncr_summary_report (lines 2557-2602)
old_ncr_summary = '''        by_status = db.execute(f"""
            SELECT status, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql}
            GROUP BY status
        """, params).fetchall()

        # Summary by severity
        by_severity = db.execute(f"""
            SELECT severity, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql}
            GROUP BY severity
        """, params).fetchall()

        # Summary by category
        by_category = db.execute(f"""
            SELECT qnc.category_id, COUNT(*) as count
            FROM quality_non_conformances qnc
            LEFT JOIN quality_defect_categories qdc ON qnc.category_id = qdc.id
            WHERE {where_sql}
            GROUP BY qnc.category_id
            ORDER BY count DESC
        """, params).fetchall()

        # Summary by supplier
        by_supplier = db.execute(f"""
            SELECT supplier_name, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql} AND supplier_name IS NOT NULL
            GROUP BY supplier_name
            ORDER BY count DESC
            LIMIT 20
        """, params).fetchall()

        # Monthly trend
        monthly_trend = db.execute(f"""
            SELECT
                strftime('%Y-%m', detected_date) as month,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed
            FROM quality_non_conformances
            WHERE {where_sql} AND detected_date IS NOT NULL
            GROUP BY strftime('%Y-%m', detected_date)
            ORDER BY month DESC
            LIMIT 12
        """, params).fetchall()'''

new_ncr_summary = '''        by_status = db.execute("""
            SELECT status, COUNT(*) as count
            FROM quality_non_conformances
            WHERE %s
            GROUP BY status
        """ % where_sql, params).fetchall()

        # Summary by severity
        by_severity = db.execute("""
            SELECT severity, COUNT(*) as count
            FROM quality_non_conformances
            WHERE %s
            GROUP BY severity
        """ % where_sql, params).fetchall()

        # Summary by category
        by_category = db.execute("""
            SELECT qnc.category_id, COUNT(*) as count
            FROM quality_non_conformances qnc
            LEFT JOIN quality_defect_categories qdc ON qnc.category_id = qdc.id
            WHERE %s
            GROUP BY qnc.category_id
            ORDER BY count DESC
        """ % where_sql, params).fetchall()

        # Summary by supplier
        by_supplier = db.execute("""
            SELECT supplier_name, COUNT(*) as count
            FROM quality_non_conformances
            WHERE %s AND supplier_name IS NOT NULL
            GROUP BY supplier_name
            ORDER BY count DESC
            LIMIT 20
        """ % where_sql, params).fetchall()

        # Monthly trend
        monthly_trend = db.execute("""
            SELECT
                strftime('%%Y-%%m', detected_date) as month,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed
            FROM quality_non_conformances
            WHERE %s AND detected_date IS NOT NULL
            GROUP BY strftime('%%Y-%%m', detected_date)
            ORDER BY month DESC
            LIMIT 12
        """ % where_sql, params).fetchall()'''

content = content.replace(old_ncr_summary, new_ncr_summary)

# Fix get_capa_summary_report (lines 2635-2675)
old_capa_summary = '''        by_status = db.execute(f"""
            SELECT status, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql}
            GROUP BY status
        """, params).fetchall()

        # Summary by type
        by_type = db.execute(f"""
            SELECT capa_type, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql}
            GROUP BY capa_type
        """, params).fetchall()

        # Summary by category
        by_category = db.execute(f"""
            SELECT qcc.name, COUNT(*) as count
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            WHERE {where_sql}
            GROUP BY qcc.name
            ORDER BY count DESC
        """, params).fetchall()

        # Effectiveness summary
        effectiveness_summary = db.execute(f"""
            SELECT
                effectiveness_result, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql} AND effectiveness_result IS NOT NULL
            GROUP BY effectiveness_result
        """, params).fetchall()

        # Average closure time
        avg_closure = db.execute(f"""
            SELECT
                AVG(julianday(actual_completion_date) - julianday(created_at)) as avg_days
            FROM quality_capa_records
            WHERE {where_sql} AND status = 'CLOSED' AND actual_completion_date IS NOT NULL
        """, params).fetchone()'''

new_capa_summary = '''        by_status = db.execute("""
            SELECT status, COUNT(*) as count
            FROM quality_capa_records
            WHERE %s
            GROUP BY status
        """ % where_sql, params).fetchall()

        # Summary by type
        by_type = db.execute("""
            SELECT capa_type, COUNT(*) as count
            FROM quality_capa_records
            WHERE %s
            GROUP BY capa_type
        """ % where_sql, params).fetchall()

        # Summary by category
        by_category = db.execute("""
            SELECT qcc.name, COUNT(*) as count
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            WHERE %s
            GROUP BY qcc.name
            ORDER BY count DESC
        """ % where_sql, params).fetchall()

        # Effectiveness summary
        effectiveness_summary = db.execute("""
            SELECT
                effectiveness_result, COUNT(*) as count
            FROM quality_capa_records
            WHERE %s AND effectiveness_result IS NOT NULL
            GROUP BY effectiveness_result
        """ % where_sql, params).fetchall()

        # Average closure time
        avg_closure = db.execute("""
            SELECT
                AVG(julianday(actual_completion_date) - julianday(created_at)) as avg_days
            FROM quality_capa_records
            WHERE %s AND status = 'CLOSED' AND actual_completion_date IS NOT NULL
        """ % where_sql, params).fetchone()'''

content = content.replace(old_capa_summary, new_capa_summary)

# Fix get_supplier_quality_report (lines 2704-2718) - use % formatting properly
old_supplier = '''        query = """
            SELECT
                s.id as supplier_id,
                s.name as supplier_name,
                COUNT(qnc.id) as ncr_count,
                SUM(CASE WHEN qnc.status = 'CLOSED' THEN 1 ELSE 0 END) as closed_count,
                SUM(CASE WHEN qnc.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN qnc.severity = 'MAJOR' THEN 1 ELSE 0 END) as major_count,
                SUM(qnc.financial_impact) as total_cost
            FROM suppliers s
            LEFT JOIN quality_non_conformances qnc ON s.id = qnc.supplier_id AND (%s)
            WHERE s.id IN (SELECT DISTINCT supplier_id FROM quality_non_conformances WHERE supplier_id IS NOT NULL)
            GROUP BY s.id, s.name
            ORDER BY ncr_count DESC
        """ % where_sql

        ncr_by_supplier = db.execute(query, params).fetchall()'''

new_supplier = '''        query = """
            SELECT
                s.id as supplier_id,
                s.name as supplier_name,
                COUNT(qnc.id) as ncr_count,
                SUM(CASE WHEN qnc.status = 'CLOSED' THEN 1 ELSE 0 END) as closed_count,
                SUM(CASE WHEN qnc.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN qnc.severity = 'MAJOR' THEN 1 ELSE 0 END) as major_count,
                SUM(qnc.financial_impact) as total_cost
            FROM suppliers s
            LEFT JOIN quality_non_conformances qnc ON s.id = qnc.supplier_id AND (%s)
            WHERE s.id IN (SELECT DISTINCT supplier_id FROM quality_non_conformances WHERE supplier_id IS NOT NULL)
            GROUP BY s.id, s.name
            ORDER BY ncr_count DESC
        """ % where_sql

        ncr_by_supplier = db.execute(query, params).fetchall()'''

content = content.replace(old_supplier, new_supplier)

# Now test parse
import ast
try:
    ast.parse(content)
    print('Parse: SUCCESS')

    # Save the fixed file
    with open('quality_models.py', 'w') as f:
        f.write(content)
    print('Saved quality_models.py')
except SyntaxError as e:
    print(f'Parse: FAIL - {e}')