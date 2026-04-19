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
        SELECT s.*, l.characteristic_name, l.usl, l.lsl, l.target
        FROM spc_capability_studies s
        LEFT JOIN spc_specification_limits l ON s.characteristic_id = l.id
        WHERE s.id = ?
    """, (study_id,))
    study = cursor.fetchone()
    conn.close()

    if not study:
        flash('Study not found', 'danger')
        return redirect(url_for('spc.capability_list'))

    # Create Excel export
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Capability Study"

    # Styles
    header_font = Font(bold=True, size=12)
    label_font = Font(bold=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Header
    ws['A1'] = "Process Capability Study Report"
    ws['A1'].font = Font(bold=True, size=16)
    ws.merge_cells('A1:C1')

    # Study Info
    ws['A3'] = "Study Number"
    ws['B3'] = study['study_number']
    ws['A4'] = "Study Name"
    ws['B4'] = study['study_name']
    ws['A5'] = "Study Date"
    ws['B5'] = study['study_date']
    ws['A6'] = "Sample Size"
    ws['B6'] = study['sample_size']

    # Capability Metrics
    ws['A8'] = "Process Statistics"
    ws['A8'].font = header_font
    ws['A9'] = "Mean"
    ws['B9'] = f"{study['mean']:.4f}"
    ws['A10'] = "Std Dev"
    ws['B10'] = f"{study['std_dev']:.4f}"

    # Specification Limits
    ws['A12'] = "Specification Limits"
    ws['A12'].font = header_font
    ws['A13'] = "USL"
    ws['B13'] = study['usl']
    ws['A14'] = "Target"
    ws['B14'] = study['target']
    ws['A15'] = "LSL"
    ws['B15'] = study['lsl']

    # Capability Indices
    ws['A17'] = "Capability Indices"
    ws['A17'].font = header_font
    ws['A18'] = "Cp"
    ws['B18'] = f"{study['cp']:.3f}"
    ws['A19'] = "Cpk"
    ws['B19'] = f"{study['cpk']:.3f}"
    ws['A20'] = "Pp"
    ws['B20'] = f"{study['pp']:.3f}"
    ws['A21'] = "Ppk"
    ws['B21'] = f"{study['ppk']:.3f}"

    # Sigma Level
    ws['A23'] = "Sigma Level"
    ws['B23'] = f"{study['sigma_level']:.2f}σ"
    ws['A24'] = "DPMO"
    ws['B24'] = f"{study['ppmm']:.0f}"
    ws['A25'] = "Assessment"
    ws['B25'] = study['assessment']

    # Apply borders
    for row in range(3, 26):
        for col in ['A', 'B']:
            ws[f'{col}{row}'].border = border

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
