"""
Analytics Engine
================
Built-in enterprise analytics without external ML libraries.

Provides:
- Trend analysis (linear regression, moving averages)
- Variance analysis (budget vs actual)
- Ratio analysis (financial ratios)
- Peer comparison
- Alert generation
- KPI calculations
- Anomaly detection (statistical)

This module is AI-ready but uses only standard Python libraries.

Usage:
    from analytics_engine import (
        calculate_trend, calculate_variance, detect_outliers,
        calculate_kpi, generate_alert
    )
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


# =============================================================================
# TREND ANALYSIS
# =============================================================================

def calculate_trend(data: List[float], periods: int = 12) -> Dict[str, Any]:
    """
    Calculate trend using linear regression.

    Args:
        data: List of numeric values (time series, oldest first)
        periods: Number of periods to forecast ahead

    Returns:
        Dict with:
        - slope: Trend slope (positive = increasing)
        - intercept: Y-intercept
        - r_squared: R-squared (fit quality, 0-1)
        - forecast: List of forecasted values
        - direction: 'increasing', 'decreasing', or 'stable'
        - trend_strength: 'strong', 'moderate', 'weak', or 'none'

    Example:
        >>> data = [100, 105, 110, 115, 120, 125]
        >>> result = calculate_trend(data)
        >>> print(result['direction'])  # 'increasing'
    """
    n = len(data)
    if n < 2:
        return {
            'slope': 0, 'intercept': data[0] if data else 0,
            'r_squared': 0, 'forecast': data if data else [],
            'direction': 'stable', 'trend_strength': 'none'
        }

    # Calculate means
    x_mean = sum(range(n)) / n
    y_mean = sum(data) / n

    # Calculate slope and intercept (least squares)
    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator

    intercept = y_mean - slope * x_mean

    # Calculate R-squared
    ss_tot = sum((y - y_mean) ** 2 for y in data)
    ss_res = sum((y - (slope * i + intercept)) ** 2 for i, y in enumerate(data))

    if ss_tot == 0:
        r_squared = 0
    else:
        r_squared = 1 - (ss_res / ss_tot)

    # Determine direction and strength
    if abs(slope) < 0.01:
        direction = 'stable'
        trend_strength = 'none'
    elif slope > 0:
        direction = 'increasing'
        trend_strength = 'strong' if r_squared > 0.8 else 'moderate' if r_squared > 0.5 else 'weak'
    else:
        direction = 'decreasing'
        trend_strength = 'strong' if r_squared > 0.8 else 'moderate' if r_squared > 0.5 else 'weak'

    # Generate forecast
    forecast = [slope * (n + i) + intercept for i in range(1, periods + 1)]

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'forecast': forecast,
        'direction': direction,
        'trend_strength': trend_strength,
        'periods_forecast': periods
    }


def calculate_moving_average(data: List[float], window: int = 3) -> List[float]:
    """
    Calculate simple moving average.

    Args:
        data: List of numeric values
        window: Window size for averaging

    Returns:
        List of moving averages (same length as input, with None for first values)
    """
    if len(data) < window:
        return [None] * len(data)

    result = [None] * (window - 1)
    for i in range(window - 1, len(data)):
        avg = sum(data[i - window + 1:i + 1]) / window
        result.append(round(avg, 2))

    return result


def calculate_exponential_moving_average(data: List[float], alpha: float = 0.3) -> List[float]:
    """
    Calculate exponential moving average.

    Args:
        data: List of numeric values
        alpha: Smoothing factor (0-1), higher = more weight to recent

    Returns:
        List of EMA values
    """
    if not data:
        return []

    result = [data[0]]  # First value is initial EMA
    for i in range(1, len(data)):
        ema = alpha * data[i] + (1 - alpha) * result[-1]
        result.append(round(ema, 2))

    return result


# =============================================================================
# VARIANCE ANALYSIS
# =============================================================================

def calculate_variance(budget: float, actual: float, absolute: bool = True) -> Dict[str, Any]:
    """
    Calculate budget vs actual variance.

    Args:
        budget: Budgeted/planned amount
        actual: Actual amount
        absolute: If True, return absolute variance; if False, return percentage

    Returns:
        Dict with variance amount, percentage, and status
    """
    if budget == 0:
        variance_pct = 100 if actual != 0 else 0
    else:
        variance_pct = ((actual - budget) / budget) * 100

    variance_amount = actual - budget

    if absolute:
        variance = abs(variance_amount)
    else:
        variance = variance_pct

    # Determine status
    if variance_amount > 0:
        status = 'over_budget'
        severity = 'high' if abs(variance_pct) > 10 else 'medium' if abs(variance_pct) > 5 else 'low'
    elif variance_amount < 0:
        status = 'under_budget'
        severity = 'low'
    else:
        status = 'on_budget'
        severity = 'none'

    return {
        'budget': budget,
        'actual': actual,
        'variance': variance,
        'variance_amount': variance_amount,
        'variance_percentage': round(variance_pct, 2),
        'status': status,
        'severity': severity,
        'is_favorable': variance_amount <= 0  # Under budget is usually favorable
    }


def calculate_variance_analysis(period_data: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Perform variance analysis on multiple periods.

    Args:
        period_data: List of dicts with 'budget' and 'actual' keys

    Returns:
        Dict with overall variance and period-by-period breakdown
    """
    total_budget = sum(p['budget'] for p in period_data)
    total_actual = sum(p['actual'] for p in period_data)

    overall = calculate_variance(total_budget, total_actual)

    periods = []
    for i, p in enumerate(period_data):
        v = calculate_variance(p['budget'], p['actual'])
        v['period'] = i + 1
        v['period_budget'] = p['budget']
        v['period_actual'] = p['actual']
        periods.append(v)

    # Find worst variance
    worst = max(periods, key=lambda x: abs(x['variance_percentage']))

    return {
        'total_budget': total_budget,
        'total_actual': total_actual,
        'overall_variance': overall,
        'periods': periods,
        'worst_period': worst,
        'period_count': len(periods)
    }


# =============================================================================
# FINANCIAL RATIO ANALYSIS
# =============================================================================

def calculate_ratios(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate common financial ratios.

    Args:
        metrics: Dict with financial values like:
            - revenue, cogs, gross_profit
            - operating_expenses, operating_profit
            - net_income, total_assets, current_assets, current_liabilities
            - cash, accounts_receivable, inventory, accounts_payable
            - equity, debt

    Returns:
        Dict with calculated ratios
    """
    ratios = {}

    # Profitability Ratios
    if 'revenue' in metrics and metrics['revenue'] > 0:
        if 'gross_profit' in metrics:
            ratios['gross_margin'] = (metrics['gross_profit'] / metrics['revenue']) * 100
        if 'operating_profit' in metrics:
            ratios['operating_margin'] = (metrics['operating_profit'] / metrics['revenue']) * 100
        if 'net_income' in metrics:
            ratios['net_margin'] = (metrics['net_income'] / metrics['revenue']) * 100

    if 'cogs' in metrics and 'revenue' in metrics and metrics['revenue'] > 0:
        ratios['gross_profit_margin'] = ((metrics['revenue'] - metrics['cogs']) / metrics['revenue']) * 100

    # Liquidity Ratios
    if 'current_assets' in metrics and 'current_liabilities' in metrics:
        if metrics['current_liabilities'] > 0:
            ratios['current_ratio'] = metrics['current_assets'] / metrics['current_liabilities']
        if metrics['current_assets'] - metrics.get('inventory', 0) > 0 and metrics['current_liabilities'] > 0:
            ratios['quick_ratio'] = (metrics['current_assets'] - metrics.get('inventory', 0)) / metrics['current_liabilities']

    if 'cash' in metrics and 'current_liabilities' in metrics:
        if metrics['current_liabilities'] > 0:
            ratios['cash_ratio'] = metrics['cash'] / metrics['current_liabilities']

    # Leverage Ratios
    if 'total_assets' in metrics and 'equity' in metrics:
        if metrics['equity'] > 0:
            ratios['debt_to_equity'] = (metrics['total_assets'] - metrics['equity']) / metrics['equity']
        if metrics['total_assets'] > 0:
            ratios['debt_to_assets'] = (metrics['total_assets'] - metrics['equity']) / metrics['total_assets']

    # Efficiency Ratios (Activity)
    if 'revenue' in metrics and 'accounts_receivable' in metrics:
        if metrics['accounts_receivable'] > 0:
            ratios['receivables_turnover'] = metrics['revenue'] / metrics['accounts_receivable']
            ratios['days_sales_outstanding'] = 365 / ratios['receivables_turnover'] if ratios['receivables_turnover'] > 0 else 0

    if 'cogs' in metrics and 'inventory' in metrics:
        if metrics['inventory'] > 0:
            ratios['inventory_turnover'] = metrics['cogs'] / metrics['inventory']
            ratios['days_inventory'] = 365 / ratios['inventory_turnover'] if ratios['inventory_turnover'] > 0 else 0

    if 'revenue' in metrics and 'accounts_payable' in metrics:
        if metrics['accounts_payable'] > 0:
            ratios['payables_turnover'] = metrics['revenue'] / metrics['accounts_payable']
            ratios['days_payables_outstanding'] = 365 / ratios['payables_turnover'] if ratios['payables_turnover'] > 0 else 0

    return ratios


# =============================================================================
# ANOMALY DETECTION (Statistical)
# =============================================================================

def detect_outliers(data: List[float], std_threshold: float = 3.0) -> List[Dict[str, Any]]:
    """
    Detect outliers using standard deviation method.

    Args:
        data: List of numeric values
        std_threshold: Number of standard deviations to consider as outlier (default: 3)

    Returns:
        List of dicts with outlier info (index, value, z_score)
    """
    if len(data) < 3:
        return []

    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = math.sqrt(variance) if variance > 0 else 0

    if std_dev == 0:
        return []  # All values are the same

    outliers = []
    for i, value in enumerate(data):
        z_score = abs((value - mean) / std_dev)
        if z_score > std_threshold:
            outliers.append({
                'index': i,
                'value': value,
                'z_score': round(z_score, 2),
                'is_high': value > mean,
                'deviation': value - mean
            })

    return outliers


def detect_anomalies_iqr(data: List[float], multiplier: float = 1.5) -> List[Dict[str, Any]]:
    """
    Detect outliers using Interquartile Range (IQR) method.

    Args:
        data: List of numeric values
        multiplier: IQR multiplier for fence calculation (default: 1.5)

    Returns:
        List of dicts with outlier info
    """
    if len(data) < 4:
        return []

    sorted_data = sorted(data)
    n = len(sorted_data)

    # Calculate quartiles
    q1_idx = n // 4
    q3_idx = 3 * n // 4
    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    iqr = q3 - q1

    # Calculate bounds
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    outliers = []
    for i, value in enumerate(data):
        if value < lower_bound or value > upper_bound:
            outliers.append({
                'index': i,
                'value': value,
                'bound': 'lower' if value < lower_bound else 'upper',
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'iqr': iqr
            })

    return outliers


def detect_statistical_anomalies(data: List[float], window: int = 30) -> List[Dict[str, Any]]:
    """
    Detect anomalies using rolling statistics (for time series).

    Args:
        data: List of numeric values (time series)
        window: Rolling window size

    Returns:
        List of anomaly detections with context
    """
    if len(data) < window:
        return detect_outliers(data)

    anomalies = []
    for i in range(window, len(data)):
        window_data = data[i - window:i]
        current = data[i]

        # Calculate rolling mean and std
        mean = sum(window_data) / len(window_data)
        variance = sum((x - mean) ** 2 for x in window_data) / len(window_data)
        std_dev = math.sqrt(variance)

        if std_dev > 0:
            z_score = abs((current - mean) / std_dev)
            if z_score > 2.5:  # Threshold for anomaly
                anomalies.append({
                    'index': i,
                    'value': current,
                    'expected_range': (mean - 2 * std_dev, mean + 2 * std_dev),
                    'actual': current,
                    'deviation': current - mean,
                    'z_score': round(z_score, 2),
                    'severity': 'critical' if z_score > 4 else 'high' if z_score > 3 else 'medium'
                })

    return anomalies


# =============================================================================
# KPI CALCULATIONS
# =============================================================================

def calculate_kpi(kpi_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate various KPIs.

    Args:
        kpi_type: Type of KPI ('roi', 'roa', 'roe', ' gross_margin', 'conversion_rate', etc.)
        data: Dict with required metrics for the KPI type

    Returns:
        Dict with KPI value and metadata
    """
    kpi_functions = {
        'roi': lambda d: {
            'value': ((d.get('net_income', 0) / d.get('investment', 1)) * 100) if d.get('investment') else 0,
            'label': 'Return on Investment',
            'unit': '%'
        },
        'roa': lambda d: {
            'value': ((d.get('net_income', 0) / d.get('total_assets', 1)) * 100) if d.get('total_assets') else 0,
            'label': 'Return on Assets',
            'unit': '%'
        },
        'roe': lambda d: {
            'value': ((d.get('net_income', 0) / d.get('equity', 1)) * 100) if d.get('equity') else 0,
            'label': 'Return on Equity',
            'unit': '%'
        },
        'gross_margin': lambda d: {
            'value': (((d.get('revenue', 0) - d.get('cogs', 0)) / d.get('revenue', 1)) * 100) if d.get('revenue') else 0,
            'label': 'Gross Margin',
            'unit': '%'
        },
        'operating_margin': lambda d: {
            'value': ((d.get('operating_profit', 0) / d.get('revenue', 1)) * 100) if d.get('revenue') else 0,
            'label': 'Operating Margin',
            'unit': '%'
        },
        'net_margin': lambda d: {
            'value': ((d.get('net_income', 0) / d.get('revenue', 1)) * 100) if d.get('revenue') else 0,
            'label': 'Net Profit Margin',
            'unit': '%'
        },
        'current_ratio': lambda d: {
            'value': (d.get('current_assets', 0) / d.get('current_liabilities', 1)) if d.get('current_liabilities') else 0,
            'label': 'Current Ratio',
            'unit': 'x'
        },
        'quick_ratio': lambda d: {
            'value': ((d.get('current_assets', 0) - d.get('inventory', 0)) / d.get('current_liabilities', 1)) if d.get('current_liabilities') else 0,
            'label': 'Quick Ratio',
            'unit': 'x'
        },
        'debt_to_equity': lambda d: {
            'value': ((d.get('total_debt', 0) / d.get('equity', 1)) if d.get('equity') else 0),
            'label': 'Debt to Equity',
            'unit': 'x'
        },
        'inventory_turnover': lambda d: {
            'value': (d.get('cogs', 0) / d.get('inventory', 1)) if d.get('inventory') else 0,
            'label': 'Inventory Turnover',
            'unit': 'x'
        },
        'receivables_turnover': lambda d: {
            'value': (d.get('revenue', 0) / d.get('accounts_receivable', 1)) if d.get('accounts_receivable') else 0,
            'label': 'Receivables Turnover',
            'unit': 'x'
        },
        'conversion_rate': lambda d: {
            'value': ((d.get('conversions', 0) / d.get('visits', 1)) * 100) if d.get('visits') else 0,
            'label': 'Conversion Rate',
            'unit': '%'
        },
        'customer_acquisition_cost': lambda d: {
            'value': (d.get('marketing_cost', 0) / d.get('new_customers', 1)) if d.get('new_customers') else 0,
            'label': 'Customer Acquisition Cost',
            'unit': '$'
        },
        'customer_lifetime_value': lambda d: {
            'value': (d.get('avg_purchase', 0) * d.get('avg_purchases_per_year', 1) * d.get('avg_customer_lifespan', 1)) if all(k in d for k in ['avg_purchase', 'avg_purchases_per_year', 'avg_customer_lifespan']) else 0,
            'label': 'Customer Lifetime Value',
            'unit': '$'
        },
        'churn_rate': lambda d: {
            'value': ((d.get('churned_customers', 0) / d.get('total_customers', 1)) * 100) if d.get('total_customers') else 0,
            'label': 'Churn Rate',
            'unit': '%'
        },
        'employee_utilization': lambda d: {
            'value': (((d.get('billable_hours', 0) / (d.get('total_employees', 1) * d.get('hours_per_employee', 1))) * 100) if all(k in d for k in ['billable_hours', 'total_employees', 'hours_per_employee']) else 0),
            'label': 'Employee Utilization',
            'unit': '%'
        },
        'otoc_cycles': lambda d: {
            'receivables_days': 365 / (d.get('revenue', 1) / d.get('accounts_receivable', 1)) if d.get('accounts_receivable') and d.get('revenue') else 0,
            'inventory_days': 365 / (d.get('cogs', 1) / d.get('inventory', 1)) if d.get('inventory') and d.get('cogs') else 0,
            'payables_days': 365 / (d.get('cogs', 1) / d.get('accounts_payable', 1)) if d.get('accounts_payable') and d.get('cogs') else 0,
            'cash_conversion_cycle': 0
        },
    }

    if kpi_type == 'cash_conversion_cycle':
        result = kpi_functions['otoc_cycles'](data)
        result['cash_conversion_cycle'] = result['receivables_days'] + result['inventory_days'] - result['payables_days']
        return result

    if kpi_type not in kpi_functions:
        return {'error': f'Unknown KPI type: {kpi_type}'}

    result = kpi_functions[kpi_type](data)
    result['kpi_type'] = kpi_type
    result['value'] = round(result.get('value', 0), 2)

    return result


# =============================================================================
# ALERT GENERATION
# =============================================================================

def generate_alert(metric_name: str, value: float, threshold: float,
                  comparison: str = 'gt', severity: str = 'medium') -> Optional[Dict[str, Any]]:
    """
    Generate an alert if a threshold is breached.

    Args:
        metric_name: Name of the metric
        value: Current value
        threshold: Threshold value
        comparison: 'gt' (greater than), 'lt' (less than), 'eq' (equal)
        severity: 'critical', 'high', 'medium', 'low'

    Returns:
        Alert dict if threshold breached, None otherwise
    """
    breached = False
    if comparison == 'gt' and value > threshold:
        breached = True
    elif comparison == 'lt' and value < threshold:
        breached = True
    elif comparison == 'eq' and value == threshold:
        breached = True

    if not breached:
        return None

    return {
        'alert_type': 'threshold_breach',
        'metric': metric_name,
        'value': value,
        'threshold': threshold,
        'comparison': comparison,
        'severity': severity,
        'timestamp': datetime.now().isoformat(),
        'message': f"{metric_name} is {comparison} threshold: {value} vs {threshold}"
    }


def generate_anomaly_alert(metric_name: str, value: float, expected: Tuple[float, float],
                           z_score: float, severity: str = 'high') -> Dict[str, Any]:
    """
    Generate an alert for detected anomaly.

    Args:
        metric_name: Name of the metric
        value: Actual value
        expected: Tuple of (lower_bound, upper_bound)
        z_score: Z-score of the anomaly
        severity: 'critical', 'high', 'medium'

    Returns:
        Alert dict
    """
    return {
        'alert_type': 'anomaly_detected',
        'metric': metric_name,
        'value': value,
        'expected_range': expected,
        'z_score': z_score,
        'severity': severity,
        'timestamp': datetime.now().isoformat(),
        'message': f"Anomaly detected in {metric_name}: {value} outside expected range {expected} (z={z_score})"
    }


# =============================================================================
# COMPARATIVE ANALYSIS
# =============================================================================

def compare_entities(entity_data: Dict[str, Dict[str, float]],
                    metric: str) -> List[Dict[str, Any]]:
    """
    Compare multiple entities on a specific metric.

    Args:
        entity_data: Dict with entity_id -> {metrics}
        metric: Metric to compare

    Returns:
        Sorted list of entity comparisons
    """
    comparisons = []
    for entity_id, metrics in entity_data.items():
        if metric in metrics:
            comparisons.append({
                'entity_id': entity_id,
                'value': metrics[metric],
                'rank': 0  # Will be set after sorting
            })

    # Sort by value descending
    comparisons.sort(key=lambda x: x['value'], reverse=True)

    # Assign ranks
    for i, comp in enumerate(comparisons):
        comp['rank'] = i + 1

    return comparisons


def calculate_percentile(value: float, data: List[float]) -> float:
    """
    Calculate percentile rank of a value in a dataset.

    Args:
        value: Value to find percentile for
        data: Dataset to compare against

    Returns:
        Percentile (0-100)
    """
    if not data:
        return 0

    sorted_data = sorted(data)
    rank = sum(1 for x in sorted_data if x < value)
    return (rank / len(sorted_data)) * 100


# =============================================================================
# TIME SERIES ANALYSIS
# =============================================================================

def calculate_growth_rate(current: float, previous: float) -> Dict[str, Any]:
    """
    Calculate period-over-period growth rate.

    Args:
        current: Current period value
        previous: Previous period value

    Returns:
        Dict with growth rate and status
    """
    if previous == 0:
        growth_rate = 100 if current > 0 else 0 if current == 0 else -100
    else:
        growth_rate = ((current - previous) / abs(previous)) * 100

    return {
        'current': current,
        'previous': previous,
        'growth_rate': round(growth_rate, 2),
        'absolute_change': current - previous,
        'status': 'growth' if growth_rate > 0 else 'decline' if growth_rate < 0 else 'stable'
    }


def calculate_cagr(start_value: float, end_value: float, periods: int) -> float:
    """
    Calculate Compound Annual Growth Rate.

    Args:
        start_value: Starting value
        end_value: Ending value
        periods: Number of periods

    Returns:
        CAGR as percentage
    """
    if start_value == 0 or periods == 0:
        return 0

    cagr = (pow(end_value / start_value, 1 / periods) - 1) * 100
    return round(cagr, 2)


def project_future(data: List[float], periods: int = 3,
                   method: str = 'linear') -> List[float]:
    """
    Project future values based on historical data.

    Args:
        data: Historical time series
        periods: Number of periods to project
        method: 'linear' or 'moving_average'

    Returns:
        List of projected values
    """
    if method == 'moving_average':
        ma = calculate_moving_average(data, window=min(3, len(data)))
        # Use last valid MA as baseline and project with slight adjustment
        last_valid = next((x for x in reversed(ma) if x is not None), data[-1])
        last_trend = data[-1] - data[-2] if len(data) >= 2 else 0
        return [round(last_valid + last_trend * (i + 1), 2) for i in range(periods)]
    else:
        # Linear regression
        trend = calculate_trend(data)
        return [round(v, 2) for v in trend['forecast'][:periods]]


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

def generate_executive_summary(metrics: Dict[str, float],
                               benchmarks: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Generate an executive summary from key metrics.

    Args:
        metrics: Dict of key metric values
        benchmarks: Optional dict of benchmark/target values

    Returns:
        Comprehensive summary dict
    """
    summary = {
        'generated_at': datetime.now().isoformat(),
        'metrics': {},
        'alerts': [],
        'kpis': {},
        'overall_status': 'healthy'
    }

    # Process each metric
    for name, value in metrics.items():
        metric_summary = {
            'value': value,
            'status': 'normal'
        }

        # Check against benchmarks if provided
        if benchmarks and name in benchmarks:
            benchmark = benchmarks[name]
            variance = calculate_variance(benchmark, value)
            metric_summary['benchmark'] = benchmark
            metric_summary['variance'] = variance

            if variance['severity'] in ['high', 'critical']:
                metric_summary['status'] = variance['status']
                summary['alerts'].append({
                    'metric': name,
                    'type': 'variance',
                    'details': variance
                })

        summary['metrics'][name] = metric_summary

    # Calculate overall status
    if any(a['details']['severity'] == 'critical' for a in summary['alerts']):
        summary['overall_status'] = 'critical'
    elif any(a['details']['severity'] == 'high' for a in summary['alerts']):
        summary['overall_status'] = 'warning'

    # Add key ratios
    ratios = calculate_ratios(metrics)
    summary['ratios'] = {k: round(v, 2) for k, v in ratios.items()}

    # Add growth metrics if period data available
    if 'current_revenue' in metrics and 'previous_revenue' in metrics:
        summary['growth'] = calculate_growth_rate(
            metrics['current_revenue'],
            metrics['previous_revenue']
        )

    return summary
