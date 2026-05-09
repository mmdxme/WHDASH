"""
Advanced Reporting / BI Data Models
====================================
Centralized data models for the Advanced Reporting and BI module.

This module provides:
- Reporting dataset registry and field definitions
- KPI and metric catalog management
- Saved reports and report templates
- Report scheduling and delivery engine
- Ad-hoc query builder and execution logs
- Report access and audit logging
- Drill-down configurations
- Export management and logs
- Performance monitoring and query guardrails

All BI reporting entities are managed here to ensure:
- Single source of truth for report definitions
- Centralized KPI/metric calculations
- Consistent permission and scope enforcement
- Unified audit trail

Usage:
    from bi_reporting_models import (
        ReportingDataset, ReportingKPI, SavedReport, ReportSchedule,
        AdhocQuery, ReportAccessLog, get_reporting_db
    )

Database: warehouse.db (SQLite with WAL mode)
"""

import sqlite3
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from enum import Enum

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_reporting_db():
    """Get a database connection for BI reporting operations."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def reporting_db_context():
    """Context manager for BI reporting database operations."""
    db = get_reporting_db()
    try:
        yield db
    finally:
        db.close()


def row_to_dict(row):
    """Convert sqlite3.Row to dictionary."""
    return dict(row) if row else None


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dictionaries."""
    return [dict(row) for row in rows] if rows else []


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================

class DatasetType(str, Enum):
    """Types of reporting datasets."""
    TRANSACTIONAL = "transactional"
    AGGREGATED = "aggregated"
    CUBE = "cube"
    EXTERNAL = "external"
    VIRTUAL = "virtual"


class ReportStatus(str, Enum):
    """Status of saved reports."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SHARED = "shared"


class ScheduleStatus(str, Enum):
    """Status of report schedules."""
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


class ScheduleFrequency(str, Enum):
    """Frequency options for scheduled reports."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class QueryStatus(str, Enum):
    """Status of ad-hoc queries."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Supported export formats."""
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    JSON = "json"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# DATASET REGISTRY
# =============================================================================

class ReportingDataset:
    """
    Represents a reporting dataset / data source.
    
    A dataset is a logical grouping of related fields that form the basis
    for reports and ad-hoc queries. Datasets map to actual database tables,
    views, or virtual constructs.
    """
    
    TABLE_NAME = "bi_reporting_datasets"
    
    @staticmethod
    def create_table():
        """Create the reporting datasets table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_reporting_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_code TEXT NOT NULL UNIQUE,
                    dataset_name TEXT NOT NULL,
                    description TEXT,
                    module_domain TEXT NOT NULL,
                    dataset_type TEXT DEFAULT 'transactional',
                    base_table TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_shared INTEGER DEFAULT 0,
                    allowed_roles TEXT,
                    refresh_policy TEXT DEFAULT 'manual',
                    cache_ttl_minutes INTEGER DEFAULT 60,
                    row_level_security INTEGER DEFAULT 1,
                    created_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_dataset_code ON bi_reporting_datasets(dataset_code)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_dataset_domain ON bi_reporting_datasets(module_domain)
            """)
            db.commit()
    
    @classmethod
    def create(cls, dataset_code: str, dataset_name: str, module_domain: str,
               description: str = None, base_table: str = None,
               dataset_type: str = "transactional",
               allowed_roles: List[str] = None,
               created_by_user_id: int = None) -> int:
        """Create a new reporting dataset."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_reporting_datasets 
                (dataset_code, dataset_name, description, module_domain, base_table,
                 dataset_type, allowed_roles, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_code, dataset_name, description, module_domain,
                base_table, dataset_type,
                json.dumps(allowed_roles) if allowed_roles else None,
                created_by_user_id
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_id(cls, dataset_id: int) -> Optional[Dict]:
        """Get a dataset by ID."""
        with reporting_db_context() as db:
            row = db.execute(
                "SELECT * FROM bi_reporting_datasets WHERE id = ?",
                (dataset_id,)
            ).fetchone()
            result = row_to_dict(row)
            if result and result.get('allowed_roles'):
                result['allowed_roles'] = json.loads(result['allowed_roles'])
            return result
    
    @classmethod
    def get_by_code(cls, dataset_code: str) -> Optional[Dict]:
        """Get a dataset by code."""
        with reporting_db_context() as db:
            row = db.execute(
                "SELECT * FROM bi_reporting_datasets WHERE dataset_code = ?",
                (dataset_code,)
            ).fetchone()
            result = row_to_dict(row)
            if result and result.get('allowed_roles'):
                result['allowed_roles'] = json.loads(result['allowed_roles'])
            return result
    
    @classmethod
    def get_all(cls, include_inactive: bool = False) -> List[Dict]:
        """Get all datasets."""
        with reporting_db_context() as db:
            query = "SELECT * FROM bi_reporting_datasets"
            if not include_inactive:
                query += " WHERE is_active = 1"
            query += " ORDER BY module_domain, dataset_name"
            rows = db.execute(query).fetchall()
            results = []
            for row in rows_to_list(rows):
                if row.get('allowed_roles'):
                    row['allowed_roles'] = json.loads(row['allowed_roles'])
                results.append(row)
            return results
    
    @classmethod
    def get_by_domain(cls, module_domain: str) -> List[Dict]:
        """Get datasets by module domain."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_reporting_datasets 
                WHERE module_domain = ? AND is_active = 1
                ORDER BY dataset_name
            """, (module_domain,)).fetchall()
            return rows_to_list(rows)
    
    @classmethod
    def update(cls, dataset_id: int, **kwargs) -> bool:
        """Update a dataset."""
        allowed_fields = ['dataset_name', 'description', 'base_table', 
                          'dataset_type', 'is_active', 'is_shared', 
                          'allowed_roles', 'refresh_policy', 'cache_ttl_minutes']
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                if field == 'allowed_roles':
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(kwargs[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(dataset_id)
        
        with reporting_db_context() as db:
            db.execute(
                f"UPDATE bi_reporting_datasets SET {', '.join(updates)} WHERE id = ?",
                params
            )
            db.commit()
            return True
    
    @classmethod
    def delete(cls, dataset_id: int) -> bool:
        """Delete a dataset (soft delete by setting inactive)."""
        return cls.update(dataset_id, is_active=0)


# =============================================================================
# DATASET FIELDS
# =============================================================================

class DatasetField:
    """
    Represents a field within a reporting dataset.
    
    Fields have types, aggregation compatibility, and can be marked
    as filterable, sortable, or groupable.
    """
    
    TABLE_NAME = "bi_dataset_fields"
    
    @staticmethod
    def create_table():
        """Create the dataset fields table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_dataset_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    field_code TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    description TEXT,
                    data_type TEXT NOT NULL,
                    field_category TEXT DEFAULT 'attribute',
                    is_filterable INTEGER DEFAULT 1,
                    is_sortable INTEGER DEFAULT 1,
                    is_groupable INTEGER DEFAULT 0,
                    is_aggregatable INTEGER DEFAULT 0,
                    default_aggregation TEXT,
                    available_aggregations TEXT,
                    source_column TEXT,
                    source_expression TEXT,
                    hidden INTEGER DEFAULT 0,
                    system_field INTEGER DEFAULT 0,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES bi_reporting_datasets(id) ON DELETE CASCADE,
                    UNIQUE(dataset_id, field_code)
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_field_dataset ON bi_dataset_fields(dataset_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_field_category ON bi_dataset_fields(field_category)
            """)
            db.commit()
    
    @classmethod
    def create(cls, dataset_id: int, field_code: str, field_name: str,
               data_type: str, field_category: str = "attribute",
               source_column: str = None, source_expression: str = None,
               is_filterable: bool = True, is_sortable: bool = True,
               is_groupable: bool = False, is_aggregatable: bool = False,
               default_aggregation: str = None,
               available_aggregations: List[str] = None,
               hidden: bool = False, system_field: bool = False,
               display_order: int = 0) -> int:
        """Create a new dataset field."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_dataset_fields 
                (dataset_id, field_code, field_name, data_type, field_category,
                 source_column, source_expression, is_filterable, is_sortable,
                 is_groupable, is_aggregatable, default_aggregation,
                 available_aggregations, hidden, system_field, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_id, field_code, field_name, data_type, field_category,
                source_column, source_expression,
                1 if is_filterable else 0, 1 if is_sortable else 0,
                1 if is_groupable else 0, 1 if is_aggregatable else 0,
                default_aggregation,
                json.dumps(available_aggregations) if available_aggregations else None,
                1 if hidden else 0, 1 if system_field else 0,
                display_order
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_dataset(cls, dataset_id: int, include_hidden: bool = False) -> List[Dict]:
        """Get all fields for a dataset."""
        with reporting_db_context() as db:
            query = "SELECT * FROM bi_dataset_fields WHERE dataset_id = ?"
            if not include_hidden:
                query += " AND hidden = 0"
            query += " ORDER BY field_category, display_order, field_name"
            rows = db.execute(query, (dataset_id,)).fetchall()
            results = []
            for row in rows_to_list(rows):
                if row.get('available_aggregations'):
                    row['available_aggregations'] = json.loads(row['available_aggregations'])
                results.append(row)
            return results
    
    @classmethod
    def get_field(cls, dataset_id: int, field_code: str) -> Optional[Dict]:
        """Get a specific field."""
        with reporting_db_context() as db:
            row = db.execute("""
                SELECT * FROM bi_dataset_fields 
                WHERE dataset_id = ? AND field_code = ?
            """, (dataset_id, field_code)).fetchone()
            result = row_to_dict(row)
            if result and result.get('available_aggregations'):
                result['available_aggregations'] = json.loads(result['available_aggregations'])
            return result
    
    @classmethod
    def delete_by_dataset(cls, dataset_id: int) -> bool:
        """Delete all fields for a dataset."""
        with reporting_db_context() as db:
            db.execute("DELETE FROM bi_dataset_fields WHERE dataset_id = ?", (dataset_id,))
            db.commit()
            return True


# =============================================================================
# KPI DEFINITIONS
# =============================================================================

class ReportingKPI:
    """
    Represents a KPI (Key Performance Indicator) definition.
    
    KPIs are standardized metrics that can be used across multiple reports
    and dashboards to ensure consistency.
    """
    
    TABLE_NAME = "bi_kpis"
    
    @staticmethod
    def create_table():
        """Create the KPIs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_kpis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kpi_code TEXT NOT NULL UNIQUE,
                    kpi_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    business_definition TEXT,
                    formula_description TEXT,
                    dataset_code TEXT,
                    source_query TEXT,
                    aggregation_type TEXT,
                    unit_of_measure TEXT DEFAULT 'number',
                    display_format TEXT,
                    decimal_places INTEGER DEFAULT 0,
                    target_direction TEXT DEFAULT 'higher_is_better',
                    warning_threshold REAL,
                    critical_threshold REAL,
                    owner_role TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_shared INTEGER DEFAULT 0,
                    tags TEXT,
                    created_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_kpi_code ON bi_kpis(kpi_code)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_kpi_category ON bi_kpis(category)
            """)
            db.commit()
    
    @classmethod
    def create(cls, kpi_code: str, kpi_name: str, category: str,
               description: str = None, business_definition: str = None,
               formula_description: str = None, dataset_code: str = None,
               source_query: str = None, aggregation_type: str = None,
               unit_of_measure: str = "number", display_format: str = None,
               decimal_places: int = 0, target_direction: str = "higher_is_better",
               warning_threshold: float = None, critical_threshold: float = None,
               owner_role: str = None, tags: List[str] = None,
               created_by_user_id: int = None) -> int:
        """Create a new KPI definition."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_kpis 
                (kpi_code, kpi_name, description, category, subcategory,
                 business_definition, formula_description, dataset_code, source_query,
                 aggregation_type, unit_of_measure, display_format, decimal_places,
                 target_direction, warning_threshold, critical_threshold,
                 owner_role, tags, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kpi_code, kpi_name, description, category, None,
                business_definition, formula_description, dataset_code, source_query,
                aggregation_type, unit_of_measure, display_format, decimal_places,
                target_direction, warning_threshold, critical_threshold,
                owner_role, json.dumps(tags) if tags else None,
                created_by_user_id
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_id(cls, kpi_id: int) -> Optional[Dict]:
        """Get a KPI by ID."""
        with reporting_db_context() as db:
            row = db.execute("SELECT * FROM bi_kpis WHERE id = ?", (kpi_id,)).fetchone()
            result = row_to_dict(row)
            if result and result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
    
    @classmethod
    def get_by_code(cls, kpi_code: str) -> Optional[Dict]:
        """Get a KPI by code."""
        with reporting_db_context() as db:
            row = db.execute("SELECT * FROM bi_kpis WHERE kpi_code = ?", (kpi_code,)).fetchone()
            result = row_to_dict(row)
            if result and result.get('tags'):
                result['tags'] = json.loads(result['tags'])
            return result
    
    @classmethod
    def get_all(cls, include_inactive: bool = False, category: str = None) -> List[Dict]:
        """Get all KPIs."""
        with reporting_db_context() as db:
            query = "SELECT * FROM bi_kpis"
            conditions = []
            params = []
            
            if not include_inactive:
                conditions.append("is_active = 1")
            if category:
                conditions.append("category = ?")
                params.append(category)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY category, kpi_name"
            
            rows = db.execute(query, params).fetchall()
            results = []
            for row in rows_to_list(rows):
                if row.get('tags'):
                    row['tags'] = json.loads(row['tags'])
                results.append(row)
            return results
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all unique KPI categories."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT DISTINCT category FROM bi_kpis 
                WHERE is_active = 1 
                ORDER BY category
            """).fetchall()
            return [r['category'] for r in rows]
    
    @classmethod
    def update(cls, kpi_id: int, **kwargs) -> bool:
        """Update a KPI."""
        allowed_fields = [
            'kpi_name', 'description', 'category', 'subcategory',
            'business_definition', 'formula_description', 'dataset_code',
            'source_query', 'aggregation_type', 'unit_of_measure',
            'display_format', 'decimal_places', 'target_direction',
            'warning_threshold', 'critical_threshold', 'owner_role',
            'is_active', 'is_shared', 'tags'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                if field == 'tags':
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(kwargs[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(kpi_id)
        
        with reporting_db_context() as db:
            db.execute(
                f"UPDATE bi_kpis SET {', '.join(updates)} WHERE id = ?",
                params
            )
            db.commit()
            return True


# =============================================================================
# SAVED REPORTS
# =============================================================================

class SavedReport:
    """
    Represents a saved/custom report configuration.
    
    Reports contain selected fields, filters, grouping, sorting,
    and layout configuration.
    """
    
    TABLE_NAME = "bi_saved_reports"
    
    @staticmethod
    def create_table():
        """Create the saved reports table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_saved_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_code TEXT UNIQUE,
                    report_name TEXT NOT NULL,
                    description TEXT,
                    report_type TEXT DEFAULT 'tabular',
                    dataset_id INTEGER,
                    selected_fields TEXT,
                    selected_kpis TEXT,
                    filters_config TEXT,
                    grouping_config TEXT,
                    sorting_config TEXT,
                    layout_config TEXT,
                    chart_type TEXT,
                    visualization_type TEXT,
                    status TEXT DEFAULT 'draft',
                    is_shared INTEGER DEFAULT 0,
                    is_template INTEGER DEFAULT 0,
                    parent_report_id INTEGER,
                    access_level TEXT DEFAULT 'private',
                    default_parameters TEXT,
                    row_limit INTEGER DEFAULT 1000,
                    timeout_seconds INTEGER DEFAULT 300,
                    created_by_user_id INTEGER,
                    updated_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_run_at TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    favorite INTEGER DEFAULT 0
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_report_code ON bi_saved_reports(report_code)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_report_status ON bi_saved_reports(status)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_report_owner ON bi_saved_reports(created_by_user_id)
            """)
            db.commit()
    
    @classmethod
    def create(cls, report_name: str, dataset_id: int = None,
               report_type: str = "tabular", description: str = None,
               selected_fields: List[Dict] = None, selected_kpis: List[str] = None,
               filters_config: Dict = None, grouping_config: List[str] = None,
               sorting_config: List[Dict] = None, layout_config: Dict = None,
               chart_type: str = None, visualization_type: str = None,
               status: str = "draft", is_shared: bool = False,
               is_template: bool = False, access_level: str = "private",
               default_parameters: Dict = None, row_limit: int = 1000,
               timeout_seconds: int = 300, created_by_user_id: int = None) -> int:
        """Create a new saved report."""
        report_code = f"RPT_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_saved_reports 
                (report_code, report_name, description, report_type, dataset_id,
                 selected_fields, selected_kpis, filters_config, grouping_config,
                 sorting_config, layout_config, chart_type, visualization_type,
                 status, is_shared, is_template, access_level,
                 default_parameters, row_limit, timeout_seconds,
                 created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_code, report_name, description, report_type, dataset_id,
                json.dumps(selected_fields) if selected_fields else None,
                json.dumps(selected_kpis) if selected_kpis else None,
                json.dumps(filters_config) if filters_config else None,
                json.dumps(grouping_config) if grouping_config else None,
                json.dumps(sorting_config) if sorting_config else None,
                json.dumps(layout_config) if layout_config else None,
                chart_type, visualization_type, status,
                1 if is_shared else 0, 1 if is_template else 0,
                access_level, json.dumps(default_parameters) if default_parameters else None,
                row_limit, timeout_seconds, created_by_user_id
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_id(cls, report_id: int) -> Optional[Dict]:
        """Get a report by ID."""
        return cls._get_full_report(
            "SELECT * FROM bi_saved_reports WHERE id = ?",
            (report_id,)
        )
    
    @classmethod
    def get_by_code(cls, report_code: str) -> Optional[Dict]:
        """Get a report by code."""
        return cls._get_full_report(
            "SELECT * FROM bi_saved_reports WHERE report_code = ?",
            (report_code,)
        )
    
    @classmethod
    def _get_full_report(cls, query: str, params: Tuple) -> Optional[Dict]:
        """Internal method to get a report with parsed JSON fields."""
        with reporting_db_context() as db:
            row = db.execute(query, params).fetchone()
            if not row:
                return None
            
            result = row_to_dict(row)
            json_fields = ['selected_fields', 'selected_kpis', 'filters_config',
                          'grouping_config', 'sorting_config', 'layout_config',
                          'default_parameters']
            
            for field in json_fields:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
            return result
    
    @classmethod
    def get_all(cls, user_id: int = None, status: str = None,
                dataset_id: int = None, include_shared: bool = True,
                include_templates: bool = False) -> List[Dict]:
        """Get all reports accessible to a user."""
        with reporting_db_context() as db:
            conditions = ["1=1"]
            params = []
            
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if dataset_id:
                conditions.append("dataset_id = ?")
                params.append(dataset_id)
            
            if not include_templates:
                conditions.append("is_template = 0")
            
            if user_id and not include_shared:
                conditions.append("(created_by_user_id = ? OR access_level = 'public')")
                params.append(user_id)
            elif not include_shared:
                conditions.append("created_by_user_id = ?")
                params.append(user_id)
            
            query = f"""
                SELECT * FROM bi_saved_reports 
                WHERE {' AND '.join(conditions)}
                ORDER BY updated_at DESC
            """
            rows = db.execute(query, params).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                json_fields = ['selected_fields', 'selected_kpis', 'filters_config',
                              'grouping_config', 'sorting_config', 'layout_config',
                              'default_parameters']
                for field in json_fields:
                    if row.get(field):
                        try:
                            row[field] = json.loads(row[field])
                        except:
                            pass
                results.append(row)
            return results
    
    @classmethod
    def get_my_reports(cls, user_id: int) -> List[Dict]:
        """Get reports created by a specific user."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_saved_reports 
                WHERE created_by_user_id = ? AND is_template = 0
                ORDER BY updated_at DESC
            """, (user_id,)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                json_fields = ['selected_fields', 'selected_kpis', 'filters_config',
                              'grouping_config', 'sorting_config', 'layout_config',
                              'default_parameters']
                for field in json_fields:
                    if row.get(field):
                        try:
                            row[field] = json.loads(row[field])
                        except:
                            pass
                results.append(row)
            return results
    
    @classmethod
    def get_shared_reports(cls) -> List[Dict]:
        """Get all shared reports."""
        return cls.get_all(include_shared=True)
    
    @classmethod
    def get_templates(cls) -> List[Dict]:
        """Get all report templates."""
        return cls.get_all(include_templates=True)
    
    @classmethod
    def update(cls, report_id: int, **kwargs) -> bool:
        """Update a report."""
        allowed_fields = [
            'report_name', 'description', 'report_type', 'dataset_id',
            'selected_fields', 'selected_kpis', 'filters_config',
            'grouping_config', 'sorting_config', 'layout_config',
            'chart_type', 'visualization_type', 'status', 'is_shared',
            'is_template', 'access_level', 'default_parameters',
            'row_limit', 'timeout_seconds', 'updated_by_user_id', 'favorite'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                if field in ['selected_fields', 'selected_kpis', 'filters_config',
                             'grouping_config', 'sorting_config', 'layout_config',
                             'default_parameters']:
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(kwargs[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(report_id)
        
        with reporting_db_context() as db:
            db.execute(
                f"UPDATE bi_saved_reports SET {', '.join(updates)} WHERE id = ?",
                params
            )
            db.commit()
            return True
    
    @classmethod
    def record_run(cls, report_id: int) -> bool:
        """Record that a report was run."""
        with reporting_db_context() as db:
            db.execute("""
                UPDATE bi_saved_reports 
                SET last_run_at = CURRENT_TIMESTAMP, 
                    run_count = run_count + 1 
                WHERE id = ?
            """, (report_id,))
            db.commit()
            return True
    
    @classmethod
    def delete(cls, report_id: int) -> bool:
        """Delete a report."""
        with reporting_db_context() as db:
            db.execute("DELETE FROM bi_saved_reports WHERE id = ?", (report_id,))
            db.commit()
            return True
    
    @classmethod
    def duplicate(cls, report_id: int, new_name: str = None,
                  created_by_user_id: int = None) -> Optional[int]:
        """Duplicate a report."""
        original = cls.get_by_id(report_id)
        if not original:
            return None
        
        return cls.create(
            report_name=new_name or f"{original['report_name']} (Copy)",
            dataset_id=original.get('dataset_id'),
            report_type=original.get('report_type', 'tabular'),
            description=original.get('description'),
            selected_fields=original.get('selected_fields'),
            selected_kpis=original.get('selected_kpis'),
            filters_config=original.get('filters_config'),
            grouping_config=original.get('grouping_config'),
            sorting_config=original.get('sorting_config'),
            layout_config=original.get('layout_config'),
            chart_type=original.get('chart_type'),
            visualization_type=original.get('visualization_type'),
            status='draft',
            is_shared=False,
            access_level='private',
            default_parameters=original.get('default_parameters'),
            row_limit=original.get('row_limit', 1000),
            timeout_seconds=original.get('timeout_seconds', 300),
            created_by_user_id=created_by_user_id or original.get('created_by_user_id')
        )


# =============================================================================
# REPORT SCHEDULES
# =============================================================================

class ReportSchedule:
    """
    Represents a scheduled report execution and delivery configuration.
    """
    
    TABLE_NAME = "bi_report_schedules"
    
    @staticmethod
    def create_table():
        """Create the report schedules table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_report_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_code TEXT UNIQUE,
                    schedule_name TEXT NOT NULL,
                    description TEXT,
                    report_id INTEGER NOT NULL,
                    frequency TEXT NOT NULL DEFAULT 'monthly',
                    day_of_week INTEGER,
                    day_of_month INTEGER,
                    run_time TEXT NOT NULL,
                    timezone TEXT DEFAULT 'UTC',
                    start_date DATE,
                    end_date DATE,
                    output_formats TEXT DEFAULT '["excel"]',
                    delivery_method TEXT DEFAULT 'email',
                    recipient_emails TEXT,
                    recipient_user_ids TEXT,
                    email_subject TEXT,
                    email_body_template TEXT,
                    attachment_name_template TEXT,
                    is_active INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'active',
                    last_run_at TIMESTAMP,
                    last_run_status TEXT,
                    last_run_error TEXT,
                    next_run_at TIMESTAMP,
                    run_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    retry_delay_minutes INTEGER DEFAULT 30,
                    created_by_user_id INTEGER,
                    updated_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_schedule_report ON bi_report_schedules(report_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_schedule_status ON bi_report_schedules(status)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_schedule_next_run ON bi_report_schedules(next_run_at)
            """)
            db.commit()
    
    @classmethod
    def create(cls, schedule_name: str, report_id: int,
               frequency: str = "monthly", run_time: str = "09:00",
               timezone: str = "UTC", day_of_week: int = None,
               day_of_month: int = None, start_date: str = None,
               end_date: str = None, output_formats: List[str] = None,
               delivery_method: str = "email", recipient_emails: List[str] = None,
               recipient_user_ids: List[int] = None,
               email_subject: str = None, email_body_template: str = None,
               attachment_name_template: str = None,
               created_by_user_id: int = None, notes: str = None,
               max_retries: int = 3, retry_delay_minutes: int = 30) -> int:
        """Create a new report schedule."""
        schedule_code = f"SCH_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        next_run = cls._calculate_next_run(frequency, run_time, day_of_week, day_of_month)
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_report_schedules 
                (schedule_code, schedule_name, report_id, frequency, run_time,
                 timezone, day_of_week, day_of_month, start_date, end_date,
                 output_formats, delivery_method, recipient_emails, recipient_user_ids,
                 email_subject, email_body_template, attachment_name_template,
                 next_run_at, created_by_user_id, notes, max_retries, retry_delay_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_code, schedule_name, report_id, frequency, run_time,
                timezone, day_of_week, day_of_month, start_date, end_date,
                json.dumps(output_formats or ["excel"]),
                delivery_method,
                json.dumps(recipient_emails) if recipient_emails else None,
                json.dumps(recipient_user_ids) if recipient_user_ids else None,
                email_subject, email_body_template, attachment_name_template,
                next_run, created_by_user_id, notes, max_retries, retry_delay_minutes
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def _calculate_next_run(cls, frequency: str, run_time: str,
                           day_of_week: int = None, day_of_month: int = None) -> str:
        """Calculate the next run time based on frequency."""
        now = datetime.now()
        time_parts = run_time.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        if frequency == "once":
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        elif frequency == "daily":
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        elif frequency == "weekly":
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = (now + timedelta(days=days_ahead)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )
            return next_run
        elif frequency == "monthly":
            if day_of_month:
                if now.day < day_of_month:
                    next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    next_run = (now + timedelta(days=28)).replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                next_run = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run
        elif frequency == "quarterly":
            quarter = (now.month - 1) // 3
            next_month = quarter * 3 + 1
            next_run = now.replace(month=next_month, day=1, hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run.replace(month=next_month + 3 if next_month < 10 else 1)
            return next_run
        else:
            return now + timedelta(days=1)
    
    @classmethod
    def get_by_id(cls, schedule_id: int) -> Optional[Dict]:
        """Get a schedule by ID."""
        return cls._get_full_schedule(
            "SELECT * FROM bi_report_schedules WHERE id = ?",
            (schedule_id,)
        )
    
    @classmethod
    def get_all(cls, include_inactive: bool = False,
                report_id: int = None) -> List[Dict]:
        """Get all schedules."""
        with reporting_db_context() as db:
            query = "SELECT * FROM bi_report_schedules"
            conditions = []
            params = []
            
            if not include_inactive:
                conditions.append("is_active = 1")
            if report_id:
                conditions.append("report_id = ?")
                params.append(report_id)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY schedule_name"
            
            rows = db.execute(query, params).fetchall()
            return [cls._parse_schedule(row) for row in rows_to_list(rows)]
    
    @classmethod
    def get_due_schedules(cls) -> List[Dict]:
        """Get schedules that are due to run."""
        with reporting_db_context() as db:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows = db.execute("""
                SELECT * FROM bi_report_schedules 
                WHERE is_active = 1 
                AND status = 'active'
                AND next_run_at <= ?
                AND (end_date IS NULL OR end_date >= DATE(?))
                ORDER BY next_run_at
            """, (now, now)).fetchall()
            return [cls._parse_schedule(row) for row in rows_to_list(rows)]
    
    @classmethod
    def _get_full_schedule(cls, query: str, params: Tuple) -> Optional[Dict]:
        """Internal method to get a schedule with parsed JSON fields."""
        with reporting_db_context() as db:
            row = db.execute(query, params).fetchone()
            if not row:
                return None
            return cls._parse_schedule(row_to_dict(row))
    
    @classmethod
    def _parse_schedule(cls, row: Dict) -> Dict:
        """Parse JSON fields in a schedule row."""
        if not row:
            return row
        json_fields = ['output_formats', 'recipient_emails', 'recipient_user_ids']
        for field in json_fields:
            if row.get(field):
                try:
                    row[field] = json.loads(row[field])
                except:
                    pass
        return row
    
    @classmethod
    def update(cls, schedule_id: int, **kwargs) -> bool:
        """Update a schedule."""
        allowed_fields = [
            'schedule_name', 'description', 'report_id', 'frequency',
            'run_time', 'timezone', 'day_of_week', 'day_of_month',
            'start_date', 'end_date', 'output_formats', 'delivery_method',
            'recipient_emails', 'recipient_user_ids', 'email_subject',
            'email_body_template', 'attachment_name_template', 'is_active',
            'status', 'last_run_at', 'last_run_status', 'last_run_error',
            'next_run_at', 'failure_count', 'max_retries', 'retry_delay_minutes',
            'updated_by_user_id', 'notes'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                if field in ['output_formats', 'recipient_emails', 'recipient_user_ids']:
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(kwargs[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(schedule_id)
        
        with reporting_db_context() as db:
            db.execute(
                f"UPDATE bi_report_schedules SET {', '.join(updates)} WHERE id = ?",
                params
            )
            db.commit()
            return True
    
    @classmethod
    def record_run_start(cls, schedule_id: int) -> bool:
        """Record that a schedule run has started."""
        with reporting_db_context() as db:
            db.execute("""
                UPDATE bi_report_schedules 
                SET last_run_at = CURRENT_TIMESTAMP, 
                    status = 'running',
                    run_count = run_count + 1 
                WHERE id = ?
            """, (schedule_id,))
            db.commit()
            return True
    
    @classmethod
    def record_run_complete(cls, schedule_id: int, success: bool = True,
                           error: str = None) -> bool:
        """Record that a schedule run has completed."""
        now = datetime.now()
        
        schedule = cls.get_by_id(schedule_id)
        if not schedule:
            return False
        
        next_run = cls._calculate_next_run(
            schedule['frequency'], schedule['run_time'],
            schedule.get('day_of_week'), schedule.get('day_of_month')
        )
        
        with reporting_db_context() as db:
            if success:
                db.execute("""
                    UPDATE bi_report_schedules 
                    SET status = 'active',
                        last_run_status = 'success',
                        last_run_error = NULL,
                        next_run_at = ?,
                        failure_count = 0
                    WHERE id = ?
                """, (next_run, schedule_id))
            else:
                failure_count = schedule.get('failure_count', 0) + 1
                max_retries = schedule.get('max_retries', 3)
                
                if failure_count >= max_retries:
                    new_status = 'failed'
                else:
                    new_status = 'active'
                
                db.execute("""
                    UPDATE bi_report_schedules 
                    SET status = ?,
                        last_run_status = 'failed',
                        last_run_error = ?,
                        next_run_at = ?,
                        failure_count = ?
                    WHERE id = ?
                """, (new_status, error, next_run, failure_count, schedule_id))
            
            db.commit()
            return True
    
    @classmethod
    def delete(cls, schedule_id: int) -> bool:
        """Delete a schedule."""
        with reporting_db_context() as db:
            db.execute("DELETE FROM bi_report_schedules WHERE id = ?", (schedule_id,))
            db.commit()
            return True


# =============================================================================
# SCHEDULE DELIVERY LOGS
# =============================================================================

class DeliveryLog:
    """
    Tracks delivery attempts for scheduled reports.
    """
    
    TABLE_NAME = "bi_delivery_logs"
    
    @staticmethod
    def create_table():
        """Create the delivery logs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_delivery_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    schedule_id INTEGER NOT NULL,
                    run_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    output_format TEXT,
                    recipient_email TEXT,
                    recipient_user_id INTEGER,
                    file_path TEXT,
                    file_size_bytes INTEGER,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (schedule_id) REFERENCES bi_report_schedules(id) ON DELETE CASCADE
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_schedule ON bi_delivery_logs(schedule_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_status ON bi_delivery_logs(status)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_delivery_run_at ON bi_delivery_logs(run_at)
            """)
            db.commit()
    
    @classmethod
    def create(cls, schedule_id: int, run_at: datetime,
               status: str, output_format: str = None,
               recipient_email: str = None, recipient_user_id: int = None,
               file_path: str = None, file_size_bytes: int = None,
               error_message: str = None, retry_count: int = 0) -> int:
        """Create a new delivery log entry."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_delivery_logs 
                (schedule_id, run_at, status, output_format, recipient_email,
                 recipient_user_id, file_path, file_size_bytes, error_message, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_id, run_at, status, output_format, recipient_email,
                recipient_user_id, file_path, file_size_bytes, error_message, retry_count
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_schedule(cls, schedule_id: int, limit: int = 50) -> List[Dict]:
        """Get delivery logs for a schedule."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_delivery_logs 
                WHERE schedule_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (schedule_id, limit)).fetchall()
            return rows_to_list(rows)
    
    @classmethod
    def get_failed(cls, limit: int = 100) -> List[Dict]:
        """Get recent failed deliveries."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT dl.*, rs.schedule_name, rs.report_id
                FROM bi_delivery_logs dl
                JOIN bi_report_schedules rs ON dl.schedule_id = rs.id
                WHERE dl.status = 'failed'
                ORDER BY dl.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return rows_to_list(rows)


# =============================================================================
# AD-HOC QUERIES
# =============================================================================

class AdhocQuery:
    """
    Represents an ad-hoc query configuration and execution history.
    """
    
    TABLE_NAME = "bi_adhoc_queries"
    
    @staticmethod
    def create_table():
        """Create the ad-hoc queries table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_adhoc_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_code TEXT UNIQUE,
                    query_name TEXT NOT NULL,
                    description TEXT,
                    query_type TEXT DEFAULT 'select',
                    dataset_id INTEGER,
                    sql_statement TEXT,
                    parameters_config TEXT,
                    result_columns TEXT,
                    result_sample TEXT,
                    row_limit INTEGER DEFAULT 1000,
                    timeout_seconds INTEGER DEFAULT 60,
                    status TEXT DEFAULT 'draft',
                    is_shared INTEGER DEFAULT 0,
                    access_level TEXT DEFAULT 'private',
                    execution_count INTEGER DEFAULT 0,
                    last_executed_at TIMESTAMP,
                    last_execution_time_ms INTEGER,
                    avg_execution_time_ms INTEGER,
                    error_message TEXT,
                    created_by_user_id INTEGER,
                    updated_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    favorite INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_code ON bi_adhoc_queries(query_code)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_status ON bi_adhoc_queries(status)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_owner ON bi_adhoc_queries(created_by_user_id)
            """)
            db.commit()
    
    @classmethod
    def create(cls, query_name: str, dataset_id: int = None,
               sql_statement: str = None, query_type: str = "select",
               description: str = None, parameters_config: Dict = None,
               row_limit: int = 1000, timeout_seconds: int = 60,
               status: str = "draft", is_shared: bool = False,
               access_level: str = "private",
               created_by_user_id: int = None, notes: str = None) -> int:
        """Create a new ad-hoc query."""
        query_code = f"QRY_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_adhoc_queries 
                (query_code, query_name, description, query_type, dataset_id,
                 sql_statement, parameters_config, row_limit, timeout_seconds,
                 status, is_shared, access_level, created_by_user_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_code, query_name, description, query_type, dataset_id,
                sql_statement, json.dumps(parameters_config) if parameters_config else None,
                row_limit, timeout_seconds, status,
                1 if is_shared else 0, access_level,
                created_by_user_id, notes
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_id(cls, query_id: int) -> Optional[Dict]:
        """Get a query by ID."""
        return cls._get_full_query(
            "SELECT * FROM bi_adhoc_queries WHERE id = ?",
            (query_id,)
        )
    
    @classmethod
    def _get_full_query(cls, query: str, params: Tuple) -> Optional[Dict]:
        """Internal method to get a query with parsed JSON fields."""
        with reporting_db_context() as db:
            row = db.execute(query, params).fetchone()
            if not row:
                return None
            
            result = row_to_dict(row)
            json_fields = ['parameters_config', 'result_columns', 'result_sample']
            for field in json_fields:
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except:
                        pass
            return result
    
    @classmethod
    def get_my_queries(cls, user_id: int) -> List[Dict]:
        """Get queries created by a specific user."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_adhoc_queries 
                WHERE created_by_user_id = ?
                ORDER BY updated_at DESC
            """, (user_id,)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                for field in ['parameters_config', 'result_columns', 'result_sample']:
                    if row.get(field):
                        try:
                            row[field] = json.loads(row[field])
                        except:
                            pass
                results.append(row)
            return results
    
    @classmethod
    def get_shared_queries(cls) -> List[Dict]:
        """Get all shared queries."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_adhoc_queries 
                WHERE is_shared = 1
                ORDER BY query_name
            """).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                for field in ['parameters_config', 'result_columns', 'result_sample']:
                    if row.get(field):
                        try:
                            row[field] = json.loads(row[field])
                        except:
                            pass
                results.append(row)
            return results
    
    @classmethod
    def update(cls, query_id: int, **kwargs) -> bool:
        """Update a query."""
        allowed_fields = [
            'query_name', 'description', 'dataset_id', 'sql_statement',
            'query_type', 'parameters_config', 'row_limit', 'timeout_seconds',
            'status', 'is_shared', 'access_level', 'result_columns',
            'result_sample', 'updated_by_user_id', 'favorite', 'notes'
        ]
        
        updates = []
        params = []
        for field in allowed_fields:
            if field in kwargs:
                if field in ['parameters_config', 'result_columns', 'result_sample']:
                    updates.append(f"{field} = ?")
                    params.append(json.dumps(kwargs[field]))
                else:
                    updates.append(f"{field} = ?")
                    params.append(kwargs[field])
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(query_id)
        
        with reporting_db_context() as db:
            db.execute(
                f"UPDATE bi_adhoc_queries SET {', '.join(updates)} WHERE id = ?",
                params
            )
            db.commit()
            return True
    
    @classmethod
    def record_execution(cls, query_id: int, execution_time_ms: int,
                        status: str = "completed", error_message: str = None,
                        result_sample: List[Dict] = None) -> bool:
        """Record a query execution."""
        with reporting_db_context() as db:
            query = db.execute("SELECT * FROM bi_adhoc_queries WHERE id = ?", (query_id,)).fetchone()
            if not query:
                return False
            
            current_avg = query['avg_execution_time_ms'] or 0
            current_count = query['execution_count'] or 0
            
            new_avg = ((current_avg * current_count) + execution_time_ms) / (current_count + 1)
            
            db.execute("""
                UPDATE bi_adhoc_queries 
                SET last_executed_at = CURRENT_TIMESTAMP,
                    last_execution_time_ms = ?,
                    avg_execution_time_ms = ?,
                    execution_count = execution_count + 1,
                    status = ?,
                    error_message = ?,
                    result_sample = ?
                WHERE id = ?
            """, (
                execution_time_ms, int(new_avg), status, error_message,
                json.dumps(result_sample[:10]) if result_sample else None,
                query_id
            ))
            db.commit()
            return True
    
    @classmethod
    def delete(cls, query_id: int) -> bool:
        """Delete a query."""
        with reporting_db_context() as db:
            db.execute("DELETE FROM bi_adhoc_queries WHERE id = ?", (query_id,))
            db.commit()
            return True


# =============================================================================
# AD-HOC QUERY LOGS
# =============================================================================

class QueryLog:
    """
    Detailed execution logs for ad-hoc queries.
    """
    
    TABLE_NAME = "bi_query_logs"
    
    @staticmethod
    def create_table():
        """Create the query logs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_query_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER,
                    query_name TEXT,
                    executed_by_user_id INTEGER NOT NULL,
                    sql_statement TEXT,
                    parameters_used TEXT,
                    result_row_count INTEGER,
                    execution_time_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    client_ip TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_querylog_query ON bi_query_logs(query_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_querylog_user ON bi_query_logs(executed_by_user_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_querylog_status ON bi_query_logs(status)
            """)
            db.commit()
    
    @classmethod
    def create(cls, query_id: int = None, query_name: str = None,
               executed_by_user_id: int = None, sql_statement: str = None,
               parameters_used: Dict = None, result_row_count: int = 0,
               execution_time_ms: int = 0, status: str = "completed",
               error_message: str = None, client_ip: str = None,
               user_agent: str = None) -> int:
        """Create a new query log entry."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_query_logs 
                (query_id, query_name, executed_by_user_id, sql_statement,
                 parameters_used, result_row_count, execution_time_ms,
                 status, error_message, client_ip, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id, query_name, executed_by_user_id, sql_statement,
                json.dumps(parameters_used) if parameters_used else None,
                result_row_count, execution_time_ms, status, error_message,
                client_ip, user_agent
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 100) -> List[Dict]:
        """Get query logs for a user."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_query_logs 
                WHERE executed_by_user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results
    
    @classmethod
    def get_slow_queries(cls, threshold_ms: int = 5000, limit: int = 50) -> List[Dict]:
        """Get slow queries above a threshold."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_query_logs 
                WHERE execution_time_ms > ? AND status = 'completed'
                ORDER BY execution_time_ms DESC
                LIMIT ?
            """, (threshold_ms, limit)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results


# =============================================================================
# REPORT ACCESS LOGS
# =============================================================================

class ReportAccessLog:
    """
    Tracks access to saved reports for audit purposes.
    """
    
    TABLE_NAME = "bi_report_access_logs"
    
    @staticmethod
    def create_table():
        """Create the report access logs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_report_access_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER,
                    report_name TEXT,
                    report_code TEXT,
                    accessed_by_user_id INTEGER NOT NULL,
                    access_type TEXT NOT NULL,
                    parameters_used TEXT,
                    export_format TEXT,
                    scheduled_report_id INTEGER,
                    execution_time_ms INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_report ON bi_report_access_logs(report_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_user ON bi_report_access_logs(accessed_by_user_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_access_at ON bi_report_access_logs(created_at)
            """)
            db.commit()
    
    @classmethod
    def create(cls, report_id: int = None, report_name: str = None,
               report_code: str = None, accessed_by_user_id: int = None,
               access_type: str = "view", parameters_used: Dict = None,
               export_format: str = None, scheduled_report_id: int = None,
               execution_time_ms: int = None, ip_address: str = None,
               user_agent: str = None) -> int:
        """Create a new access log entry."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_report_access_logs 
                (report_id, report_name, report_code, accessed_by_user_id,
                 access_type, parameters_used, export_format, scheduled_report_id,
                 execution_time_ms, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, report_name, report_code, accessed_by_user_id,
                access_type, json.dumps(parameters_used) if parameters_used else None,
                export_format, scheduled_report_id, execution_time_ms,
                ip_address, user_agent
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_report(cls, report_id: int, limit: int = 100) -> List[Dict]:
        """Get access logs for a specific report."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_report_access_logs 
                WHERE report_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (report_id, limit)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results
    
    @classmethod
    def get_recent_access(cls, user_id: int = None, limit: int = 50) -> List[Dict]:
        """Get recent report access logs."""
        with reporting_db_context() as db:
            query = """
                SELECT * FROM bi_report_access_logs 
                WHERE 1=1
            """
            params = []
            
            if user_id:
                query += " AND accessed_by_user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = db.execute(query, params).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results


# =============================================================================
# EXPORT LOGS
# =============================================================================

class ExportLog:
    """
    Tracks report exports for audit and compliance.
    """
    
    TABLE_NAME = "bi_export_logs"
    
    @staticmethod
    def create_table():
        """Create the export logs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_export_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_code TEXT UNIQUE,
                    report_id INTEGER,
                    report_name TEXT,
                    report_code TEXT,
                    exported_by_user_id INTEGER NOT NULL,
                    export_format TEXT NOT NULL,
                    file_name TEXT,
                    file_path TEXT,
                    file_size_bytes INTEGER,
                    row_count INTEGER,
                    parameters_used TEXT,
                    include_headers INTEGER DEFAULT 1,
                    compressed INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_export_report ON bi_export_logs(report_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_export_user ON bi_export_logs(exported_by_user_id)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_export_format ON bi_export_logs(export_format)
            """)
            db.commit()
    
    @classmethod
    def create(cls, report_id: int = None, report_name: str = None,
               report_code: str = None, exported_by_user_id: int = None,
               export_format: str = "excel", file_name: str = None,
               file_path: str = None, file_size_bytes: int = None,
               row_count: int = 0, parameters_used: Dict = None,
               include_headers: bool = True, compressed: bool = False,
               status: str = "completed", error_message: str = None,
               execution_time_ms: int = None, ip_address: str = None) -> int:
        """Create a new export log entry."""
        export_code = f"EXP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_export_logs 
                (export_code, report_id, report_name, report_code,
                 exported_by_user_id, export_format, file_name, file_path,
                 file_size_bytes, row_count, parameters_used, include_headers,
                 compressed, status, error_message, execution_time_ms, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                export_code, report_id, report_name, report_code,
                exported_by_user_id, export_format, file_name, file_path,
                file_size_bytes, row_count, json.dumps(parameters_used) if parameters_used else None,
                1 if include_headers else 0, 1 if compressed else 0,
                status, error_message, execution_time_ms, ip_address
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 50) -> List[Dict]:
        """Get export logs for a user."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_export_logs 
                WHERE exported_by_user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results
    
    @classmethod
    def get_recent_exports(cls, limit: int = 50) -> List[Dict]:
        """Get recent exports across all users."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_export_logs 
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('parameters_used'):
                    try:
                        row['parameters_used'] = json.loads(row['parameters_used'])
                    except:
                        pass
                results.append(row)
            return results


# =============================================================================
# DRILL-DOWN CONFIGURATIONS
# =============================================================================

class DrillDownConfig:
    """
    Defines drill-down paths from summary reports to detail views.
    """
    
    TABLE_NAME = "bi_drilldown_configs"
    
    @staticmethod
    def create_table():
        """Create the drill-down configurations table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_drilldown_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_code TEXT UNIQUE,
                    config_name TEXT NOT NULL,
                    description TEXT,
                    source_dataset_id INTEGER,
                    source_field TEXT,
                    target_dataset_id INTEGER,
                    target_field TEXT,
                    target_url TEXT,
                    target_type TEXT DEFAULT 'report',
                    filter_mapping TEXT,
                    is_active INTEGER DEFAULT 1,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_drilldown_source ON bi_drilldown_configs(source_dataset_id)
            """)
            db.commit()
    
    @classmethod
    def create(cls, config_name: str, source_dataset_id: int,
               source_field: str, target_dataset_id: int = None,
               target_field: str = None, target_url: str = None,
               target_type: str = "report", filter_mapping: Dict = None,
               description: str = None, display_order: int = 0) -> int:
        """Create a new drill-down configuration."""
        config_code = f"DD_{source_dataset_id}_{source_field}_{datetime.now().strftime('%Y%m%d')}"
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_drilldown_configs 
                (config_code, config_name, description, source_dataset_id,
                 source_field, target_dataset_id, target_field, target_url,
                 target_type, filter_mapping, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config_code, config_name, description, source_dataset_id,
                source_field, target_dataset_id, target_field, target_url,
                target_type, json.dumps(filter_mapping) if filter_mapping else None,
                display_order
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_by_source(cls, source_dataset_id: int, source_field: str = None) -> List[Dict]:
        """Get drill-down configurations for a source."""
        with reporting_db_context() as db:
            query = """
                SELECT * FROM bi_drilldown_configs 
                WHERE source_dataset_id = ? AND is_active = 1
            """
            params = [source_dataset_id]
            
            if source_field:
                query += " AND source_field = ?"
                params.append(source_field)
            
            query += " ORDER BY display_order"
            
            rows = db.execute(query, params).fetchall()
            
            results = []
            for row in rows_to_list(rows):
                if row.get('filter_mapping'):
                    try:
                        row['filter_mapping'] = json.loads(row['filter_mapping'])
                    except:
                        pass
                results.append(row)
            return results
    
    @classmethod
    def delete(cls, config_id: int) -> bool:
        """Delete a drill-down configuration."""
        with reporting_db_context() as db:
            db.execute("DELETE FROM bi_drilldown_configs WHERE id = ?", (config_id,))
            db.commit()
            return True


# =============================================================================
# PERFORMANCE / QUERY GUARDRAILS
# =============================================================================

class PerformanceLog:
    """
    Tracks query performance for monitoring and optimization.
    """
    
    TABLE_NAME = "bi_performance_logs"
    
    @staticmethod
    def create_table():
        """Create the performance logs table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_fingerprint TEXT,
                    query_type TEXT,
                    dataset_code TEXT,
                    execution_time_ms INTEGER NOT NULL,
                    rows_scanned INTEGER,
                    rows_returned INTEGER,
                    cached_result INTEGER DEFAULT 0,
                    timeout_occurred INTEGER DEFAULT 0,
                    slow_query INTEGER DEFAULT 0,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_fingerprint ON bi_performance_logs(query_fingerprint)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_perf_slow ON bi_performance_logs(slow_query)
            """)
            db.commit()
    
    @classmethod
    def create(cls, query_fingerprint: str = None, query_type: str = None,
               dataset_code: str = None, execution_time_ms: int = 0,
               rows_scanned: int = 0, rows_returned: int = 0,
               cached_result: bool = False, timeout_occurred: bool = False,
               slow_query: bool = False, user_id: int = None) -> int:
        """Create a new performance log entry."""
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_performance_logs 
                (query_fingerprint, query_type, dataset_code, execution_time_ms,
                 rows_scanned, rows_returned, cached_result, timeout_occurred,
                 slow_query, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query_fingerprint, query_type, dataset_code, execution_time_ms,
                rows_scanned, rows_returned, 1 if cached_result else 0,
                1 if timeout_occurred else 0, 1 if slow_query else 0, user_id
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_slow_queries(cls, threshold_ms: int = 5000, limit: int = 50) -> List[Dict]:
        """Get slow queries above a threshold."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_performance_logs 
                WHERE slow_query = 1
                ORDER BY execution_time_ms DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return rows_to_list(rows)
    
    @classmethod
    def get_average_execution_time(cls, query_fingerprint: str = None) -> Optional[float]:
        """Get average execution time for a query fingerprint."""
        with reporting_db_context() as db:
            if query_fingerprint:
                row = db.execute("""
                    SELECT AVG(execution_time_ms) as avg_time
                    FROM bi_performance_logs 
                    WHERE query_fingerprint = ?
                """, (query_fingerprint,)).fetchone()
            else:
                row = db.execute("""
                    SELECT AVG(execution_time_ms) as avg_time
                    FROM bi_performance_logs 
                """).fetchone()
            return row['avg_time'] if row else None


# =============================================================================
# REPORT APPROVALS
# =============================================================================

class ApprovalRequest:
    """
    Tracks approval requests for shared/scheduled reports.
    """
    
    TABLE_NAME = "bi_approval_requests"
    
    @staticmethod
    def create_table():
        """Create the approval requests table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_approval_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_code TEXT UNIQUE,
                    request_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    entity_name TEXT,
                    requested_by_user_id INTEGER NOT NULL,
                    approved_by_user_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    reason TEXT,
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decided_at TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_approval_status ON bi_approval_requests(status)
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_approval_type ON bi_approval_requests(entity_type)
            """)
            db.commit()
    
    @classmethod
    def create(cls, request_type: str, entity_type: str, entity_id: int,
               entity_name: str = None, requested_by_user_id: int = None,
               reason: str = None) -> int:
        """Create a new approval request."""
        request_code = f"APR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        
        with reporting_db_context() as db:
            cursor = db.execute("""
                INSERT INTO bi_approval_requests 
                (request_code, request_type, entity_type, entity_id, entity_name,
                 requested_by_user_id, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                request_code, request_type, entity_type, entity_id, entity_name,
                requested_by_user_id, reason
            ))
            db.commit()
            return cursor.lastrowid
    
    @classmethod
    def get_pending(cls) -> List[Dict]:
        """Get all pending approval requests."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_approval_requests 
                WHERE status = 'pending'
                ORDER BY created_at ASC
            """).fetchall()
            return rows_to_list(rows)
    
    @classmethod
    def approve(cls, request_id: int, approved_by_user_id: int,
                remarks: str = None) -> bool:
        """Approve a request."""
        with reporting_db_context() as db:
            db.execute("""
                UPDATE bi_approval_requests 
                SET status = 'approved',
                    approved_by_user_id = ?,
                    remarks = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approved_by_user_id, remarks, request_id))
            db.commit()
            return True
    
    @classmethod
    def reject(cls, request_id: int, approved_by_user_id: int,
               remarks: str = None) -> bool:
        """Reject a request."""
        with reporting_db_context() as db:
            db.execute("""
                UPDATE bi_approval_requests 
                SET status = 'rejected',
                    approved_by_user_id = ?,
                    remarks = ?,
                    decided_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approved_by_user_id, remarks, request_id))
            db.commit()
            return True


# =============================================================================
# REPORTING SETTINGS
# =============================================================================

class ReportingSettings:
    """
    Global settings for the BI reporting module.
    """
    
    TABLE_NAME = "bi_settings"
    
    @staticmethod
    def create_table():
        """Create the reporting settings table."""
        with reporting_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS bi_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    is_encrypted INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_settings_key ON bi_settings(setting_key)
            """)
            db.commit()
    
    @classmethod
    def get(cls, setting_key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with reporting_db_context() as db:
            row = db.execute(
                "SELECT * FROM bi_settings WHERE setting_key = ?",
                (setting_key,)
            ).fetchone()
            
            if not row:
                return default
            
            value = row['setting_value']
            setting_type = row['setting_type']
            
            if setting_type == 'int':
                return int(value) if value else default
            elif setting_type == 'float':
                return float(value) if value else default
            elif setting_type == 'bool':
                return value == 'true' if value else default
            elif setting_type == 'json':
                try:
                    return json.loads(value) if value else default
                except:
                    return default
            else:
                return value if value else default
    
    @classmethod
    def set(cls, setting_key: str, value: Any, setting_type: str = None,
           description: str = None, category: str = "general") -> bool:
        """Set a setting value."""
        if setting_type is None:
            if isinstance(value, bool):
                setting_type = 'bool'
            elif isinstance(value, int):
                setting_type = 'int'
            elif isinstance(value, float):
                setting_type = 'float'
            elif isinstance(value, dict) or isinstance(value, list):
                setting_type = 'json'
                value = json.dumps(value)
            else:
                setting_type = 'string'
                value = str(value)
        
        with reporting_db_context() as db:
            db.execute("""
                INSERT INTO bi_settings (setting_key, setting_value, setting_type, description, category)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value = excluded.setting_value,
                    setting_type = excluded.setting_type,
                    description = COALESCE(excluded.description, description),
                    updated_at = CURRENT_TIMESTAMP
            """, (setting_key, value, setting_type, description, category))
            db.commit()
            return True
    
    @classmethod
    def get_all_by_category(cls, category: str = "general") -> Dict[str, Any]:
        """Get all settings in a category."""
        with reporting_db_context() as db:
            rows = db.execute("""
                SELECT * FROM bi_settings WHERE category = ?
                ORDER BY setting_key
            """, (category,)).fetchall()
            
            settings = {}
            for row in rows:
                value = row['setting_value']
                setting_type = row['setting_type']
                
                if setting_type == 'int':
                    settings[row['setting_key']] = int(value) if value else 0
                elif setting_type == 'float':
                    settings[row['setting_key']] = float(value) if value else 0.0
                elif setting_type == 'bool':
                    settings[row['setting_key']] = value == 'true' if value else False
                elif setting_type == 'json':
                    try:
                        settings[row['setting_key']] = json.loads(value) if value else None
                    except:
                        settings[row['setting_key']] = value
                else:
                    settings[row['setting_key']] = value
            return settings


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_reporting_tables():
    """
    Initialize all BI reporting tables.
    Call this function once during application startup.
    """
    ReportingDataset.create_table()
    DatasetField.create_table()
    ReportingKPI.create_table()
    SavedReport.create_table()
    ReportSchedule.create_table()
    DeliveryLog.create_table()
    AdhocQuery.create_table()
    QueryLog.create_table()
    ReportAccessLog.create_table()
    ExportLog.create_table()
    DrillDownConfig.create_table()
    PerformanceLog.create_table()
    ApprovalRequest.create_table()
    ReportingSettings.create_table()
    
    initialize_default_settings()


def initialize_default_settings():
    """Initialize default reporting settings."""
    defaults = [
        ('bi.default_row_limit', '1000', 'int', 'Default maximum rows for reports'),
        ('bi.default_timeout_seconds', '300', 'int', 'Default query timeout'),
        ('bi.slow_query_threshold_ms', '5000', 'int', 'Threshold for marking queries as slow'),
        ('bi.max_export_rows', '50000', 'int', 'Maximum rows for exports'),
        ('bi.enable_query_cache', 'true', 'bool', 'Enable query result caching'),
        ('bi.cache_ttl_minutes', '60', 'int', 'Default cache TTL in minutes'),
        ('bi.require_approval_for_shared', 'false', 'bool', 'Require approval for shared reports'),
        ('bi.require_approval_for_schedule', 'false', 'bool', 'Require approval for scheduled reports'),
        ('bi.audit_log_retention_days', '365', 'int', 'Days to retain audit logs'),
        ('bi.performance_log_retention_days', '90', 'int', 'Days to retain performance logs'),
        ('bi.allow_csv_export', 'true', 'bool', 'Allow CSV exports'),
        ('bi.allow_excel_export', 'true', 'bool', 'Allow Excel exports'),
        ('bi.allow_pdf_export', 'false', 'bool', 'Allow PDF exports'),
        ('bi.default_export_format', 'excel', 'string', 'Default export format'),
        ('bi.max_schedules_per_user', '20', 'int', 'Maximum schedules per user'),
        ('bi.max_queries_per_user', '100', 'int', 'Maximum saved queries per user'),
    ]
    
    for key, value, setting_type, description in defaults:
        existing = ReportingSettings.get(key)
        if existing is None:
            ReportingSettings.set(key, value, setting_type, description)


# Auto-initialize when module is imported
initialize_reporting_tables()
