"""
SPC / Statistical Process Control Module
=========================================
Enterprise-grade SPC system matching and exceeding SAP QM capabilities.

Features:
- Control Charts (X-bar, R, S, C, P, NP, U, I-MR)
- Process Capability Analysis (Cp, Cpk, Pp, Ppk)
- Sampling Plans (AQL, ANSI/ASQ Z1.4, ISO 2859)
- Anomaly Detection (Western Electric Rules)
- Real-time SPC Metrics
- DPMO and Sigma Level Calculations
"""

import sqlite3
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from database import get_db

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def initialize_spc_tables():
    """Initialize SPC/Quality Analytics database tables."""
    with get_db() as db:
        # =========================================================================
        # SPC CONTROL CHART CONFIGURATIONS
        # =========================================================================
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_control_charts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_code TEXT UNIQUE NOT NULL,
                chart_name TEXT NOT NULL,
                chart_type TEXT NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Measurement Data (for control charts)
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_measurement_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_id INTEGER,
                chart_code TEXT NOT NULL,
                measurement_group TEXT NOT NULL,
                sample_size INTEGER DEFAULT 1,
                sample_values TEXT NOT NULL,
                average REAL,
                range_val REAL,
                std_dev REAL,
                measurement_date TEXT NOT NULL,
                recorded_by INTEGER,
                notes TEXT,
                is_out_of_control INTEGER DEFAULT 0,
                control_status TEXT DEFAULT 'IN_CONTROL',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (chart_id) REFERENCES spc_control_charts(id)
            )
        """)

        # SPC Specification Limits
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_specification_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chart_id INTEGER,
                characteristic_name TEXT NOT NULL,
                usl REAL,
                lsl REAL,
                target REAL,
                ucl REAL,
                lcl REAL,
                ucl_2 REAL,
                lcl_2 REAL,
                ucl_3 REAL,
                lcl_3 REAL,
                unit_of_measure TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (chart_id) REFERENCES spc_control_charts(id)
            )
        """)

        # Process Capability Studies
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_capability_studies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_number TEXT UNIQUE NOT NULL,
                study_name TEXT NOT NULL,
                characteristic_id INTEGER,
                process_name TEXT,
                sample_size INTEGER NOT NULL,
                sample_data TEXT NOT NULL,
                mean REAL,
                std_dev REAL,
                cp REAL,
                cpk REAL,
                pp REAL,
                ppk REAL,
                ppmm REAL,
                sigma_level REAL,
                dpmo REAL,
                assessment TEXT,
                study_date TEXT NOT NULL,
                study_type TEXT DEFAULT 'INITIAL',
                notes TEXT,
                status TEXT DEFAULT 'COMPLETED',
                created_by INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Sampling Plans
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_sampling_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_code TEXT UNIQUE NOT NULL,
                plan_name TEXT NOT NULL,
                inspection_type TEXT NOT NULL,
                sampling_type TEXT DEFAULT 'SINGLE',
                aql REAL DEFAULT 1.0,
                acceptance_number INTEGER DEFAULT 1,
                rejection_number INTEGER,
                sample_size_code TEXT,
                double_sample_n1 INTEGER,
                double_sample_n2 INTEGER,
                double_sample_c1 INTEGER,
                double_sample_c2 INTEGER,
                skip_lot_enabled INTEGER DEFAULT 0,
                skip_lot_skip_number INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # AQL Master Table (ANSI/ASQ Z1.4, ISO 2859)
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_aql_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_size_min INTEGER,
                lot_size_max INTEGER,
                aql_010_code TEXT,
                aql_015_code TEXT,
                aql_025_code TEXT,
                aql_040_code TEXT,
                aql_065_code TEXT,
                aql_100_code TEXT,
                aql_150_code TEXT,
                aql_250_code TEXT,
                aql_400_code TEXT,
                aql_650_code TEXT,
                aql_1000_code TEXT
            )
        """)

        # AQL Inspection Records
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_aql_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                lot_size INTEGER NOT NULL,
                sample_size INTEGER NOT NULL,
                defects_found INTEGER NOT NULL,
                acceptance_number INTEGER,
                rejection_number INTEGER,
                result TEXT NOT NULL,
                inspection_date TEXT NOT NULL,
                inspector_name TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (plan_id) REFERENCES spc_sampling_plans(id)
            )
        """)

        # SPC Anomaly Alerts
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_anomaly_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_number TEXT UNIQUE NOT NULL,
                chart_id INTEGER,
                measurement_id INTEGER,
                measurement_group TEXT,
                rule_violated TEXT NOT NULL,
                rule_description TEXT,
                severity TEXT DEFAULT 'WARNING',
                status TEXT DEFAULT 'OPEN',
                detected_at TEXT NOT NULL,
                acknowledged_by INTEGER,
                acknowledged_at TEXT,
                resolved_at TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Western Electric Rules Configuration
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_western_electric_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT UNIQUE NOT NULL,
                rule_name TEXT NOT NULL,
                rule_description TEXT,
                zone_a_violation TEXT,
                zone_b_violation TEXT,
                zone_c_violation TEXT,
                pattern_violation TEXT,
                severity_weight INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Quality Metrics (real-time calculations)
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_code TEXT UNIQUE NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                previous_value REAL,
                change_percent REAL,
                trend_direction TEXT,
                sigma_level REAL,
                dpmo REAL,
                yield_percent REAL,
                fpy_percent REAL,
                calculated_at TEXT NOT NULL,
                period_start TEXT,
                period_end TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Trend Analysis
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_trend_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_number TEXT UNIQUE NOT NULL,
                chart_id INTEGER,
                analysis_type TEXT NOT NULL,
                trend_type TEXT,
                slope REAL,
                intercept REAL,
                r_squared REAL,
                prediction TEXT,
                confidence_interval TEXT,
                recommendation TEXT,
                analyzed_at TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Equipment/Gage Registry
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_equipment_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_code TEXT UNIQUE NOT NULL,
                equipment_name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                manufacturer TEXT,
                model_number TEXT,
                serial_number TEXT,
                location TEXT,
                custodian_id INTEGER,
                measurement_range_min REAL,
                measurement_range_max REAL,
                resolution REAL,
                accuracy REAL,
                calibration_status TEXT DEFAULT 'DUE',
                last_calibration_date TEXT,
                next_calibration_date TEXT,
                calibration_interval_days INTEGER DEFAULT 90,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # SPC Calibration Records
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_calibration_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calibration_number TEXT UNIQUE NOT NULL,
                equipment_id INTEGER NOT NULL,
                calibration_date TEXT NOT NULL,
                performed_by INTEGER,
                standards_used TEXT,
                temperature REAL,
                humidity REAL,
                as_found_min REAL,
                as_found_max REAL,
                as_left_min REAL,
                as_left_max REAL,
                tolerance REAL,
                measurement_uncertainty REAL,
                result TEXT,
                certificate_number TEXT,
                certificate_path TEXT,
                next_calibration_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (equipment_id) REFERENCES spc_equipment_registry(id)
            )
        """)

        # SPC Gage R&R Studies
        db.execute("""
            CREATE TABLE IF NOT EXISTS spc_gage_rr_studies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_number TEXT UNIQUE NOT NULL,
                gage_id INTEGER NOT NULL,
                study_type TEXT DEFAULT 'GAGE_RR',
                part_count INTEGER NOT NULL,
                operator_count INTEGER NOT NULL,
                replicate_count INTEGER DEFAULT 2,
                part_numbers TEXT NOT NULL,
                operator_numbers TEXT NOT NULL,
                measurements TEXT NOT NULL,
                part_variation REAL,
                repeatability_ev REAL,
                reproducibility_av REAL,
                grr REAL,
                part_variation_pv REAL,
                tolerance_tv REAL,
                ndch REAL,
                percent_study_variation REAL,
                percent_tolerance REAL,
                assessment TEXT,
                study_date TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (gage_id) REFERENCES spc_equipment_registry(id)
            )
        """)

        # Seed default control chart types
        _seed_spc_defaults(db)

    return True


def _seed_spc_defaults(db):
    """Seed default SPC configuration data."""

    # Control Chart Types
    chart_types = [
        ('XBAR_R', 'X-bar and R Chart', 'XBAR_R', 'Variables chart for subgroup size 2-10'),
        ('XBAR_S', 'X-bar and S Chart', 'XBAR_S', 'Variables chart for subgroup size >10'),
        ('I_MR', 'Individual-Moving Range', 'I_MR', 'For individual measurements'),
        ('X_MR', 'X-Moving Range (same as I-MR)', 'I_MR', 'For individual measurements'),
        ('C', 'C Chart', 'C', 'Count of defects'),
        ('P', 'P Chart', 'P', 'Proportion defective'),
        ('NP', 'NP Chart', 'NP', 'Number of defective'),
        ('U', 'U Chart', 'U', 'Defects per unit'),
    ]

    for code, name, chart_type, desc in chart_types:
        db.execute("""
            INSERT OR IGNORE INTO spc_control_charts (chart_code, chart_name, chart_type, description)
            VALUES (?, ?, ?, ?)
        """, (code, name, chart_type, desc))

    # Western Electric Rules
    we_rules = [
        ('WE1', 'Rule 1 - Outside Limits',
         'Any single point outside 3σ control limits (Zone A)',
         'Zone A', None, None, 'OUTSIDE_LIMITS', 'CRITICAL', 1),
        ('WE2A', 'Rule 2a - Zone A Violation',
         '2 of 3 consecutive points in Zone A (beyond 2σ)',
         None, 'Zone A', None, 'ZONE_A_VIOLATION', 'MAJOR', 2),
        ('WE2B', 'Rule 2b - Zone A Violation',
         '4 of 5 consecutive points in Zone B (beyond 1σ)',
         None, 'Zone B', None, 'ZONE_B_VIOLATION', 'MAJOR', 3),
        ('WE3', 'Rule 3 - Zone B/C Violation',
         '8 consecutive points in Zone B or beyond (on one side of center)',
         None, None, 'Zone B', 'ONE_SIDE_VIOLATION', 'MINOR', 4),
        ('WE4', 'Rule 4 - Trend Violation',
         '6 consecutive points steadily increasing or decreasing',
         None, None, None, 'TREND_VIOLATION', 'MINOR', 5),
        ('WE5', 'Rule 5 - Stratification',
         '15 consecutive points in Zone C (center third)',
         None, None, 'Zone C', 'STRATIFICATION', 'WARNING', 6),
        ('WE6', 'Rule 6 - Mixture',
         '8 consecutive points with none in Zone C',
         None, None, 'MIXTURE', 'MIXTURE', 'WARNING', 7),
        ('WE7', 'Rule 7 - Systematic Pattern',
         '14 alternating up and down',
         None, None, 'SYSTEMATIC', 'SYSTEMATIC', 'WARNING', 8),
    ]

    for code, name, desc, zone_a, zone_b, zone_c, pattern, severity, weight in we_rules:
        db.execute("""
            INSERT OR IGNORE INTO spc_western_electric_rules
            (rule_code, rule_name, rule_description, zone_a_violation, zone_b_violation,
             zone_c_violation, pattern_violation, severity_weight, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (code, name, desc, zone_a, zone_b, zone_c, pattern, weight))

    # AQL Levels (ANSI/ASQ Z1.4 / ISO 2859-1)
    aql_levels = [
        (2, 8, 'G', 'G', 'G', 'H', 'J', 'K', 'L', 'N', 'P', 'Q', 'R'),
        (9, 15, 'G', 'G', 'H', 'J', 'K', 'L', 'N', 'P', 'Q', 'R', 'S'),
        (16, 25, 'H', 'J', 'K', 'L', 'N', 'P', 'Q', 'R', 'S', 'T', 'U'),
        (26, 50, 'J', 'K', 'L', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'X'),
        (51, 90, 'K', 'L', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'X', 'Y'),
        (91, 150, 'L', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'X', 'Y', 'Z'),
        (151, 280, 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'X', 'Y', 'Z', 'Z'),
        (281, 500, 'P', 'Q', 'R', 'S', 'T', 'U', 'X', 'Y', 'Z', 'Z', 'Z'),
        (501, 1200, 'Q', 'R', 'S', 'T', 'U', 'X', 'Y', 'Z', 'Z', 'Z', 'Z'),
        (1201, 3200, 'R', 'S', 'T', 'U', 'X', 'Y', 'Z', 'Z', 'Z', 'Z', 'Z'),
        (3201, 10000, 'S', 'T', 'U', 'X', 'Y', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'),
        (10001, 35000, 'T', 'U', 'X', 'Y', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'),
        (35001, 150000, 'U', 'X', 'Y', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'),
        (150001, 500000, 'X', 'Y', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'),
        (500001, 999999999, 'Y', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z', 'Z'),
    ]

    for row in aql_levels:
        db.execute("""
            INSERT OR IGNORE INTO spc_aql_levels
            (lot_size_min, lot_size_max, aql_010_code, aql_015_code, aql_025_code,
             aql_040_code, aql_065_code, aql_100_code, aql_150_code, aql_250_code,
             aql_400_code, aql_650_code, aql_1000_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)


# ============================================================================
# SPC CALCULATION ENGINE
# ============================================================================

class SPCCalculator:
    """Statistical Process Control calculation engine."""

    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """Calculate arithmetic mean."""
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def calculate_std_dev(values: List[float], mean: float = None) -> float:
        """Calculate standard deviation (sample)."""
        if len(values) < 2:
            return 0.0
        if mean is None:
            mean = SPCCalculator.calculate_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)

    @staticmethod
    def calculate_range(values: List[float]) -> float:
        """Calculate range (max - min)."""
        if not values:
            return 0.0
        return max(values) - min(values)

    @staticmethod
    def calculate_moving_range(values: List[float]) -> List[float]:
        """Calculate moving range values."""
        if len(values) < 2:
            return []
        return [abs(values[i] - values[i-1]) for i in range(1, len(values))]

    @staticmethod
    def calculate_xbar_r_control_limits(
        grand_mean: float,
        r_bar: float,
        subgroup_size: int
    ) -> Dict[str, float]:
        """Calculate X-bar R chart control limits using standard factors."""
        factors = {
            2: {'A2': 1.880, 'D3': 0, 'D4': 3.267},
            3: {'A2': 1.023, 'D3': 0, 'D4': 2.574},
            4: {'A2': 0.729, 'D3': 0, 'D4': 2.282},
            5: {'A2': 0.577, 'D3': 0, 'D4': 2.114},
            6: {'A2': 0.483, 'D3': 0, 'D4': 2.004},
            7: {'A2': 0.419, 'D3': 0.076, 'D4': 1.924},
            8: {'A2': 0.373, 'D3': 0.136, 'D4': 1.864},
            9: {'A2': 0.337, 'D3': 0.184, 'D4': 1.816},
            10: {'A2': 0.308, 'D3': 0.223, 'D4': 1.777},
        }
        f = factors.get(subgroup_size, {'A2': 0, 'D3': 0, 'D4': 2.5})

        ucl_x = grand_mean + f['A2'] * r_bar
        lcl_x = grand_mean - f['A2'] * r_bar
        ucl_r = f['D4'] * r_bar
        lcl_r = max(0, f['D3'] * r_bar)

        return {
            'x_ucl': ucl_x,
            'x_lcl': lcl_x,
            'x_cl': grand_mean,
            'r_ucl': ucl_r,
            'r_lcl': lcl_r,
            'r_bar': r_bar,
            'grand_mean': grand_mean
        }

    @staticmethod
    def calculate_xbar_s_control_limits(
        grand_mean: float,
        s_bar: float,
        subgroup_size: int
    ) -> Dict[str, float]:
        """Calculate X-bar S chart control limits using standard factors."""
        c4_factors = {
            2: 0.7979, 3: 0.8862, 4: 0.9213, 5: 0.9400,
            6: 0.9515, 7: 0.9594, 8: 0.9650, 9: 0.9693,
            10: 0.9727, 11: 0.9754, 12: 0.9776, 15: 0.9823,
            20: 0.9869, 25: 0.9896, 30: 0.9914
        }
        c4 = c4_factors.get(subgroup_size, 0.94)

        # B3 and B4 factors for S chart
        b3_factors = {
            2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.076, 8: 0.136,
            9: 0.184, 10: 0.223, 11: 0.256, 12: 0.283,
            15: 0.348, 20: 0.387, 25: 0.404, 30: 0.414
        }
        b4_factors = {
            2: 3.267, 3: 2.568, 4: 2.266, 5: 2.089, 6: 1.970,
            7: 1.882, 8: 1.815, 9: 1.761, 10: 1.717,
            11: 1.680, 12: 1.646, 15: 1.564, 20: 1.485,
            25: 1.435, 30: 1.395
        }
        b3 = b3_factors.get(subgroup_size, 0)
        b4 = b4_factors.get(subgroup_size, 1.5)

        ucl_x = grand_mean + (3 / (c4 * math.sqrt(subgroup_size))) * s_bar
        lcl_x = grand_mean - (3 / (c4 * math.sqrt(subgroup_size))) * s_bar
        ucl_s = b4 * s_bar
        lcl_s = max(0, b3 * s_bar)

        return {
            'x_ucl': ucl_x,
            'x_lcl': lcl_x,
            'x_cl': grand_mean,
            's_ucl': ucl_s,
            's_lcl': lcl_s,
            's_bar': s_bar,
            'grand_mean': grand_mean
        }

    @staticmethod
    def calculate_imr_control_limits(values: List[float]) -> Dict[str, float]:
        """Calculate I-MR (Individual-Moving Range) control limits."""
        mean = SPCCalculator.calculate_mean(values)
        mr_values = SPCCalculator.calculate_moving_range(values)
        mr_bar = SPCCalculator.calculate_mean(mr_values) if mr_values else 0

        # Standard factors for I-MR chart
        d2 = 1.128  # for n=2 (moving range of 2)
        D3 = 0
        D4 = 3.267

        ucl_i = mean + 3 * (mr_bar / d2)
        lcl_i = mean - 3 * (mr_bar / d2)
        ucl_mr = D4 * mr_bar
        lcl_mr = 0

        return {
            'i_ucl': ucl_i,
            'i_lcl': lcl_i,
            'i_cl': mean,
            'mr_ucl': ucl_mr,
            'mr_lcl': lcl_mr,
            'mr_bar': mr_bar,
            'mean': mean
        }

    @staticmethod
    def calculate_c_chart_limits(
        defect_count_total: int,
        k: int
    ) -> Dict[str, float]:
        """Calculate C chart limits (count of defects)."""
        c_bar = defect_count_total / k if k > 0 else 0

        ucl = c_bar + 3 * math.sqrt(c_bar)
        lcl = max(0, c_bar - 3 * math.sqrt(c_bar))

        return {
            'c_ucl': ucl,
            'c_lcl': lcl,
            'c_bar': c_bar
        }

    @staticmethod
    def calculate_p_chart_limits(
        defectives_total: int,
        sample_size_total: int,
        k: int
    ) -> Dict[str, float]:
        """Calculate P chart limits (proportion defective)."""
        p_bar = defectives_total / sample_size_total if sample_size_total > 0 else 0

        ucl = p_bar + 3 * math.sqrt(p_bar * (1 - p_bar) / sample_size_total)
        lcl = max(0, p_bar - 3 * math.sqrt(p_bar * (1 - p_bar) / sample_size_total))

        return {
            'p_ucl': ucl,
            'p_lcl': lcl,
            'p_bar': p_bar
        }

    @staticmethod
    def calculate_u_chart_limits(
        defect_count_total: int,
        sample_size_total: int,
        k: int
    ) -> Dict[str, float]:
        """Calculate U chart limits (defects per unit)."""
        u_bar = defect_count_total / sample_size_total if sample_size_total > 0 else 0

        ucl = u_bar + 3 * math.sqrt(u_bar / sample_size_total)
        lcl = max(0, u_bar - 3 * math.sqrt(u_bar / sample_size_total))

        return {
            'u_ucl': ucl,
            'u_lcl': lcl,
            'u_bar': u_bar
        }

    @staticmethod
    def calculate_np_chart_limits(
        defectives_total: int,
        sample_size_total: int,
        k: int
    ) -> Dict[str, float]:
        """Calculate NP chart limits (number of defective)."""
        n = sample_size_total / k if k > 0 else 1
        p_bar = defectives_total / sample_size_total if sample_size_total > 0 else 0
        np_bar = n * p_bar

        ucl = np_bar + 3 * math.sqrt(n * p_bar * (1 - p_bar))
        lcl = max(0, np_bar - 3 * math.sqrt(n * p_bar * (1 - p_bar)))

        return {
            'np_ucl': ucl,
            'np_lcl': lcl,
            'np_bar': np_bar,
            'n': n
        }

    @staticmethod
    def calculate_u_chart_limits(
        defect_count_total: int,
        sample_size_total: int,
        k: int
    ) -> Dict[str, float]:
        """Calculate U chart limits (defects per unit)."""
        u_bar = defect_count_total / sample_size_total if sample_size_total > 0 else 0

        ucl = u_bar + 3 * math.sqrt(u_bar / sample_size_total)
        lcl = max(0, u_bar - 3 * math.sqrt(u_bar / sample_size_total))

        return {
            'u_ucl': ucl,
            'u_lcl': lcl,
            'u_bar': u_bar
        }

    @staticmethod
    def calculate_r_chart_limits(
        r_bar: float,
        subgroup_size: int
    ) -> Dict[str, float]:
        """Calculate R chart limits."""
        factors = {
            2: {'D3': 0, 'D4': 3.267},
            3: {'D3': 0, 'D4': 2.574},
            4: {'D3': 0, 'D4': 2.282},
            5: {'D3': 0, 'D4': 2.114},
            6: {'D3': 0, 'D4': 2.004},
            7: {'D3': 0.076, 'D4': 1.924},
            8: {'D3': 0.136, 'D4': 1.864},
            9: {'D3': 0.184, 'D4': 1.816},
            10: {'D3': 0.223, 'D4': 1.777},
        }
        f = factors.get(subgroup_size, {'D3': 0, 'D4': 2.5})

        ucl_r = f['D4'] * r_bar
        lcl_r = max(0, f['D3'] * r_bar)

        return {
            'r_ucl': ucl_r,
            'r_lcl': lcl_r,
            'r_bar': r_bar
        }

    @staticmethod
    def calculate_s_chart_limits(
        s_bar: float,
        subgroup_size: int
    ) -> Dict[str, float]:
        """Calculate S chart limits."""
        b3_factors = {
            2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0.076, 8: 0.136,
            9: 0.184, 10: 0.223, 11: 0.256, 12: 0.283,
            15: 0.348, 20: 0.387, 25: 0.404, 30: 0.414
        }
        b4_factors = {
            2: 3.267, 3: 2.568, 4: 2.266, 5: 2.089, 6: 1.970,
            7: 1.882, 8: 1.815, 9: 1.761, 10: 1.717,
            11: 1.680, 12: 1.646, 15: 1.564, 20: 1.485,
            25: 1.435, 30: 1.395
        }
        b3 = b3_factors.get(subgroup_size, 0)
        b4 = b4_factors.get(subgroup_size, 1.5)

        ucl_s = b4 * s_bar
        lcl_s = max(0, b3 * s_bar)

        return {
            's_ucl': ucl_s,
            's_lcl': lcl_s,
            's_bar': s_bar
        }

    @staticmethod
    def calculate_cpk_from_data(values: List[float], usl: float, lsl: float, target: float = None) -> Dict[str, float]:
        """Calculate Cp and Cpk from raw data values."""
        if not values or len(values) < 2:
            return {'cp': 0, 'cpk': 0, 'cpu': 0, 'cpl': 0, 'mean': 0, 'std_dev': 0}

        mean = sum(values) / len(values)
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in values) / (len(values) - 1))

        if std_dev > 0:
            cpu = (usl - mean) / (3 * std_dev)
            cpl = (mean - lsl) / (3 * std_dev)
            cp = (usl - lsl) / (6 * std_dev)
            cpk = min(cpu, cpl)
        else:
            cpu = cpl = cp = cpk = float('inf')

        return {
            'mean': mean,
            'std_dev': std_dev,
            'cp': cp,
            'cpk': cpk,
            'cpu': cpu,
            'cpl': cpl,
            'target': target
        }

    @staticmethod
    def check_western_electric_rules(
        values: List[float],
        mean: float,
        std_dev: float,
        limits: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Check Western Electric rules for out-of-control signals."""
        violations = []

        if len(values) < 5:
            return violations

        if std_dev <= 0:
            return violations

        zone_a_upper = mean + 3 * std_dev
        zone_a_lower = mean - 3 * std_dev
        zone_b_upper = mean + 2 * std_dev
        zone_b_lower = mean - 2 * std_dev
        zone_c_upper = mean + 1 * std_dev
        zone_c_lower = mean - 1 * std_dev

        def in_zone_a(val):
            return val > zone_a_upper or val < zone_a_lower

        def in_zone_b(val):
            return (val > zone_b_upper and val <= zone_a_upper) or (val >= zone_a_lower and val < zone_b_lower)

        def in_zone_c(val):
            return (val > zone_c_upper and val <= zone_b_upper) or (val >= zone_b_lower and val < zone_c_lower)

        # Rule 1: Any single point outside 3σ limits (Zone A)
        for i, val in enumerate(values):
            if in_zone_a(val):
                violations.append({
                    'rule': 'WE1',
                    'description': 'Point outside 3σ control limits',
                    'index': i,
                    'value': val,
                    'severity': 'CRITICAL',
                    'zone': 'A'
                })

        # Rule 2a: 2 of 3 consecutive points in Zone A (beyond 2σ on same side)
        for i in range(len(values) - 2):
            window = values[i:i+3]
            if sum(1 for v in window if in_zone_a(v)) >= 2:
                violations.append({
                    'rule': 'WE2A',
                    'description': '2 of 3 consecutive points in Zone A',
                    'index': i + 2,
                    'values': window,
                    'severity': 'MAJOR',
                    'zone': 'A'
                })

        # Rule 2b: 4 of 5 consecutive points in Zone B (beyond 1σ on same side)
        for i in range(len(values) - 4):
            window = values[i:i+5]
            if sum(1 for v in window if in_zone_b(v)) >= 4:
                violations.append({
                    'rule': 'WE2B',
                    'description': '4 of 5 consecutive points in Zone B',
                    'index': i + 4,
                    'values': window,
                    'severity': 'MAJOR',
                    'zone': 'B'
                })

        # Rule 3: 8 consecutive points on one side of center line
        for i in range(len(values) - 7):
            window = values[i:i+8]
            if all(v > mean for v in window) or all(v < mean for v in window):
                violations.append({
                    'rule': 'WE3',
                    'description': '8 consecutive points on one side of center',
                    'index': i + 7,
                    'values': window,
                    'severity': 'MINOR',
                    'zone': 'CENTER'
                })

        # Rule 4: 6 consecutive points steadily increasing or decreasing
        for i in range(len(values) - 5):
            window = values[i:i+6]
            diffs = [window[j+1] - window[j] for j in range(5)]
            if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
                violations.append({
                    'rule': 'WE4',
                    'description': '6 consecutive points with sustained trend',
                    'index': i + 5,
                    'values': window,
                    'severity': 'MINOR',
                    'zone': 'TREND'
                })

        # Rule 5: 15 consecutive points in Zone C (center third)
        for i in range(len(values) - 14):
            window = values[i:i+15]
            if sum(1 for v in window if in_zone_c(v)) >= 15:
                violations.append({
                    'rule': 'WE5',
                    'description': '15 consecutive points in Zone C (stratification)',
                    'index': i + 14,
                    'values': window,
                    'severity': 'WARNING',
                    'zone': 'C'
                })

        # Rule 6: 8 consecutive points with none in Zone C (mixture pattern)
        for i in range(len(values) - 7):
            window = values[i:i+8]
            if sum(1 for v in window if in_zone_c(v)) == 0:
                violations.append({
                    'rule': 'WE6',
                    'description': '8 consecutive points with none in Zone C (mixture)',
                    'index': i + 7,
                    'values': window,
                    'severity': 'WARNING',
                    'zone': 'OUTER'
                })

        # Rule 7: 14 alternating up and down (systematic pattern)
        for i in range(len(values) - 13):
            window = values[i:i+14]
            alternating = True
            for j in range(12):
                if (window[j+1] - window[j]) * (window[j+2] - window[j+1]) >= 0:
                    alternating = False
                    break
            if alternating:
                violations.append({
                    'rule': 'WE7',
                    'description': '14 alternating points (systematic pattern)',
                    'index': i + 13,
                    'values': window,
                    'severity': 'WARNING',
                    'zone': 'ALTERNATING'
                })

        # Rule 8: 8 points in a row beyond 1σ (same side)
        for i in range(len(values) - 7):
            window = values[i:i+8]
            if all(v > zone_c_upper for v in window) or all(v < zone_c_lower for v in window):
                violations.append({
                    'rule': 'WE8',
                    'description': '8 points in a row beyond 1σ',
                    'index': i + 7,
                    'values': window,
                    'severity': 'WARNING',
                    'zone': 'OUTSIDE_C'
                })

        return violations


class CapabilityCalculator:
    """Process capability calculation engine."""

    @staticmethod
    def calculate_capability(
        values: List[float],
        usl: float,
        lsl: float,
        target: float = None
    ) -> Dict[str, float]:
        """
        Calculate process capability indices.
        Uses within-subgroup variation (s) for Cp/Cpk
        and overall variation (σ) for Pp/Ppk.
        """
        if not values:
            return {}

        mean = sum(values) / len(values)
        n = len(values)

        # Sample standard deviation (within-subgroup estimate)
        s = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))

        # Population standard deviation (overall variation)
        sigma = math.sqrt(sum((x - mean) ** 2 for x in values) / n)

        # Calculate 6σ spread
        spread_6s = 6 * s
        spread_6sigma = 6 * sigma

        # Cp and Cpk
        if s > 0:
            cp = (usl - lsl) / spread_6s
            cpu = (usl - mean) / (3 * s)
            cpl = (mean - lsl) / (3 * s)
            cpk = min(cpu, cpl)
        else:
            cp = cpk = cpu = cpl = float('inf')

        # Pp and Ppk
        if sigma > 0:
            pp = (usl - lsl) / spread_6sigma
            ppu = (usl - mean) / (3 * sigma)
            ppl = (mean - lsl) / (3 * sigma)
            ppk = min(ppu, ppl)
        else:
            pp = ppk = ppu = ppl = float('inf')

        # PPM (Parts Per Million) defective
        # Using normal distribution approximation - enhanced with error function approximation
        try:
            from scipy.stats import norm
            z_upper = (usl - mean) / sigma if sigma > 0 else 0
            z_lower = (lsl - mean) / sigma if sigma > 0 else 0
            ppm_upper = (1 - norm.cdf(z_upper)) * 1000000
            ppm_lower = norm.cdf(z_lower) * 1000000
            total_ppm = ppm_upper + ppm_lower
        except ImportError:
            # Enhanced fallback using error function approximation (Abramowitz and Stegun)
            def erf_approx(x):
                # Approximation of error function
                if x < 0:
                    return -erf_approx(-x)
                a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
                p = 0.3275911
                t = 1.0 / (1.0 + p * x)
                y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
                return y

            def norm_cdf_approx(z):
                return 0.5 * (1 + erf_approx(z / math.sqrt(2)))

            z_upper = (usl - mean) / sigma if sigma > 0 else 0
            z_lower = (lsl - mean) / sigma if sigma > 0 else 0
            ppm_upper = (1 - norm_cdf_approx(z_upper)) * 1000000
            ppm_lower = norm_cdf_approx(z_lower) * 1000000
            total_ppm = ppm_upper + ppm_lower

        # Sigma level (defects per million opportunities / 3.4)
        sigma_level = 0
        if total_ppm > 0:
            sigma_level = 0.8406 + math.sqrt(
                (27.6337 + 23.7669 * math.log(total_ppm, 10))
            ) if total_ppm > 0 else 6

        # Target offset (Cpm - Taguchi capability)
        if target is not None and s > 0:
            cpm = (usl - lsl) / (6 * math.sqrt(s**2 + (mean - target)**2))
        else:
            cpm = cp

        return {
            'mean': mean,
            'std_dev': s,
            'std_dev_overall': sigma,
            'cp': cp,
            'cpk': cpk,
            'cpu': cpu,
            'cpl': cpl,
            'pp': pp,
            'ppk': ppk,
            'ppu': ppu,
            'ppl': ppl,
            'cpm': cpm,
            'ppmm': total_ppm,
            'sigma_level': sigma_level,
            'usl': usl,
            'lsl': lsl,
            'target': target,
            'assessment': CapabilityCalculator._assess_capability(cpk)
        }

    @staticmethod
    def _assess_capability(cpk: float) -> str:
        """Assess process capability based on Cpk value."""
        if cpk >= 2.0:
            return 'WORLD_CLASS'
        elif cpk >= 1.67:
            return 'EXCELLENT'
        elif cpk >= 1.33:
            return 'GOOD'
        elif cpk >= 1.0:
            return 'ACCEPTABLE'
        elif cpk >= 0.67:
            return 'MARGINAL'
        else:
            return 'NOT_CAPABLE'


class SamplingPlanCalculator:
    """AQL-based sampling plan calculations (ANSI/ASQ Z1.4 / ISO 2859)."""

    # Standard AQL values
    AQL_VALUES = [0.010, 0.015, 0.025, 0.040, 0.065, 0.100, 0.150, 0.250, 0.400, 0.650, 1.0]

    # Sample size code letters
    SAMPLE_SIZE_CODES = {
        (2, 8): 'G', (9, 15): 'H', (16, 25): 'J', (26, 50): 'K',
        (51, 90): 'L', (91, 150): 'M', (151, 280): 'N', (281, 500): 'P',
        (501, 1200): 'Q', (1201, 3200): 'R', (3201, 10000): 'S',
        (10001, 35000): 'T', (35001, 150000): 'U', (150001, 500000): 'V',
        (500001, float('inf')): 'X'
    }

    @staticmethod
    def get_sample_size_code(lot_size: int) -> str:
        """Get sample size code letter based on lot size."""
        for (min_size, max_size), code in SamplingPlanCalculator.SAMPLE_SIZE_CODES.items():
            if min_size <= lot_size <= max_size:
                return code
        return 'X'

    @staticmethod
    def calculate_sample_size(lot_size: int, aql: float, inspection_level: str = 'II') -> Dict[str, Any]:
        """
        Calculate sample size and acceptance/rejection numbers.
        Based on ANSI/ASQ Z1.4 and ISO 2859-1.
        """
        sample_code = SamplingPlanCalculator.get_sample_size_code(lot_size)

        # Sample size by code (simplified)
        sample_sizes = {
            'A': 2, 'B': 3, 'C': 5, 'D': 8, 'E': 13, 'F': 20,
            'G': 32, 'H': 50, 'J': 80, 'K': 125, 'L': 200,
            'M': 315, 'N': 500, 'P': 800, 'Q': 1250, 'R': 2000,
            'S': 3150, 'T': 5000, 'U': 8000, 'V': 12500, 'X': 20000
        }

        n = sample_sizes.get(sample_code, 32)

        # Acceptance constants for normal inspection (simplified table)
        # These would normally come from the full ANSI/ASQ Z1.4 tables
        acceptance_table = {
            0.010: {'Ac': 0, 'Re': 1},
            0.015: {'Ac': 0, 'Re': 1},
            0.025: {'Ac': 0, 'Re': 1},
            0.040: {'Ac': 0, 'Re': 1},
            0.065: {'Ac': 0, 'Re': 1},
            0.100: {'Ac': 1, 'Re': 2},
            0.150: {'Ac': 1, 'Re': 2},
            0.250: {'Ac': 2, 'Re': 3},
            0.400: {'Ac': 3, 'Re': 4},
            0.650: {'Ac': 5, 'Re': 6},
            1.000: {'Ac': 7, 'Re': 8},
        }

        acceptance = acceptance_table.get(aql, {'Ac': 1, 'Re': 2})

        return {
            'sample_code': sample_code,
            'sample_size': n,
            'acceptance_number': acceptance['Ac'],
            'rejection_number': acceptance['Re'],
            'aql': aql,
            'lot_size': lot_size,
            'inspection_level': inspection_level
        }

    @staticmethod
    def evaluate_lot(
        lot_size: int,
        defects_found: int,
        aql: float = 1.0
    ) -> Dict[str, Any]:
        """
        Evaluate a lot based on sampling plan.
        Returns accept/reject decision with details.
        """
        plan = SamplingPlanCalculator.calculate_sample_size(lot_size, aql)

        accepted = defects_found <= plan['acceptance_number']
        rejected = defects_found >= plan['rejection_number']

        decision = 'ACCEPT' if accepted else ('REJECT' if rejected else 'SAMPLE')

        return {
            'decision': decision,
            'lot_size': lot_size,
            'sample_size': plan['sample_size'],
            'defects_found': defects_found,
            'acceptance_number': plan['acceptance_number'],
            'rejection_number': plan['rejection_number'],
            'aql': aql,
            'percent_defective': (defects_found / lot_size * 100) if lot_size > 0 else 0
        }


# ============================================================================
# DATA ACCESS FUNCTIONS
# ============================================================================

def add_spc_measurement(
    chart_id: int,
    chart_code: str,
    measurement_group: str,
    sample_values: List[float],
    measurement_date: str,
    recorded_by: int = None,
    notes: str = None
) -> int:
    """Add SPC measurement data and calculate statistics."""
    conn = get_db()
    cursor = conn.cursor()

    # Calculate statistics
    mean = SPCCalculator.calculate_mean(sample_values)
    range_val = SPCCalculator.calculate_range(sample_values)
    std_dev = SPCCalculator.calculate_std_dev(sample_values, mean)

    # Check control limits based on chart type
    limits = None
    control_status = 'IN_CONTROL'

    cursor.execute("SELECT chart_type FROM spc_control_charts WHERE id = ?", (chart_id,))
    row = cursor.fetchone()
    chart_type = row['chart_type'] if row else 'I_MR'

    # Get spec limits for the chart
    cursor.execute("""
        SELECT usl, lsl, ucl, lcl FROM spc_specification_limits
        WHERE chart_id = ? AND is_active = 1
    """, (chart_id,))
    spec_row = cursor.fetchone()

    if spec_row:
        usl = spec_row['usl']
        lsl = spec_row['lsl']

        # Check if out of spec limits (not just control limits)
        for val in sample_values:
            if (usl and val > usl) or (lsl and val < lsl):
                control_status = 'OUT_OF_SPEC'
                break

        # If not out of spec, check control limits
        if control_status == 'IN_CONTROL':
            if chart_type == 'I_MR':
                # Get historical data for control limits
                cursor.execute("""
                    SELECT average FROM spc_measurement_data
                    WHERE chart_id = ? ORDER BY measurement_date DESC LIMIT 20
                """, (chart_id,))
                history = [r['average'] for r in cursor.fetchall()]

                if len(history) >= 5:
                    all_values = history + [mean]
                    limits = SPCCalculator.calculate_imr_control_limits(all_values)

                    if mean > limits['i_ucl'] or mean < limits['i_lcl']:
                        control_status = 'OUT_OF_CONTROL'

    cursor.execute("""
        INSERT INTO spc_measurement_data
        (chart_id, chart_code, measurement_group, sample_size, sample_values,
         average, range_val, std_dev, measurement_date, recorded_by, notes, control_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        chart_id, chart_code, measurement_group, len(sample_values),
        ','.join(map(str, sample_values)), mean, range_val, std_dev,
        measurement_date, recorded_by, notes, control_status
    ))

    measurement_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Create anomaly alert if out of control
    if control_status != 'IN_CONTROL':
        create_spc_alert(
            chart_id=chart_id,
            measurement_id=measurement_id,
            measurement_group=measurement_group,
            rule_violated='OUT_OF_SPEC' if control_status == 'OUT_OF_SPEC' else 'OUT_OF_CONTROL',
            rule_description=f'Measurement {control_status}: Mean={mean:.4f}',
            severity='HIGH'
        )

    return measurement_id


def create_spc_alert(
    chart_id: int,
    measurement_id: int,
    measurement_group: str,
    rule_violated: str,
    rule_description: str,
    severity: str = 'WARNING'
) -> int:
    """Create an SPC anomaly alert."""
    conn = get_db()
    cursor = conn.cursor()

    # Generate alert number
    cursor.execute("SELECT COUNT(*) as cnt FROM spc_anomaly_alerts")
    count = cursor.fetchone()['cnt'] + 1
    alert_number = f"SPAlert-{datetime.now().strftime('%Y%m%d')}-{count:04d}"

    cursor.execute("""
        INSERT INTO spc_anomaly_alerts
        (alert_number, chart_id, measurement_id, measurement_group,
         rule_violated, rule_description, severity, detected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (alert_number, chart_id, measurement_id, measurement_group,
          rule_violated, rule_description, severity))

    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Send Flow notification
    try:
        from quality_routes import send_quality_notification
        send_quality_notification(
            notification_type='SPC_ALERT',
            title=f'SPC Alert: {rule_violated}',
            message=f'{rule_description} in {measurement_group}',
            severity=severity,
            related_id=alert_id,
            related_type='spc_alert'
        )
    except Exception as e:
        print(f"Error sending SPC alert notification: {e}")

    return alert_id


def create_capability_study(
    study_name: str,
    characteristic_id: int,
    process_name: str,
    sample_data: List[float],
    usl: float,
    lsl: float,
    target: float,
    study_date: str,
    study_type: str = 'INITIAL',
    notes: str = None,
    created_by: int = None
) -> Tuple[int, Dict[str, float]]:
    """
    Create a process capability study.
    Returns (study_id, capability_metrics)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Calculate capability
    capability = CapabilityCalculator.calculate_capability(sample_data, usl, lsl, target)

    # Generate study number
    cursor.execute("SELECT COUNT(*) as cnt FROM spc_capability_studies")
    count = cursor.fetchone()['cnt'] + 1
    study_number = f"CAP-{datetime.now().strftime('%Y%m%d')}-{count:04d}"

    cursor.execute("""
        INSERT INTO spc_capability_studies
        (study_number, study_name, characteristic_id, process_name,
         sample_size, sample_data, mean, std_dev, cp, cpk, pp, ppk, ppmm,
         sigma_level, assessment, study_date, study_type, notes,
         created_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED')
    """, (
        study_number, study_name, characteristic_id, process_name,
        len(sample_data), ','.join(map(str, sample_data)),
        capability['mean'], capability['std_dev'],
        capability['cp'], capability['cpk'],
        capability['pp'], capability['ppk'], capability['ppmm'],
        capability['sigma_level'], capability['assessment'],
        study_date, study_type, notes, created_by
    ))

    study_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return study_id, capability


def get_spc_metrics_summary(
    start_date: str = None,
    end_date: str = None,
    chart_id: int = None
) -> Dict[str, Any]:
    """Get comprehensive SPC metrics summary."""
    conn = get_db()
    cursor = conn.cursor()

    # Base query
    base_query = """
        FROM spc_measurement_data m
        LEFT JOIN spc_control_charts c ON m.chart_id = c.id
        WHERE 1=1
    """
    params = []

    if start_date:
        base_query += " AND m.measurement_date >= ?"
        params.append(start_date)
    if end_date:
        base_query += " AND m.measurement_date <= ?"
        params.append(end_date)
    if chart_id:
        base_query += " AND m.chart_id = ?"
        params.append(chart_id)

    # Get overall statistics
    cursor.execute(f"""
        SELECT
            COUNT(*) as total_measurements,
            AVG(average) as overall_mean,
            SUM(CASE WHEN control_status = 'OUT_OF_CONTROL' THEN 1 ELSE 0 END) as out_of_control_count,
            SUM(CASE WHEN control_status = 'OUT_OF_SPEC' THEN 1 ELSE 0 END) as out_of_spec_count,
            MIN(measurement_date) as first_date,
            MAX(measurement_date) as last_date
        {base_query}
    """, params)

    row = cursor.fetchone()

    total = row['total_measurements'] or 0
    out_of_control = row['out_of_control_count'] or 0
    out_of_spec = row['out_of_spec_count'] or 0

    # Calculate derived metrics
    in_control_rate = ((total - out_of_control) / total * 100) if total > 0 else 100
    pass_rate = ((total - out_of_spec) / total * 100) if total > 0 else 100

    # Get defect data from quality_inspections for DPMO calculation
    cursor.execute("""
        SELECT
            COUNT(*) as total_inspected,
            SUM(quantity_failed) as total_defects
        FROM quality_inspections
        WHERE 1=1
        AND status = 'completed'
    """ + (f" AND inspection_date BETWEEN ? AND ?" if start_date and end_date else ""),
        [start_date, end_date] if start_date and end_date else [])

    insp_row = cursor.fetchone()
    total_inspected = insp_row['total_inspected'] or 1
    total_defects = insp_row['total_defects'] or 0

    # DPMO calculation
    dpmo = (total_defects / total_inspected) * 1000000 if total_inspected > 0 else 0

    # Sigma level from DPMO
    sigma_level = 0
    if dpmo > 0:
        sigma_level = 0.8406 + math.sqrt(27.6337 + 23.7669 * math.log(dpmo, 10))
    else:
        sigma_level = 6.0

    conn.close()

    return {
        'total_measurements': total,
        'out_of_control_count': out_of_control,
        'out_of_spec_count': out_of_spec,
        'in_control_rate': round(in_control_rate, 2),
        'pass_rate': round(pass_rate, 2),
        'dpmo': round(dpmo, 2),
        'sigma_level': round(sigma_level, 2),
        'first_date': row['first_date'],
        'last_date': row['last_date'],
        'total_inspected': total_inspected,
        'total_defects': total_defects
    }


def get_control_chart_data(
    chart_id: int,
    limit: int = 50,
    start_date: str = None,
    end_date: str = None
) -> List[Dict[str, Any]]:
    """Get measurement data for a control chart."""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT m.*, s.usl, s.lsl, s.target, s.ucl, s.lcl
        FROM spc_measurement_data m
        LEFT JOIN spc_specification_limits s ON m.chart_id = s.chart_id AND s.is_active = 1
        WHERE m.chart_id = ?
    """
    params = [chart_id]

    if start_date:
        query += " AND m.measurement_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND m.measurement_date <= ?"
        params.append(end_date)

    query += " ORDER BY m.measurement_date ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_open_spc_alerts(status: str = 'OPEN') -> List[Dict[str, Any]]:
    """Get open SPC anomaly alerts."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.*, c.chart_name, c.chart_code
        FROM spc_anomaly_alerts a
        LEFT JOIN spc_control_charts c ON a.chart_id = c.id
        WHERE a.status = ?
        ORDER BY a.detected_at DESC
    """, (status,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ============================================================================
# EQUIPMENT / CALIBRATION FUNCTIONS
# ============================================================================

def register_equipment(
    equipment_code: str,
    equipment_name: str,
    equipment_type: str,
    manufacturer: str = None,
    model_number: str = None,
    serial_number: str = None,
    location: str = None,
    custodian_id: int = None,
    measurement_range_min: float = None,
    measurement_range_max: float = None,
    resolution: float = None,
    accuracy: float = None,
    calibration_interval_days: int = 90
) -> int:
    """Register new measurement equipment."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO spc_equipment_registry
        (equipment_code, equipment_name, equipment_type, manufacturer, model_number,
         serial_number, location, custodian_id, measurement_range_min, measurement_range_max,
         resolution, accuracy, calibration_interval_days, next_calibration_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now', '+' || ? || ' days'))
    """, (
        equipment_code, equipment_name, equipment_type, manufacturer, model_number,
        serial_number, location, custodian_id, measurement_range_min, measurement_range_max,
        resolution, accuracy, calibration_interval_days, calibration_interval_days
    ))

    equipment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return equipment_id


def record_calibration(
    equipment_id: int,
    calibration_date: str,
    performed_by: int,
    as_found_min: float,
    as_found_max: float,
    as_left_min: float = None,
    as_left_max: float = None,
    tolerance: float = None,
    measurement_uncertainty: float = None,
    result: str = 'PASSED',
    certificate_number: str = None,
    certificate_path: str = None,
    standards_used: str = None,
    temperature: float = None,
    humidity: float = None,
    notes: str = None
) -> int:
    """Record a calibration event."""
    conn = get_db()
    cursor = conn.cursor()

    # Get equipment for next calibration date
    cursor.execute("SELECT calibration_interval_days FROM spc_equipment_registry WHERE id = ?",
                   (equipment_id,))
    row = cursor.fetchone()
    interval = row['calibration_interval_days'] if row else 90

    # Generate calibration number
    cursor.execute("SELECT COUNT(*) as cnt FROM spc_calibration_records")
    count = cursor.fetchone()['cnt'] + 1
    cal_number = f"CAL-{datetime.now().strftime('%Y%m%d')}-{count:04d}"

    next_date = f"date('{calibration_date}', '+{interval} days')"

    cursor.execute("""
        INSERT INTO spc_calibration_records
        (calibration_number, equipment_id, calibration_date, performed_by,
         standards_used, temperature, humidity, as_found_min, as_found_max,
         as_left_min, as_left_max, tolerance, measurement_uncertainty,
         result, certificate_number, certificate_path,
         next_calibration_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date(?, '+' || ? || ' days'), ?)
    """, (
        cal_number, equipment_id, calibration_date, performed_by,
        standards_used, temperature, humidity, as_found_min, as_found_max,
        as_left_min, as_left_max, tolerance, measurement_uncertainty,
        result, certificate_number, certificate_path,
        calibration_date, interval, notes
    ))

    cal_id = cursor.lastrowid

    # Update equipment status
    if result == 'PASSED':
        new_status = 'CURRENT'
    elif result == 'FAILED':
        new_status = 'CALIBRATION_HOLD'
    else:
        new_status = 'CALIBRATION_DUE'

    cursor.execute("""
        UPDATE spc_equipment_registry
        SET calibration_status = ?,
            last_calibration_date = ?,
            next_calibration_date = date(?, '+' || ? || ' days'),
            updated_at = datetime('now')
        WHERE id = ?
    """, (new_status, calibration_date, calibration_date, interval, equipment_id))

    conn.commit()
    conn.close()

    return cal_id


def perform_gage_rr_study(
    gage_id: int,
    part_numbers: List[str],
    operator_numbers: List[str],
    measurements: List[List[float]],
    study_date: str,
    study_type: str = 'GAGE_RR',
    created_by: int = None
) -> Tuple[int, Dict[str, float]]:
    """
    Perform Gage R&R study with ANOVA calculation.
    measurements: List of lists [[part1_op1_repl1, part1_op1_repl2], [part1_op2_repl1, part1_op2_repl2], ...]
    Format: measurements[part_index][operator_index * replicates + replicate_index]
    For crossed design with 2 operators and 2 replicates:
    [[op1_rep1, op1_rep2], [op2_rep1, op2_rep2], ...] per part
    """
    conn = get_db()
    cursor = conn.cursor()

    # Flatten measurements for storage
    flat_measurements = [str(m) for m in measurements]
    parts_str = ','.join(part_numbers)
    operators_str = ','.join(operator_numbers)

    # Study design
    n_parts = len(part_numbers)
    n_operators = len(operator_numbers)
    n_replicates = len(measurements[0]) // (n_parts * n_operators) if measurements else 2

    # Reorganize data for ANOVA: measurements[part][operator][replicate]
    data = []
    idx = 0
    for p in range(n_parts):
        part_data = []
        for o in range(n_operators):
            op_replicates = []
            for r in range(n_replicates):
                op_replicates.append(measurements[0][idx] if idx < len(measurements[0]) else 0)
                idx += 1
            part_data.append(op_replicates)
        data.append(part_data)

    # Calculate Grand Mean
    total_sum = 0
    total_count = 0
    for p in range(n_parts):
        for o in range(n_operators):
            for r in range(n_replicates):
                total_sum += data[p][o][r]
                total_count += 1
    grand_mean = total_sum / total_count if total_count > 0 else 0

    # Calculate factor sums for ANOVA
    part_sum = [0.0] * n_parts
    op_sum = [0.0] * n_operators
    cell_sum = [[0.0] * n_operators for _ in range(n_parts)]
    cell_count = [[0] * n_operators for _ in range(n_parts)]

    for p in range(n_parts):
        for o in range(n_operators):
            for r in range(n_replicates):
                val = data[p][o][r]
                part_sum[p] += val
                op_sum[o] += val
                cell_sum[p][o] += val
                cell_count[p][o] += 1

    # Part means
    part_means = [part_sum[p] / (n_operators * n_replicates) for p in range(n_parts)]
    op_means = [op_sum[o] / (n_parts * n_replicates) for o in range(n_operators)]
    cell_means = [[cell_sum[p][o] / cell_count[p][o] if cell_count[p][o] > 0 else 0
                   for o in range(n_operators)] for p in range(n_parts)]

    # Sum of Squares
    SS_total = sum((data[p][o][r] - grand_mean) ** 2
                  for p in range(n_parts) for o in range(n_operators) for r in range(n_replicates))

    SS_parts = sum((part_means[p] - grand_mean) ** 2 * n_operators * n_replicates
                   for p in range(n_parts))

    SS_operators = sum((op_means[o] - grand_mean) ** 2 * n_parts * n_replicates
                       for o in range(n_operators))

    SS_reproducibility = sum((cell_means[p][o] - part_means[p] - op_means[o] + grand_mean) ** 2
                             * n_replicates for p in range(n_parts) for o in range(n_operators))

    SS_repeatability = SS_total - SS_parts - SS_operators - SS_reproducibility

    # Degrees of freedom
    df_total = total_count - 1
    df_parts = n_parts - 1
    df_operators = n_operators - 1
    df_reproducibility = df_parts * df_operators
    df_repeatability = df_total - df_parts - df_operators - df_reproducibility

    # Mean Squares
    MS_parts = SS_parts / df_parts if df_parts > 0 else 0
    MS_operators = SS_operators / df_operators if df_operators > 0 else 0
    MS_reproducibility = SS_reproducibility / df_reproducibility if df_reproducibility > 0 else 0
    MS_repeatability = SS_repeatability / df_repeatability if df_repeatability > 0 else 0

    # F-statistics and variance components
    F_parts = MS_parts / MS_repeatability if MS_repeatability > 0 else 0
    F_operators = MS_operators / MS_repeatability if MS_repeatability > 0 else 0

    # Variance components
    var_repeatability = MS_repeatability
    var_reproducibility = max(0, (MS_reproducibility - MS_repeatability) / n_replicates)
    var_parts = max(0, (MS_parts - MS_repeatability) / (n_operators * n_replicates))
    var_total = var_repeatability + var_reproducibility + var_parts

    # Calculate GRR using variance components
    grr = math.sqrt(var_repeatability + var_reproducibility) * 6 if var_total > 0 else 0
    part_variation = math.sqrt(var_parts) * 6 if var_total > 0 else 0
    total_variation = math.sqrt(var_total) * 6 if var_total > 0 else 0

    # %GRR and %Tolerance
    tolerance = 10  # Default tolerance
    percent_grr = (grr / tolerance * 100) if tolerance > 0 else 0
    percent_pv = (part_variation / tolerance * 100) if tolerance > 0 else 0

    # Number of distinct categories
    ndch = 1.41 * (math.sqrt(var_parts) / math.sqrt(var_repeatability + var_reproducibility)) \
           if (var_repeatability + var_reproducibility) > 0 else 0

    # Assessment
    if percent_grr <= 10:
        assessment = 'ACCEPTABLE'
    elif percent_grr <= 30:
        assessment = 'MARGINAL'
    else:
        assessment = 'UNACCEPTABLE'

    # Generate study number
    cursor.execute("SELECT COUNT(*) as cnt FROM spc_gage_rr_studies")
    count = cursor.fetchone()['cnt'] + 1
    study_number = f"GRR-{datetime.now().strftime('%Y%m%d')}-{count:04d}"

    cursor.execute("""
        INSERT INTO spc_gage_rr_studies
        (study_number, gage_id, study_type, part_count, operator_count,
         replicate_count, part_numbers, operator_numbers, measurements,
         part_variation, repeatability_ev, reproducibility_av, grr,
         part_variation_pv, tolerance_tv, ndch, percent_study_variation,
         percent_tolerance, assessment, study_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        study_number, gage_id, study_type, n_parts, n_operators,
        n_replicates, parts_str, operators_str, ','.join(str(m) for m in flat_measurements),
        math.sqrt(var_parts), math.sqrt(var_repeatability), math.sqrt(var_reproducibility),
        grr / 6, part_variation / 6, tolerance, ndch, percent_grr,
        percent_pv, assessment, study_date, created_by
    ))

    study_id = cursor.lastrowid
    conn.commit()
    conn.close()

    metrics = {
        'study_number': study_number,
        'part_variation': math.sqrt(var_parts),
        'repeatability_ev': math.sqrt(var_repeatability),
        'reproducibility_av': math.sqrt(var_reproducibility),
        'grr': grr / 6,
        'part_variation_pv': part_variation / 6,
        'tolerance_tv': tolerance,
        'ndch': ndch,
        'percent_study_variation': percent_grr,
        'percent_tolerance': percent_pv,
        'assessment': assessment,
        'anova': {
            'SS_parts': SS_parts,
            'SS_operators': SS_operators,
            'SS_reproducibility': SS_reproducibility,
            'SS_repeatability': SS_repeatability,
            'SS_total': SS_total,
            'df_parts': df_parts,
            'df_operators': df_operators,
            'df_reproducibility': df_reproducibility,
            'df_repeatability': df_repeatability,
            'MS_parts': MS_parts,
            'MS_operators': MS_operators,
            'MS_reproducibility': MS_reproducibility,
            'MS_repeatability': MS_repeatability,
            'F_parts': F_parts,
            'F_operators': F_operators,
            'var_parts': var_parts,
            'var_reproducibility': var_reproducibility,
            'var_repeatability': var_repeatability,
            'var_total': var_total
        }
    }

    return study_id, metrics
