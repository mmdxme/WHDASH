"""
SPC / Statistical Process Control Routes
=========================================
Flask routes for SPC functionality.

Provides endpoints for:
- Control Charts (X-bar, R, S, C, P, NP, U, I-MR)
- Process Capability Analysis (Cp, Cpk, Pp, Ppk)
- Sampling Plans (AQL, ANSI/ASQ Z1.4)
- Anomaly Detection and Alerts
- Equipment/Calibration Management
- Gage R&R Studies
- SPC Dashboard and Analytics
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from functools import wraps
import sqlite3
import json
from datetime import datetime, timedelta
from io import BytesIO

from database import get_db, get_db_context
from permissions import user_has_permission
from spc_models import (
    initialize_spc_tables,
    SPCCalculator,
    CapabilityCalculator,
    SamplingPlanCalculator,
    add_spc_measurement,
    create_spc_alert,
    create_capability_study,
    get_spc_metrics_summary,
    get_control_chart_data,
    get_open_spc_alerts,
    register_equipment,
    record_calibration,
    perform_gage_rr_study
)

# Create blueprint
spc_bp = Blueprint('spc', __name__, url_prefix='/spc')


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_spc_routes(app):
    """Register SPC routes with the Flask app."""
    initialize_spc_tables()
    app.register_blueprint(spc_bp)


# =============================================================================
# SPC DASHBOARD
# =============================================================================

@spc_bp.route('/')
@spc_bp.route('/dashboard')
def dashboard():
    """SPC / Quality Analytics Dashboard."""
    page_title = "SPC / Quality Analytics"

    # Get metrics summary
    metrics = get_spc_metrics_summary()

    # Get open alerts
    alerts = get_open_spc_alerts('OPEN')

    # Get recent control chart data
    from database import get_db
    conn = get_db()
    cursor = conn.cursor()

    # Get chart types with recent data
    cursor.execute("""
        SELECT DISTINCT c.id, c.chart_name, c.chart_code, c.chart_type,
               COUNT(m.id) as measurement_count
        FROM spc_control_charts c
        LEFT JOIN spc_measurement_data m ON c.id = m.chart_id
        GROUP BY c.id
        ORDER BY c.chart_name
    """)
    charts = cursor.fetchall()

    # Get capability studies
    cursor.execute("""
        SELECT study_number, study_name, cp, cpk, pp, ppk, sigma_level, assessment, study_date
        FROM spc_capability_studies
        ORDER BY study_date DESC
        LIMIT 10
    """)
    capability_studies = cursor.fetchall()

    conn.close()

    return render_template('spc/dashboard.html',
                         page_title=page_title,
                         metrics=metrics,
                         alerts=alerts,
                         charts=list(charts),
                         capability_studies=list(capability_studies))


@spc_bp.route('/charts')
def charts_list():
    """List all SPC control charts."""
    page_title = "Control Charts"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.*,
               COUNT(m.id) as measurement_count,
               MAX(m.measurement_date) as last_measurement
        FROM spc_control_charts c
        LEFT JOIN spc_measurement_data m ON c.id = m.chart_id
        GROUP BY c.id
        ORDER BY c.chart_name
    """)
    charts = cursor.fetchall()

    conn.close()

    return render_template('spc/charts/list.html',
                         page_title=page_title,
                         charts=list(charts))


@spc_bp.route('/charts/<int:chart_id>')
def chart_view(chart_id):
    """View specific control chart with data."""
    page_title = "Control Chart Details"

    conn = get_db()
    cursor = conn.cursor()

    # Get chart info
    cursor.execute("SELECT * FROM spc_control_charts WHERE id = ?", (chart_id,))
    chart = cursor.fetchone()

    if not chart:
        conn.close()
        flash('Control chart not found', 'danger')
        return redirect(url_for('spc.charts_list'))

    # Get spec limits
    cursor.execute("""
        SELECT * FROM spc_specification_limits
        WHERE chart_id = ? AND is_active = 1
    """, (chart_id,))
    spec_limits = cursor.fetchone()

    # Get measurement data
    limit = int(request.args.get('limit', 50))
    chart_data = get_control_chart_data(chart_id, limit=limit)

    # Get control limits if enough data
    if len(chart_data) >= 5:
        values = [d['average'] for d in chart_data]
        if chart['chart_type'] == 'I_MR':
            limits = SPCCalculator.calculate_imr_control_limits(values)
        elif chart['chart_type'] == 'XBAR_R':
            # Need subgroup data for X-bar R chart
            limits = None
        else:
            limits = None
    else:
        limits = None

    # Get alerts for this chart
    cursor.execute("""
        SELECT * FROM spc_anomaly_alerts
        WHERE chart_id = ? AND status = 'OPEN'
        ORDER BY detected_at DESC
        LIMIT 10
    """, (chart_id,))
    alerts = cursor.fetchall()

    conn.close()

    return render_template('spc/charts/view.html',
                         page_title=page_title,
                         chart=dict(chart),
                         spec_limits=dict(spec_limits) if spec_limits else None,
                         chart_data=chart_data,
                         limits=limits,
                         alerts=list(alerts))


@spc_bp.route('/charts/create', methods=['GET', 'POST'])
def chart_create():
    """Create a new SPC control chart."""
    page_title = "Create Control Chart"

    if request.method == 'POST':
        chart_code = request.form.get('chart_code')
        chart_name = request.form.get('chart_name')
        chart_type = request.form.get('chart_type')
        description = request.form.get('description')

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO spc_control_charts (chart_code, chart_name, chart_type, description)
                VALUES (?, ?, ?, ?)
            """, (chart_code, chart_name, chart_type, description))

            chart_id = cursor.lastrowid

            # Add specification limits if provided
            usl = request.form.get('usl')
            lsl = request.form.get('lsl')
            target = request.form.get('target')
            ucl = request.form.get('ucl')
            lcl = request.form.get('lcl')

            if usl or lsl or target or ucl or lcl:
                cursor.execute("""
                    INSERT INTO spc_specification_limits
                    (chart_id, characteristic_name, usl, lsl, target, ucl, lcl)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (chart_id, chart_name, usl, lsl, target, ucl, lcl))

            conn.commit()
            flash('Control chart created successfully', 'success')
            return redirect(url_for('spc.chart_view', chart_id=chart_id))

        except sqlite3.IntegrityError:
            flash('Chart code already exists', 'danger')
        finally:
            conn.close()

    return render_template('spc/charts/create.html', page_title=page_title)


@spc_bp.route('/charts/<int:chart_id>/measurement', methods=['POST'])
def add_measurement(chart_id):
    """Add measurement data to a control chart."""
    try:
        data = request.get_json()

        measurement_group = data.get('measurement_group', f"Group-{datetime.now().strftime('%Y%m%d%H%M')}")
        sample_values = [float(v) for v in data.get('sample_values', [])]
        measurement_date = data.get('measurement_date', datetime.now().strftime('%Y-%m-%d'))
        notes = data.get('notes')

        if len(sample_values) == 0:
            return jsonify({'success': False, 'error': 'No measurement values provided'}), 400

        # Get chart code
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT chart_code FROM spc_control_charts WHERE id = ?", (chart_id,))
        row = cursor.fetchone()
        chart_code = row['chart_code'] if row else 'UNKNOWN'
        conn.close()

        measurement_id = add_spc_measurement(
            chart_id=chart_id,
            chart_code=chart_code,
            measurement_group=measurement_group,
            sample_values=sample_values,
            measurement_date=measurement_date,
            notes=notes
        )

        # Calculate current stats
        mean = sum(sample_values) / len(sample_values)

        return jsonify({
            'success': True,
            'measurement_id': measurement_id,
            'mean': mean,
            'sample_size': len(sample_values)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@spc_bp.route('/charts/<int:chart_id>/import', methods=['GET', 'POST'])
def import_measurements(chart_id):
    """Import measurements from CSV file."""
    page_title = "Import Measurements"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_control_charts WHERE id = ?", (chart_id,))
    chart = cursor.fetchone()
    conn.close()

    if not chart:
        flash('Control chart not found', 'danger')
        return redirect(url_for('spc.charts_list'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return render_template('spc/charts/import.html', page_title=page_title, chart=dict(chart), error='No file provided')

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return render_template('spc/charts/import.html', page_title=page_title, chart=dict(chart), error='No file selected')

        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'danger')
            return render_template('spc/charts/import.html', page_title=page_title, chart=dict(chart), error='Invalid file type')

        try:
            import csv
            from io import TextIOWrapper

            csv_content = TextIOWrapper(file.stream, encoding='utf-8-sig')
            reader = csv.DictReader(csv_content)

            imported = 0
            errors = []
            row_num = 1

            for row in reader:
                row_num += 1
                try:
                    measurement_group = row.get('group', row.get('measurement_group', f"Import-{datetime.now().strftime('%Y%m%d%H%M')}"))
                    values_str = row.get('values', row.get('sample_values', row.get('measurement')))

                    if not values_str:
                        errors.append(f"Row {row_num}: No values found")
                        continue

                    sample_values = [float(v.strip()) for v in values_str.split(',') if v.strip()]

                    if len(sample_values) == 0:
                        errors.append(f"Row {row_num}: Empty values")
                        continue

                    measurement_date = row.get('date', row.get('measurement_date', datetime.now().strftime('%Y-%m-%d')))
                    notes = row.get('notes', '')

                    add_spc_measurement(
                        chart_id=chart_id,
                        chart_code=chart['chart_code'],
                        measurement_group=measurement_group,
                        sample_values=sample_values,
                        measurement_date=measurement_date,
                        notes=notes
                    )
                    imported += 1

                except ValueError as ve:
                    errors.append(f"Row {row_num}: Invalid number format - {str(ve)}")
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

            flash(f'Successfully imported {imported} measurements', 'success' if imported > 0 else 'warning')
            if errors:
                flash(f'{len(errors)} rows had errors', 'warning')

            return redirect(url_for('spc.chart_view', chart_id=chart_id))

        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')

    return render_template('spc/charts/import.html', page_title=page_title, chart=dict(chart), error=None)


@spc_bp.route('/charts/<int:chart_id>/spec-limits', methods=['POST'])
def update_spec_limits(chart_id):
    """Update specification and control limits for a chart."""
    try:
        data = request.get_json()

        conn = get_db()
        cursor = conn.cursor()

        # Deactivate existing limits
        cursor.execute("""
            UPDATE spc_specification_limits SET is_active = 0, updated_at = datetime('now')
            WHERE chart_id = ?
        """, (chart_id,))

        # Insert new limits
        cursor.execute("""
            INSERT INTO spc_specification_limits
            (chart_id, characteristic_name, usl, lsl, target, ucl, lcl, ucl_2, lcl_2, ucl_3, lcl_3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chart_id,
            data.get('characteristic_name', ''),
            data.get('usl'),
            data.get('lsl'),
            data.get('target'),
            data.get('ucl'),
            data.get('lcl'),
            data.get('ucl_2'),
            data.get('lcl_2'),
            data.get('ucl_3'),
            data.get('lcl_3')
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# PROCESS CAPABILITY
# =============================================================================

@spc_bp.route('/capability')
def capability_list():
    """List process capability studies."""
    page_title = "Process Capability Studies"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, l.characteristic_name, l.usl, l.lsl, l.target
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        ORDER BY s.study_date DESC
        LIMIT 100
    """)
    studies = cursor.fetchall()

    conn.close()

    return render_template('spc/capability/list.html',
                         page_title=page_title,
                         studies=list(studies))


@spc_bp.route('/capability/create', methods=['GET', 'POST'])
def capability_create():
    """Create a new capability study."""
    page_title = "Create Capability Study"

    if request.method == 'POST':
        study_name = request.form.get('study_name')
        process_name = request.form.get('process_name')
        characteristic_id = request.form.get('characteristic_id')
        sample_data_str = request.form.get('sample_data')
        usl = float(request.form.get('usl', 0))
        lsl = float(request.form.get('lsl', 0))
        target = float(request.form.get('target', 0)) if request.form.get('target') else None
        study_date = request.form.get('study_date', datetime.now().strftime('%Y-%m-%d'))
        study_type = request.form.get('study_type', 'INITIAL')
        notes = request.form.get('notes')

        try:
            # Parse sample data
            sample_data = [float(x.strip()) for x in sample_data_str.split(',') if x.strip()]

            if len(sample_data) < 3:
                flash('Minimum 3 sample values required', 'danger')
                return render_template('spc/capability/create.html', page_title=page_title)

            study_id, capability = create_capability_study(
                study_name=study_name,
                characteristic_id=int(characteristic_id) if characteristic_id else None,
                process_name=process_name,
                sample_data=sample_data,
                usl=usl,
                lsl=lsl,
                target=target,
                study_date=study_date,
                study_type=study_type,
                notes=notes
            )

            flash(f'Capability study created: Cpk = {capability["cpk"]:.3f}', 'success')
            return redirect(url_for('spc.capability_view', study_id=study_id))

        except ValueError as e:
            flash(f'Invalid sample data format: {e}', 'danger')

    return render_template('spc/capability/create.html', page_title=page_title)


@spc_bp.route('/capability/<int:study_id>')
def capability_view(study_id):
    """View capability study details."""
    page_title = "Capability Study Details"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, l.characteristic_name, l.usl, l.lsl, l.target, l.unit_of_measure
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        WHERE s.id = ?
    """, (study_id,))
    study = cursor.fetchone()

    if not study:
        conn.close()
        flash('Capability study not found', 'danger')
        return redirect(url_for('spc.capability_list'))

    conn.close()

    # Parse sample data
    sample_data = [float(x) for x in study['sample_data'].split(',')]

    # Recalculate capability for display
    capability = CapabilityCalculator.calculate_capability(
        sample_data, study['usl'], study['lsl'], study['target']
    )

    return render_template('spc/capability/view.html',
                         page_title=page_title,
                         study=dict(study),
                         sample_data=sample_data,
                         capability=capability)


@spc_bp.route('/capability/<int:study_id>/compare')
def capability_compare(study_id):
    """Compare capability study with others."""
    page_title = "Capability Comparison"

    conn = get_db()
    cursor = conn.cursor()

    # Get current study
    cursor.execute("""
        SELECT s.*, l.characteristic_name, l.usl, l.lsl, l.target
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        WHERE s.id = ?
    """, (study_id,))
    current = cursor.fetchone()

    if not current:
        conn.close()
        flash('Capability study not found', 'danger')
        return redirect(url_for('spc.capability_list'))

    # Get comparable studies (same characteristic or all if no characteristic)
    if current['characteristic_id']:
        cursor.execute("""
            SELECT s.*, l.characteristic_name
            FROM spc_capability_studies s
            LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
            WHERE s.characteristic_id = ? AND s.id != ?
            ORDER BY s.study_date DESC
            LIMIT 10
        """, (current['characteristic_id'], study_id))
    else:
        cursor.execute("""
            SELECT s.*, l.characteristic_name
            FROM spc_capability_studies s
            LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
            WHERE s.id != ?
            ORDER BY s.study_date DESC
            LIMIT 10
        """, (study_id,))

    comparisons = cursor.fetchall()

    # Get trend data
    cursor.execute("""
        SELECT study_date, cp, cpk, pp, ppk, sigma_level
        FROM spc_capability_studies
        WHERE characteristic_id = ? OR characteristic_id IS NULL
        ORDER BY study_date ASC
        LIMIT 30
    """, (current['characteristic_id'] if current['characteristic_id'] else 0,))
    trend_data = cursor.fetchall()

    conn.close()

    return render_template('spc/capability/compare.html',
                         page_title=page_title,
                         current=dict(current),
                         comparisons=list(comparisons),
                         trend_data=list(trend_data))


@spc_bp.route('/capability/trends')
def capability_trends():
    """View capability trends across all studies."""
    page_title = "Capability Trends"

    conn = get_db()
    cursor = conn.cursor()

    # Get trends by date
    cursor.execute("""
        SELECT DATE(study_date) as date,
               AVG(cp) as avg_cp,
               AVG(cpk) as avg_cpk,
               MIN(cpk) as min_cpk,
               MAX(cpk) as max_cpk,
               COUNT(*) as study_count
        FROM spc_capability_studies
        WHERE study_date >= datetime('now', '-6 months')
        GROUP BY DATE(study_date)
        ORDER BY date ASC
    """)
    date_trends = cursor.fetchall()

    # Get assessment distribution
    cursor.execute("""
        SELECT assessment, COUNT(*) as count
        FROM spc_capability_studies
        GROUP BY assessment
    """)
    distribution = cursor.fetchall()

    # Get capability by characteristic
    cursor.execute("""
        SELECT l.characteristic_name,
               AVG(s.cpk) as avg_cpk,
               COUNT(s.id) as study_count,
               MIN(s.study_date) as first_study,
               MAX(s.study_date) as last_study
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        GROUP BY s.characteristic_id
        ORDER BY avg_cpk ASC
    """)
    by_characteristic = cursor.fetchall()

    conn.close()

    return render_template('spc/capability/trends.html',
                         page_title=page_title,
                         date_trends=list(date_trends),
                         distribution=list(distribution),
                         by_characteristic=list(by_characteristic))


# =============================================================================
# SAMPLING PLANS
# =============================================================================

@spc_bp.route('/sampling-plans')
def sampling_plans_list():
    """List sampling plans."""
    page_title = "Sampling Plans"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_sampling_plans WHERE is_active = 1 ORDER BY plan_name")
    plans = cursor.fetchall()

    conn.close()

    return render_template('spc/sampling/list.html',
                         page_title=page_title,
                         plans=list(plans))


@spc_bp.route('/sampling-plans/create', methods=['GET', 'POST'])
def sampling_plan_create():
    """Create a new sampling plan."""
    page_title = "Create Sampling Plan"

    if request.method == 'POST':
        plan_code = request.form.get('plan_code')
        plan_name = request.form.get('plan_name')
        inspection_type = request.form.get('inspection_type')
        sampling_type = request.form.get('sampling_type', 'SINGLE')
        aql = float(request.form.get('aql', 1.0))

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO spc_sampling_plans
                (plan_code, plan_name, inspection_type, sampling_type, aql)
                VALUES (?, ?, ?, ?, ?)
            """, (plan_code, plan_name, inspection_type, sampling_type, aql))

            plan_id = cursor.lastrowid
            conn.commit()

            # Calculate sample size
            result = SamplingPlanCalculator.calculate_sample_size(1000, aql)

            flash(f'Sampling plan created. Sample size: {result["sample_size"]}', 'success')
            return redirect(url_for('spc.sampling_plan_view', plan_id=plan_id))

        except sqlite3.IntegrityError:
            flash('Plan code already exists', 'danger')
        finally:
            conn.close()

    return render_template('spc/sampling/create.html', page_title=page_title)


@spc_bp.route('/sampling-plans/<int:plan_id>')
def sampling_plan_view(plan_id):
    """View sampling plan details."""
    page_title = "Sampling Plan Details"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_sampling_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()

    if not plan:
        conn.close()
        flash('Sampling plan not found', 'danger')
        return redirect(url_for('spc.sampling_plans_list'))

    conn.close()

    # Get sample size calculation for different lot sizes
    lot_sizes = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
    calculations = []
    for lot_size in lot_sizes:
        result = SamplingPlanCalculator.calculate_sample_size(lot_size, plan['aql'])
        calculations.append(result)

    return render_template('spc/sampling/view.html',
                         page_title=page_title,
                         plan=dict(plan),
                         calculations=calculations)


@spc_bp.route('/api/sampling/evaluate', methods=['POST'])
def evaluate_sampling():
    """Evaluate a lot against a sampling plan."""
    try:
        data = request.get_json()

        lot_size = int(data.get('lot_size', 100))
        defects_found = int(data.get('defects_found', 0))
        aql = float(data.get('aql', 1.0))

        result = SamplingPlanCalculator.evaluate_lot(lot_size, defects_found, aql)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@spc_bp.route('/sampling-plans/<int:plan_id>/inspect', methods=['GET', 'POST'])
def sampling_inspection(plan_id):
    """Record inspection result for a sampling plan."""
    page_title = "Record Inspection"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_sampling_plans WHERE id = ?", (plan_id,))
    plan = cursor.fetchone()
    conn.close()

    if not plan:
        flash('Sampling plan not found', 'danger')
        return redirect(url_for('spc.sampling_plans_list'))

    if request.method == 'POST':
        lot_size = int(request.form.get('lot_size', 100))
        sample_size = int(request.form.get('sample_size', 0))
        defects_found = int(request.form.get('defects_found', 0))
        inspection_date = request.form.get('inspection_date', datetime.now().strftime('%Y-%m-%d'))
        inspector_name = request.form.get('inspector_name', '')
        notes = request.form.get('notes', '')

        # Evaluate based on plan
        result = SamplingPlanCalculator.evaluate_lot(lot_size, defects_found, plan['aql'])

        # Store inspection record
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO spc_aql_inspections
            (plan_id, lot_size, sample_size, defects_found, acceptance_number,
             rejection_number, result, inspection_date, inspector_name, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (plan_id, lot_size, sample_size, defects_found,
              result['acceptance_number'], result['rejection_number'],
              result['decision'], inspection_date, inspector_name, notes))

        conn.commit()
        inspection_id = cursor.lastrowid
        conn.close()

        flash(f'Inspection recorded: {result["decision"]}', 'success' if result['decision'] == 'ACCEPT' else 'warning')
        return redirect(url_for('spc.sampling_plan_view', plan_id=plan_id))

    return render_template('spc/sampling/inspect.html',
                         page_title=page_title,
                         plan=dict(plan))


# =============================================================================
# SPC ALERTS
# =============================================================================

@spc_bp.route('/alerts')
def alerts_list():
    """List SPC anomaly alerts."""
    page_title = "SPC Alerts"

    status = request.args.get('status', 'OPEN')

    alerts = get_open_spc_alerts(status) if status == 'OPEN' else get_open_spc_alerts(status)

    conn = get_db()
    cursor = conn.cursor()

    if status == 'ALL':
        cursor.execute("""
            SELECT a.*, c.chart_name, c.chart_code
            FROM spc_anomaly_alerts a
            LEFT JOIN spc_control_charts c ON a.chart_id = c.id
            ORDER BY a.detected_at DESC
            LIMIT 100
        """)
    else:
        cursor.execute("""
            SELECT a.*, c.chart_name, c.chart_code
            FROM spc_anomaly_alerts a
            LEFT JOIN spc_control_charts c ON a.chart_id = c.id
            WHERE a.status = ?
            ORDER BY a.detected_at DESC
        """, (status,))

    alerts = cursor.fetchall()
    conn.close()

    return render_template('spc/alerts/list.html',
                         page_title=page_title,
                         alerts=list(alerts),
                         current_status=status)


@spc_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an SPC alert."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE spc_anomaly_alerts
        SET status = 'ACKNOWLEDGED',
            acknowledged_by = ?,
            acknowledged_at = datetime('now')
        WHERE id = ?
    """, (1, alert_id))  # Would use session user_id

    conn.commit()
    conn.close()

    flash('Alert acknowledged', 'success')
    return redirect(url_for('spc.alerts_list'))


@spc_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an SPC alert."""
    notes = request.form.get('notes', '')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE spc_anomaly_alerts
        SET status = 'RESOLVED',
            notes = ?,
            resolved_at = datetime('now')
        WHERE id = ?
    """, (notes, alert_id))

    conn.commit()
    conn.close()

    flash('Alert resolved', 'success')
    return redirect(url_for('spc.alerts_list'))


# =============================================================================
# EQUIPMENT / CALIBRATION
# =============================================================================

@spc_bp.route('/equipment')
def equipment_list():
    """List measurement equipment."""
    page_title = "Equipment Registry"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.*,
               (SELECT COUNT(*) FROM spc_calibration_records WHERE equipment_id = e.id) as calibration_count
        FROM spc_equipment_registry e
        WHERE e.is_active = 1
        ORDER BY e.equipment_name
    """)
    equipment = cursor.fetchall()

    conn.close()

    return render_template('spc/equipment/list.html',
                         page_title=page_title,
                         equipment=list(equipment))


@spc_bp.route('/equipment/create', methods=['GET', 'POST'])
def equipment_create():
    """Register new equipment."""
    page_title = "Register Equipment"

    if request.method == 'POST':
        equipment_code = request.form.get('equipment_code')
        equipment_name = request.form.get('equipment_name')
        equipment_type = request.form.get('equipment_type')
        manufacturer = request.form.get('manufacturer')
        model_number = request.form.get('model_number')
        serial_number = request.form.get('serial_number')
        location = request.form.get('location')
        measurement_range_min = request.form.get('measurement_range_min')
        measurement_range_max = request.form.get('measurement_range_max')
        resolution = request.form.get('resolution')
        accuracy = request.form.get('accuracy')
        calibration_interval = request.form.get('calibration_interval_days', 90)

        try:
            equipment_id = register_equipment(
                equipment_code=equipment_code,
                equipment_name=equipment_name,
                equipment_type=equipment_type,
                manufacturer=manufacturer,
                model_number=model_number,
                serial_number=serial_number,
                location=location,
                measurement_range_min=float(measurement_range_min) if measurement_range_min else None,
                measurement_range_max=float(measurement_range_max) if measurement_range_max else None,
                resolution=float(resolution) if resolution else None,
                accuracy=float(accuracy) if accuracy else None,
                calibration_interval_days=int(calibration_interval)
            )

            flash('Equipment registered successfully', 'success')
            return redirect(url_for('spc.equipment_view', equipment_id=equipment_id))

        except sqlite3.IntegrityError:
            flash('Equipment code already exists', 'danger')

    return render_template('spc/equipment/create.html', page_title=page_title)


@spc_bp.route('/equipment/<int:equipment_id>')
def equipment_view(equipment_id):
    """View equipment details."""
    page_title = "Equipment Details"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_equipment_registry WHERE id = ?", (equipment_id,))
    equipment = cursor.fetchone()

    if not equipment:
        conn.close()
        flash('Equipment not found', 'danger')
        return redirect(url_for('spc.equipment_list'))

    # Get calibration history
    cursor.execute("""
        SELECT * FROM spc_calibration_records
        WHERE equipment_id = ?
        ORDER BY calibration_date DESC
        LIMIT 20
    """, (equipment_id,))
    calibrations = cursor.fetchall()

    # Get GRR studies
    cursor.execute("""
        SELECT * FROM spc_gage_rr_studies
        WHERE gage_id = ?
        ORDER BY study_date DESC
        LIMIT 10
    """, (equipment_id,))
    grr_studies = cursor.fetchall()

    conn.close()

    return render_template('spc/equipment/view.html',
                         page_title=page_title,
                         equipment=dict(equipment),
                         calibrations=list(calibrations),
                         grr_studies=list(grr_studies))


@spc_bp.route('/equipment/<int:equipment_id>/calibrate', methods=['GET', 'POST'])
def equipment_calibrate(equipment_id):
    """Record calibration for equipment."""
    page_title = "Record Calibration"

    if request.method == 'POST':
        calibration_date = request.form.get('calibration_date', datetime.now().strftime('%Y-%m-%d'))
        as_found_min = float(request.form.get('as_found_min', 0))
        as_found_max = float(request.form.get('as_found_max', 0))
        as_left_min = float(request.form.get('as_left_min', 0)) if request.form.get('as_left_min') else None
        as_left_max = float(request.form.get('as_left_max', 0)) if request.form.get('as_left_max') else None
        tolerance = float(request.form.get('tolerance', 0)) if request.form.get('tolerance') else None
        measurement_uncertainty = float(request.form.get('measurement_uncertainty', 0)) if request.form.get('measurement_uncertainty') else None
        result = request.form.get('result', 'PASSED')
        certificate_number = request.form.get('certificate_number')
        standards_used = request.form.get('standards_used')
        temperature = float(request.form.get('temperature', 0)) if request.form.get('temperature') else None
        humidity = float(request.form.get('humidity', 0)) if request.form.get('humidity') else None
        notes = request.form.get('notes')

        try:
            cal_id = record_calibration(
                equipment_id=equipment_id,
                calibration_date=calibration_date,
                performed_by=1,  # Would use session user_id
                as_found_min=as_found_min,
                as_found_max=as_found_max,
                as_left_min=as_left_min,
                as_left_max=as_left_max,
                tolerance=tolerance,
                measurement_uncertainty=measurement_uncertainty,
                result=result,
                certificate_number=certificate_number,
                standards_used=standards_used,
                temperature=temperature,
                humidity=humidity,
                notes=notes
            )

            flash(f'Calibration recorded: {result}', 'success')
            return redirect(url_for('spc.equipment_view', equipment_id=equipment_id))

        except Exception as e:
            flash(f'Error recording calibration: {e}', 'danger')

    return render_template('spc/equipment/calibrate.html', page_title=page_title)


# =============================================================================
# GAGE R&R STUDIES
# =============================================================================

@spc_bp.route('/gage-rr')
def gage_rr_list():
    """List Gage R&R studies."""
    page_title = "Gage R&R Studies"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.*, e.equipment_name, e.equipment_code
        FROM spc_gage_rr_studies g
        LEFT JOIN spc_equipment_registry e ON g.gage_id = e.id
        ORDER BY g.study_date DESC
        LIMIT 50
    """)
    studies = cursor.fetchall()

    conn.close()

    return render_template('spc/gage_rr/list.html',
                         page_title=page_title,
                         studies=list(studies))


@spc_bp.route('/gage-rr/create', methods=['GET', 'POST'])
def gage_rr_create():
    """Create a Gage R&R study."""
    page_title = "Create Gage R&R Study"

    conn = get_db()
    cursor = conn.cursor()

    # Get available equipment
    cursor.execute("SELECT id, equipment_code, equipment_name FROM spc_equipment_registry WHERE is_active = 1")
    equipment = cursor.fetchall()
    conn.close()

    if request.method == 'POST':
        gage_id = request.form.get('gage_id')
        study_type = request.form.get('study_type', 'GAGE_RR')
        study_date = request.form.get('study_date', datetime.now().strftime('%Y-%m-%d'))

        # Parse measurements (format: part_op1_val,part_op2_val|part_op1_val,part_op2_val|...)
        measurements_str = request.form.get('measurements', '')
        part_numbers = request.form.get.getlist('part_number')
        operator_numbers = request.form.get.getlist('operator_number')

        try:
            # Parse measurements into nested list
            measurements = []
            for row in measurements_str.split('|'):
                if row.strip():
                    measurements.append([float(x) for x in row.split(',')])

            study_id, metrics = perform_gage_rr_study(
                gage_id=int(gage_id),
                part_numbers=part_numbers,
                operator_numbers=operator_numbers,
                measurements=measurements,
                study_date=study_date,
                study_type=study_type
            )

            flash(f'Gage R&R Study completed. Assessment: {metrics["assessment"]}', 'success')
            return redirect(url_for('spc.gage_rr_view', study_id=study_id))

        except Exception as e:
            flash(f'Error creating study: {e}', 'danger')

    return render_template('spc/gage_rr/create.html',
                         page_title=page_title,
                         equipment=list(equipment))


@spc_bp.route('/gage-rr/<int:study_id>')
def gage_rr_view(study_id):
    """View Gage R&R study details."""
    page_title = "Gage R&R Study Details"

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.*, e.equipment_name, e.equipment_code
        FROM spc_gage_rr_studies g
        LEFT JOIN spc_equipment_registry e ON g.gage_id = e.id
        WHERE g.id = ?
    """, (study_id,))
    study = cursor.fetchone()

    if not study:
        conn.close()
        flash('Gage R&R study not found', 'danger')
        return redirect(url_for('spc.gage_rr_list'))

    conn.close()

    return render_template('spc/gage_rr/view.html',
                         page_title=page_title,
                         study=dict(study))


# =============================================================================
# API ENDPOINTS
# =============================================================================

@spc_bp.route('/api/metrics')
def api_metrics():
    """Get SPC metrics summary API."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    chart_id = request.args.get('chart_id', type=int)

    metrics = get_spc_metrics_summary(start_date, end_date, chart_id)
    return jsonify(metrics)


@spc_bp.route('/api/chart/<int:chart_id>/data')
def api_chart_data(chart_id):
    """Get control chart data for charting."""
    limit = int(request.args.get('limit', 50))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    data = get_control_chart_data(chart_id, limit, start_date, end_date)

    # Get control limits
    if len(data) >= 5:
        values = [d['average'] for d in data]
        limits = SPCCalculator.calculate_imr_control_limits(values)
    else:
        limits = None

    return jsonify({
        'data': data,
        'limits': limits
    })


@spc_bp.route('/api/capability/calculate', methods=['POST'])
def api_calculate_capability():
    """Calculate capability from provided data."""
    try:
        data = request.get_json()

        values = [float(x) for x in data.get('values', [])]
        usl = float(data.get('usl', 0))
        lsl = float(data.get('lsl', 0))
        target = float(data.get('target', 0)) if data.get('target') else None

        capability = CapabilityCalculator.calculate_capability(values, usl, lsl, target)

        return jsonify(capability)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@spc_bp.route('/api/sampling/calculate', methods=['POST'])
def api_calculate_sampling():
    """Calculate sampling plan from parameters."""
    try:
        data = request.get_json()

        lot_size = int(data.get('lot_size', 100))
        aql = float(data.get('aql', 1.0))
        inspection_level = data.get('inspection_level', 'II')

        result = SamplingPlanCalculator.calculate_sample_size(lot_size, aql, inspection_level)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@spc_bp.route('/api/alerts/count')
def api_alerts_count():
    """Get count of open alerts by severity."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT severity, COUNT(*) as count
        FROM spc_anomaly_alerts
        WHERE status = 'OPEN'
        GROUP BY severity
    """)
    rows = cursor.fetchall()
    conn.close()

    alerts = {row['severity']: row['count'] for row in rows}

    return jsonify({
        'total': sum(alerts.values()),
        'by_severity': alerts
    })


# =============================================================================
# EXPORT
# =============================================================================

@spc_bp.route('/export/capability/<int:study_id>')
def export_capability(study_id):
    """Export capability study to PDF/Excel."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, l.characteristic_name, l.usl, l.lsl, l.target, l.unit_of_measure
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        WHERE s.id = ?
    """, (study_id,))
    study = cursor.fetchone()
    conn.close()

    if not study:
        flash('Study not found', 'danger')
        return redirect(url_for('spc.capability_list'))

    # Create Excel export with enhanced formatting
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, GradientFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Capability Study"

    # Define styles
    header_font = Font(bold=True, size=14, color='FFFFFF')
    section_font = Font(bold=True, size=12, color='FFFFFF')
    label_font = Font(bold=True)
    value_font = Font(size=11)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    header_fill = PatternFill(start_color='4F46E5', end_color='4F46E5', fill_type='solid')
    section_fill = PatternFill(start_color='7C3AED', end_color='7C3AED', fill_type='solid')
    light_fill = PatternFill(start_color='F3F4F6', end_color='F3F4F6', fill_type='solid')

    # Set column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15

    # Title
    ws.merge_cells('A1:C1')
    ws['A1'] = "Process Capability Study Report"
    ws['A1'].font = Font(bold=True, size=18, color='4F46E5')
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30

    # Company/Report Info
    ws['A2'] = f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    ws['A2'].font = Font(size=9, italic=True, color='6B7280')

    # Study Information Section
    ws.merge_cells('A4:C4')
    ws['A4'] = "STUDY INFORMATION"
    ws['A4'].fill = section_fill
    ws['A4'].font = section_font
    ws['A4'].alignment = Alignment(horizontal='center')

    ws['A5'] = "Study Number"
    ws['A5'].font = label_font
    ws['B5'] = study['study_number']
    ws['B5'].fill = light_fill

    ws['A6'] = "Study Name"
    ws['A6'].font = label_font
    ws['B6'] = study['study_name']
    ws['B6'].fill = light_fill

    ws['A7'] = "Study Date"
    ws['A7'].font = label_font
    ws['B7'] = study['study_date']
    ws['B7'].fill = light_fill

    ws['A8'] = "Sample Size"
    ws['A8'].font = label_font
    ws['B8'] = study['sample_size']
    ws['B8'].fill = light_fill

    ws['A9'] = "Study Type"
    ws['A9'].font = label_font
    ws['B9'] = study['study_type']
    ws['B9'].fill = light_fill

    # Process Statistics Section
    ws.merge_cells('A11:C11')
    ws['A11'] = "PROCESS STATISTICS"
    ws['A11'].fill = section_fill
    ws['A11'].font = section_font
    ws['A11'].alignment = Alignment(horizontal='center')

    mean = float(study['mean']) if study['mean'] else 0
    std_dev = float(study['std_dev']) if study['std_dev'] else 0

    ws['A12'] = "Mean (μ)"
    ws['A12'].font = label_font
    ws['B12'] = f"{mean:.6f}"
    ws['B12'].alignment = Alignment(horizontal='right')

    ws['A13'] = "Standard Deviation (σ)"
    ws['A13'].font = label_font
    ws['B13'] = f"{std_dev:.6f}"
    ws['B13'].alignment = Alignment(horizontal='right')

    ws['A14'] = "Sample Size"
    ws['A14'].font = label_font
    ws['B14'] = study['sample_size']
    ws['B14'].alignment = Alignment(horizontal='right')

    # Specification Limits Section
    ws.merge_cells('A16:C16')
    ws['A16'] = "SPECIFICATION LIMITS"
    ws['A16'].fill = section_fill
    ws['A16'].font = section_font
    ws['A16'].alignment = Alignment(horizontal='center')

    ws['A17'] = "Upper Specification Limit (USL)"
    ws['A17'].font = label_font
    ws['B17'] = f"{study['usl']:.4f}" if study['usl'] else 'N/A'
    ws['B17'].font = Font(color='DC2626', bold=True)

    ws['A18'] = "Target"
    ws['A18'].font = label_font
    ws['B18'] = f"{study['target']:.4f}" if study['target'] else 'N/A'
    ws['B18'].font = Font(color='059669', bold=True)

    ws['A19'] = "Lower Specification Limit (LSL)"
    ws['A19'].font = label_font
    ws['B19'] = f"{study['lsl']:.4f}" if study['lsl'] else 'N/A'
    ws['B19'].font = Font(color='D97706', bold=True)

    unit = study['unit_of_measure'] or ''
    ws['C17'] = unit
    ws['C18'] = unit
    ws['C19'] = unit

    # Capability Indices Section
    ws.merge_cells('A21:C21')
    ws['A21'] = "CAPABILITY INDICES"
    ws['A21'].fill = section_fill
    ws['A21'].font = section_font
    ws['A21'].alignment = Alignment(horizontal='center')

    ws['A22'] = "Cp (Potential Capability)"
    ws['A22'].font = label_font
    ws['B22'] = f"{study['cp']:.4f}" if study['cp'] else 'N/A'

    ws['A23'] = "Cpk (Actual Capability)"
    ws['A23'].font = label_font
    cpk_val = study['cpk']
    ws['B23'] = f"{cpk_val:.4f}" if cpk_val else 'N/A'
    if cpk_val and float(cpk_val) >= 1.33:
        ws['B23'].font = Font(color='059669', bold=True)
    elif cpk_val and float(cpk_val) >= 1.0:
        ws['B23'].font = Font(color='D97706', bold=True)
    else:
        ws['B23'].font = Font(color='DC2626', bold=True)

    ws['A24'] = "Cpu (Upper Capability)"
    ws['A24'].font = label_font
    ws['B24'] = f"{study.get('cpu', 'N/A'):.4f}" if study.get('cpu') else 'N/A'

    ws['A25'] = "Cpl (Lower Capability)"
    ws['A25'].font = label_font
    ws['B25'] = f"{study.get('cpl', 'N/A'):.4f}" if study.get('cpl') else 'N/A'

    ws['A26'] = "Pp (Overall Potential)"
    ws['A26'].font = label_font
    ws['B26'] = f"{study['pp']:.4f}" if study['pp'] else 'N/A'

    ws['A27'] = "Ppk (Overall Performance)"
    ws['A27'].font = label_font
    ws['B27'] = f"{study['ppk']:.4f}" if study['ppk'] else 'N/A'

    # Sigma Level Section
    ws.merge_cells('A29:C29')
    ws['A29'] = "SIGMA LEVEL & PERFORMANCE"
    ws['A29'].fill = section_fill
    ws['A29'].font = section_font
    ws['A29'].alignment = Alignment(horizontal='center')

    sigma_val = study['sigma_level']
    ws['A30'] = "Sigma Level"
    ws['A30'].font = label_font
    ws['B30'] = f"{sigma_val:.2f}σ" if sigma_val else 'N/A'

    dpmo_val = study['ppmm']
    ws['A31'] = "DPMO (Defects Per Million Opportunities)"
    ws['A31'].font = label_font
    ws['B31'] = f"{dpmo_val:,.0f}" if dpmo_val else '0'

    ws['A32'] = "Process Assessment"
    ws['A32'].font = label_font
    ws['B32'] = study['assessment'] or 'N/A'
    assessment = study['assessment']
    if assessment == 'WORLD_CLASS':
        ws['B32'].font = Font(color='059669', bold=True)
    elif assessment == 'EXCELLENT':
        ws['B32'].font = Font(color='7C3AED', bold=True)
    elif assessment == 'GOOD':
        ws['B32'].font = Font(color='2563EB', bold=True)
    elif assessment == 'ACCEPTABLE':
        ws['B32'].font = Font(color='D97706', bold=True)
    else:
        ws['B32'].font = Font(color='DC2626', bold=True)

    # Assessment Legend
    ws.merge_cells('A34:C34')
    ws['A34'] = "ASSESSMENT GUIDELINES"
    ws['A34'].fill = header_fill
    ws['A34'].font = section_font
    ws['A34'].alignment = Alignment(horizontal='center')

    guidelines = [
        ("Cpk ≥ 2.0", "WORLD_CLASS", "World Class - Six Sigma Performance"),
        ("Cpk ≥ 1.67", "EXCELLENT", "Excellent - Exceptional Process Capability"),
        ("Cpk ≥ 1.33", "GOOD", "Good - Meets Customer Requirements"),
        ("Cpk ≥ 1.0", "ACCEPTABLE", "Acceptable - Baseline Process Capability"),
        ("Cpk ≥ 0.67", "MARGINAL", "Marginal - Requires Monitoring"),
        ("Cpk < 0.67", "NOT_CAPABLE", "Not Capable - Immediate Action Required"),
    ]

    row = 35
    for criteria, level, desc in guidelines:
        ws[f'A{row}'] = criteria
        ws[f'B{row}'] = level
        ws[f'C{row}'] = desc
        ws[f'A{row}'].font = label_font
        row += 1

    # Apply borders to data cells
    for r in range(5, 32):
        for col in ['A', 'B', 'C']:
            ws[f'{col}{r}'].border = thin_border

    # Save
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"Capability_Study_{study['study_number']}.xlsx"
    )


@spc_bp.route('/export/chart/<int:chart_id>')
def export_chart_data(chart_id):
    """Export control chart data to CSV."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT chart_name, chart_code, chart_type FROM spc_control_charts WHERE id = ?", (chart_id,))
    chart = cursor.fetchone()

    if not chart:
        conn.close()
        flash('Chart not found', 'danger')
        return redirect(url_for('spc.charts_list'))

    cursor.execute("""
        SELECT m.measurement_date, m.measurement_group, m.sample_size,
               m.average, m.range_val, m.std_dev, m.control_status,
               s.usl, s.lsl, s.target
        FROM spc_measurement_data m
        LEFT JOIN spc_specification_limits s ON m.chart_id = s.chart_id AND s.is_active = 1
        WHERE m.chart_id = ?
        ORDER BY m.measurement_date ASC
    """, (chart_id,))
    data = cursor.fetchall()
    conn.close()

    # Create CSV
    from csv import writer
    output = BytesIO()
    csv_writer = writer(output)

    # Header
    csv_writer.writerow([
        'Date', 'Group', 'Sample Size', 'Mean', 'Range', 'Std Dev',
        'Status', 'USL', 'Target', 'LSL'
    ])

    # Data rows
    for row in data:
        csv_writer.writerow([
            row['measurement_date'],
            row['measurement_group'],
            row['sample_size'],
            f"{row['average']:.6f}" if row['average'] else '',
            f"{row['range_val']:.6f}" if row['range_val'] else '',
            f"{row['std_dev']:.6f}" if row['std_dev'] else '',
            row['control_status'],
            f"{row['usl']:.4f}" if row['usl'] else '',
            f"{row['target']:.4f}" if row['target'] else '',
            f"{row['lsl']:.4f}" if row['lsl'] else ''
        ])

    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"ControlChart_{chart['chart_code']}_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@spc_bp.route('/export/alerts')
def export_alerts():
    """Export alerts to CSV."""
    status = request.args.get('status', 'ALL')

    conn = get_db()
    cursor = conn.cursor()

    if status == 'ALL':
        cursor.execute("""
            SELECT a.alert_number, a.rule_violated, a.rule_description,
                   a.severity, a.status, a.detected_at, a.acknowledged_at,
                   a.resolved_at, c.chart_name, c.chart_code
            FROM spc_anomaly_alerts a
            LEFT JOIN spc_control_charts c ON a.chart_id = c.id
            ORDER BY a.detected_at DESC
        """)
    else:
        cursor.execute("""
            SELECT a.alert_number, a.rule_violated, a.rule_description,
                   a.severity, a.status, a.detected_at, a.acknowledged_at,
                   a.resolved_at, c.chart_name, c.chart_code
            FROM spc_anomaly_alerts a
            LEFT JOIN spc_control_charts c ON a.chart_id = c.id
            WHERE a.status = ?
            ORDER BY a.detected_at DESC
        """, (status,))

    alerts = cursor.fetchall()
    conn.close()

    from csv import writer
    output = BytesIO()
    csv_writer = writer(output)

    csv_writer.writerow([
        'Alert Number', 'Chart', 'Rule Violated', 'Description',
        'Severity', 'Status', 'Detected', 'Acknowledged', 'Resolved'
    ])

    for alert in alerts:
        csv_writer.writerow([
            alert['alert_number'],
            alert['chart_name'] or alert['chart_code'],
            alert['rule_violated'],
            alert['rule_description'],
            alert['severity'],
            alert['status'],
            alert['detected_at'],
            alert['acknowledged_at'] or '',
            alert['resolved_at'] or ''
        ])

    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"SPC_Alerts_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@spc_bp.route('/export/equipment')
def export_equipment():
    """Export equipment calibration status to CSV."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.equipment_code, e.equipment_name, e.equipment_type,
               e.manufacturer, e.model_number, e.serial_number,
               e.calibration_status, e.last_calibration_date,
               e.next_calibration_date, e.calibration_interval_days,
               (SELECT COUNT(*) FROM spc_calibration_records WHERE equipment_id = e.id) as calibration_count
        FROM spc_equipment_registry e
        WHERE e.is_active = 1
        ORDER BY e.equipment_name
    """)
    equipment = cursor.fetchall()
    conn.close()

    from csv import writer
    output = BytesIO()
    csv_writer = writer(output)

    csv_writer.writerow([
        'Code', 'Name', 'Type', 'Manufacturer', 'Model', 'Serial',
        'Status', 'Last Calibration', 'Next Due', 'Interval (days)', 'Calibrations'
    ])

    for eq in equipment:
        csv_writer.writerow([
            eq['equipment_code'],
            eq['equipment_name'],
            eq['equipment_type'],
            eq['manufacturer'] or '',
            eq['model_number'] or '',
            eq['serial_number'] or '',
            eq['calibration_status'],
            eq['last_calibration_date'] or 'Never',
            eq['next_calibration_date'] or 'Not Set',
            eq['calibration_interval_days'],
            eq['calibration_count']
        ])

    output.seek(0)

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"SPC_Equipment_{datetime.now().strftime('%Y%m%d')}.csv"
    )


@spc_bp.route('/api/we-rules/evaluate', methods=['POST'])
def api_evaluate_we_rules():
    """Evaluate Western Electric rules for provided data."""
    try:
        data = request.get_json()

        values = [float(x) for x in data.get('values', [])]
        mean = float(data.get('mean', 0))
        std_dev = float(data.get('std_dev', 0))

        if len(values) < 5:
            return jsonify({'error': 'Minimum 5 data points required'}), 400

        if std_dev <= 0:
            return jsonify({'error': 'Standard deviation must be positive'}), 400

        violations = SPCCalculator.check_western_electric_rules(values, mean, std_dev, {})

        return jsonify({
            'violations': violations,
            'total_violations': len(violations),
            'has_critical': any(v['severity'] == 'CRITICAL' for v in violations),
            'has_major': any(v['severity'] == 'MAJOR' for v in violations),
            'status': 'OUT_OF_CONTROL' if any(v['severity'] in ['CRITICAL', 'MAJOR'] for v in violations) else 'IN_CONTROL'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@spc_bp.route('/api/chart-types')
def api_chart_types():
    """Get available chart types."""
    chart_types = [
        {'code': 'I_MR', 'name': 'Individual-Moving Range (I-MR)', 'description': 'For individual measurements'},
        {'code': 'XBAR_R', 'name': 'X-bar and R Chart', 'description': 'Variables chart for subgroup sizes 2-10'},
        {'code': 'XBAR_S', 'name': 'X-bar and S Chart', 'description': 'Variables chart for subgroup sizes >10'},
        {'code': 'C', 'name': 'C Chart', 'description': 'Count of defects'},
        {'code': 'P', 'name': 'P Chart', 'description': 'Proportion defective'},
        {'code': 'NP', 'name': 'NP Chart', 'description': 'Number of defective items'},
        {'code': 'U', 'name': 'U Chart', 'description': 'Defects per unit'},
    ]
    return jsonify(chart_types)


@spc_bp.route('/api/aql-table')
def api_aql_table():
    """Get AQL sampling table."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM spc_aql_levels ORDER BY lot_size_min")
    rows = cursor.fetchall()
    conn.close()

    aql_levels = [dict(row) for row in rows]

    return jsonify({
        'aql_values': [0.010, 0.015, 0.025, 0.040, 0.065, 0.100, 0.150, 0.250, 0.400, 0.650, 1.0],
        'data': aql_levels
    })


@spc_bp.route('/api/equipment/status')
def api_equipment_status():
    """Get equipment calibration status summary."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT calibration_status, COUNT(*) as count
        FROM spc_equipment_registry
        WHERE is_active = 1
        GROUP BY calibration_status
    """)
    rows = cursor.fetchall()
    conn.close()

    status_counts = {row['calibration_status']: row['count'] for row in rows}

    total = sum(status_counts.values())
    overdue = status_counts.get('OVERDUE', 0)
    due = status_counts.get('DUE', 0)
    current = status_counts.get('CURRENT', 0)

    return jsonify({
        'total': total,
        'current': current,
        'due': due,
        'overdue': overdue,
        'by_status': status_counts,
        'compliance_rate': round((current / total * 100) if total > 0 else 100, 2)
    })


@spc_bp.route('/api/dashboard/summary')
def api_dashboard_summary():
    """Get dashboard summary data for charts."""
    conn = get_db()
    cursor = conn.cursor()

    # Measurement trends (last 30 days)
    cursor.execute("""
        SELECT DATE(measurement_date) as date,
               AVG(average) as avg_value,
               COUNT(*) as measurement_count,
               SUM(CASE WHEN control_status != 'IN_CONTROL' THEN 1 ELSE 0 END) as ooc_count
        FROM spc_measurement_data
        WHERE measurement_date >= datetime('now', '-30 days')
        GROUP BY DATE(measurement_date)
        ORDER BY date ASC
    """)
    trends = cursor.fetchall()

    # Capability distribution
    cursor.execute("""
        SELECT assessment, COUNT(*) as count
        FROM spc_capability_studies
        GROUP BY assessment
    """)
    capability_dist = cursor.fetchall()

    # Chart types distribution
    cursor.execute("""
        SELECT c.chart_type, COUNT(m.id) as measurement_count
        FROM spc_control_charts c
        LEFT JOIN spc_measurement_data m ON c.id = m.chart_id
        GROUP BY c.chart_type
    """)
    chart_types = cursor.fetchall()

    conn.close()

    return jsonify({
        'measurement_trends': [dict(row) for row in trends],
        'capability_distribution': {row['assessment']: row['count'] for row in capability_dist},
        'chart_types_distribution': {row['chart_type']: row['measurement_count'] for row in chart_types}
    })
