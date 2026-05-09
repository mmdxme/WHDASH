"""
BI Flow Integration Module
Provides integration between BI/Reporting and Flow communication platform.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from flow_models import (
        send_message,
        create_notification,
        get_or_create_private_conversation,
        generate_id,
        get_db_context,
    )
    FLOW_AVAILABLE = True
except ImportError:
    FLOW_AVAILABLE = False
    logger.warning("Flow models not available - BI Flow integration disabled")


def get_flow_channel_id(bi_user_id, channel_name):
    """Get or create a Flow channel for BI notifications."""
    if not FLOW_AVAILABLE:
        return None
    
    channel_id = f"bi_{channel_name.lower().replace(' ', '_')}_{bi_user_id}"
    return channel_id


def share_report_to_flow(report_name, report_url, shared_by, recipients=None):
    """
    Share a BI report to Flow.
    
    Args:
        report_name: Name of the report
        report_url: URL to access the report
        shared_by: User ID who is sharing
        recipients: List of user IDs to notify (optional)
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        logger.warning("Cannot share report - Flow not available")
        return False
    
    try:
        message_content = (
            f"📊 **Report Shared: {report_name}**\n\n"
            f"User **{shared_by}** has shared a BI report with you.\n\n"
            f"**Report:** {report_name}\n"
            f"**Link:** {report_url}\n\n"
            f"_Shared via Business Intelligence Module_"
        )
        
        conversation_id = get_or_create_private_conversation(shared_by, 'system')
        send_message(
            conversation_id=conversation_id,
            sender_id=shared_by,
            content=message_content,
            message_type='text',
            metadata={
                'type': 'bi_report_share',
                'report_name': report_name,
                'report_url': report_url,
            }
        )
        
        if recipients:
            for recipient_id in recipients:
                notif_content = f"BI report '{report_name}' has been shared with you by {shared_by}"
                create_notification(
                    user_id=recipient_id,
                    title=f"Report Shared: {report_name}",
                    message=notif_content,
                    notification_type='bi_report',
                    source_module='bi',
                    reference_id=report_url,
                )
        
        logger.info(f"Report '{report_name}' shared to Flow by {shared_by}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to share report to Flow: {e}")
        return False


def send_bi_alert_to_flow(alert_name, alert_message, severity, recipients=None, channel_id=None):
    """
    Send a BI alert notification to Flow.
    
    Args:
        alert_name: Name of the alert
        alert_message: Alert message content
        severity: Alert severity (low, medium, high, critical)
        recipients: List of user IDs to notify
        channel_id: Flow channel ID to post to (optional)
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        logger.warning("Cannot send alert - Flow not available")
        return False
    
    severity_icons = {
        'low': 'ℹ️',
        'medium': '⚠️',
        'high': '🔶',
        'critical': '🚨'
    }
    
    try:
        icon = severity_icons.get(severity.lower(), '📊')
        
        message_content = (
            f"{icon} **BI Alert: {alert_name}**\n\n"
            f"**Severity:** {severity.upper()}\n\n"
            f"{alert_message}\n\n"
            f"_This is an automated alert from the Business Intelligence Module_"
        )
        
        conversation_id = get_or_create_private_conversation('system', 'system')
        send_message(
            conversation_id=conversation_id,
            sender_id='system',
            content=message_content,
            message_type='text',
            metadata={
                'type': 'bi_alert',
                'alert_name': alert_name,
                'severity': severity,
            }
        )
        
        if recipients:
            for recipient_id in recipients:
                create_notification(
                    user_id=recipient_id,
                    title=f"BI Alert: {alert_name}",
                    message=alert_message,
                    notification_type='bi_alert',
                    source_module='bi',
                    priority=severity,
                )
        
        logger.info(f"BI alert '{alert_name}' sent to Flow")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send BI alert to Flow: {e}")
        return False


def send_scheduled_report_to_flow(schedule_name, report_url, recipients, attachment_info=None):
    """
    Send a scheduled report delivery notification to Flow.
    
    Args:
        schedule_name: Name of the report schedule
        report_url: URL to access the report
        recipients: List of user IDs to notify
        attachment_info: Dict with attachment details (filename, format, size)
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        logger.warning("Cannot send scheduled report - Flow not available")
        return False
    
    try:
        attachment_text = ""
        if attachment_info:
            attachment_text = (
                f"**Attachment:** {attachment_info.get('filename', 'Report')}\n"
                f"**Format:** {attachment_info.get('format', 'Unknown')}\n"
                f"**Size:** {attachment_info.get('size', 'Unknown')}\n\n"
            )
        
        message_content = (
            f"📅 **Scheduled Report Delivered: {schedule_name}**\n\n"
            f"{attachment_text}"
            f"**Report:** {schedule_name}\n"
            f"**Access:** {report_url}\n\n"
            f"_This report was automatically generated and delivered via the BI Scheduler_"
        )
        
        conversation_id = get_or_create_private_conversation('system', 'system')
        send_message(
            conversation_id=conversation_id,
            sender_id='system',
            content=message_content,
            message_type='text',
            metadata={
                'type': 'bi_scheduled_report',
                'schedule_name': schedule_name,
                'report_url': report_url,
            }
        )
        
        for recipient_id in recipients:
            create_notification(
                user_id=recipient_id,
                title=f"Scheduled Report: {schedule_name}",
                message=f"Your scheduled report is ready",
                notification_type='bi_schedule',
                source_module='bi',
            )
        
        logger.info(f"Scheduled report '{schedule_name}' notification sent to Flow")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send scheduled report notification to Flow: {e}")
        return False


def create_bi_digest_for_flow(user_id, digest_data):
    """
    Create a daily/weekly BI digest to post to Flow.
    
    Args:
        user_id: User ID to send digest to
        digest_data: Dict containing:
            - kpis: List of KPI summaries
            - alerts: List of active alerts
            - reports: List of recently run reports
            - date_range: Reporting period
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        return False
    
    try:
        kpis = digest_data.get('kpis', [])
        alerts = digest_data.get('alerts', [])
        recent_reports = digest_data.get('reports', [])
        date_range = digest_data.get('date_range', 'Today')
        
        kpi_text = ""
        if kpis:
            kpi_text = "**Top KPIs:**\n"
            for kpi in kpis[:5]:
                kpi_text += f"- {kpi.get('name', 'Unknown')}: {kpi.get('value', 'N/A')}\n"
        
        alerts_text = ""
        if alerts:
            alerts_text = "\n**Active Alerts:**\n"
            for alert in alerts[:5]:
                alerts_text += f"- ⚠️ {alert.get('name', 'Unknown')}: {alert.get('message', 'N/A')}\n"
        
        reports_text = ""
        if recent_reports:
            reports_text = "\n**Recent Reports:**\n"
            for report in recent_reports[:5]:
                reports_text += f"- 📊 {report.get('name', 'Unknown')} ({report.get('run_count', 0)} runs)\n"
        
        message_content = (
            f"📈 **BI Digest - {date_range}**\n\n"
            f"{kpi_text}"
            f"{alerts_text}"
            f"{reports_text}\n"
            f"_View your full BI Dashboard: /bi/dashboard_"
        )
        
        conversation_id = get_or_create_private_conversation('system', user_id)
        send_message(
            conversation_id=conversation_id,
            sender_id='system',
            content=message_content,
            message_type='text',
            metadata={
                'type': 'bi_digest',
                'date_range': date_range,
            }
        )
        
        logger.info(f"BI digest sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send BI digest to Flow: {e}")
        return False


def post_kpi_update_to_flow(kpi_name, current_value, target_value, trend, channel_id=None):
    """
    Post a KPI update to a Flow channel.
    
    Args:
        kpi_name: Name of the KPI
        current_value: Current KPI value
        target_value: Target value
        trend: Trend direction (up, down, stable)
        channel_id: Flow channel ID to post to
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        return False
    
    trend_icons = {
        'up': '📈',
        'down': '📉',
        'stable': '➡️'
    }
    
    try:
        icon = trend_icons.get(trend.lower(), '➡️')
        variance = ((current_value - target_value) / target_value * 100) if target_value else 0
        
        message_content = (
            f"{icon} **KPI Update: {kpi_name}**\n\n"
            f"**Current:** {current_value:,.2f}\n"
            f"**Target:** {target_value:,.2f}\n"
            f"**Variance:** {variance:+.1f}%\n"
            f"**Trend:** {trend.upper()}\n\n"
            f"_Auto-posted from BI Module_"
        )
        
        conversation_id = get_or_create_private_conversation('system', 'system')
        send_message(
            conversation_id=conversation_id,
            sender_id='system',
            content=message_content,
            message_type='text',
            metadata={
                'type': 'kpi_update',
                'kpi_name': kpi_name,
            }
        )
        
        logger.info(f"KPI update for '{kpi_name}' posted to Flow")
        return True
        
    except Exception as e:
        logger.error(f"Failed to post KPI update to Flow: {e}")
        return False


def notify_report_execution_to_flow(report_name, executed_by, execution_time, row_count, status):
    """
    Notify Flow when a report is executed.
    
    Args:
        report_name: Name of the executed report
        executed_by: User ID who ran the report
        execution_time: Time taken to execute (seconds)
        row_count: Number of rows returned
        status: Execution status (success, failed, timeout)
    
    Returns:
        bool: Success status
    """
    if not FLOW_AVAILABLE:
        return False
    
    status_icons = {
        'success': '✅',
        'failed': '❌',
        'timeout': '⏱️'
    }
    
    try:
        icon = status_icons.get(status.lower(), '📊')
        
        message_content = (
            f"{icon} **Report Executed: {report_name}**\n\n"
            f"**User:** {executed_by}\n"
            f"**Rows:** {row_count:,}\n"
            f"**Time:** {execution_time:.2f}s\n"
            f"**Status:** {status.upper()}\n\n"
            f"_Logged by BI Module_"
        )
        
        conversation_id = get_or_create_private_conversation('system', 'system')
        send_message(
            conversation_id=conversation_id,
            sender_id='system',
            content=message_content,
            message_type='text',
            metadata={
                'type': 'report_execution',
                'report_name': report_name,
                'status': status,
            }
        )
        
        logger.info(f"Report execution logged to Flow: {report_name} by {executed_by}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to notify report execution to Flow: {e}")
        return False


# ============================================================================
# Flow Integration API Endpoints for BI
# ============================================================================

def register_bi_flow_routes(app):
    """Register Flow integration routes with the Flask app."""
    
    @app.route('/bi/api/flow/share', methods=['POST'])
    def bi_flow_share():
        """API endpoint to share a report to Flow."""
        from flask import request, jsonify
        from routes import require_login
        
        @require_login
        def inner():
            data = request.get_json()
            report_name = data.get('report_name')
            report_url = data.get('report_url')
            recipients = data.get('recipients', [])
            
            success = share_report_to_flow(
                report_name=report_name,
                report_url=report_url,
                shared_by=session.get('user_id', 'unknown'),
                recipients=recipients
            )
            
            return jsonify({'success': success})
        
        return inner()
    
    @app.route('/bi/api/flow/alert', methods=['POST'])
    def bi_flow_alert():
        """API endpoint to send a BI alert to Flow."""
        from flask import request, jsonify
        from routes import require_login
        
        @require_login
        def inner():
            data = request.get_json()
            alert_name = data.get('alert_name')
            alert_message = data.get('alert_message')
            severity = data.get('severity', 'medium')
            recipients = data.get('recipients', [])
            
            success = send_bi_alert_to_flow(
                alert_name=alert_name,
                alert_message=alert_message,
                severity=severity,
                recipients=recipients
            )
            
            return jsonify({'success': success})
        
        return inner()
    
    @app.route('/bi/api/flow/digest', methods=['POST'])
    def bi_flow_digest():
        """API endpoint to send a BI digest to Flow."""
        from flask import request, jsonify
        from routes import require_login
        
        @require_login
        def inner():
            data = request.get_json()
            user_id = data.get('user_id', session.get('user_id'))
            digest_data = data.get('digest_data', {})
            
            success = create_bi_digest_for_flow(
                user_id=user_id,
                digest_data=digest_data
            )
            
            return jsonify({'success': success})
        
        return inner()