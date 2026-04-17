# File Management Audit and Governance

## Overview

The File Management module includes comprehensive audit logging and governance capabilities to ensure compliance, security, and accountability for all document-related activities.

## Audit Trail

### What's Logged

All significant actions are recorded in the audit system:

| Category | Events Logged |
|----------|---------------|
| Document | Create, View, Edit, Delete, Download, Share, Archive, Restore |
| Folder | Create, View, Edit, Delete, Move, Permission Change, Activity |
| Version | Upload, Set Current, Delete, Restore |
| Lock | Lock, Unlock, Force Unlock, Expiry |
| Signature | Request, Sign, Reject, Cancel |
| Access | Login, Logout, Permission Denied |

### Log Fields

Each audit record contains:

- `timestamp` - When the action occurred
- `user_id` - Who performed the action
- `action` - What was done
- `resource_type` - document, folder, version, etc.
- `resource_id` - ID of the affected resource
- `details` - Additional context (old/new values, IP address, etc.)
- `ip_address` - User's IP address
- `user_agent` - Browser/client information

### Audit Tables

#### `folder_activity_log`
```sql
CREATE TABLE folder_activity_log (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER,
    user_id INTEGER,
    action TEXT,
    details TEXT,
    ip_address TEXT,
    created_at DATETIME
);
```

#### `document_access_log`
```sql
CREATE TABLE document_access_log (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    user_id INTEGER,
    action TEXT,
    ip_address TEXT,
    user_agent TEXT,
    accessed_at DATETIME
);
```

## Governance Policies

### Document Retention

#### Retention Periods by Type

| Document Type | Retention Period | Action After Expiry |
|---------------|-----------------|-------------------|
| Contracts | 7 years | Review & Archive or Destroy |
| Financial Records | 7 years | Archive |
| Tax Documents | 7 years | Archive |
| HR Records | 5 years after termination | Destroy |
| Legal Documents | Permanent | Never Destroy |
| Operational Records | 3 years | Review & Archive |

#### Retention Actions

1. **Review Required** - Document flagged for review before action
2. **Archive** - Move to archive storage
3. **Destroy** - Secure deletion with audit trail
4. **Extend** - Extend retention period with justification

### Confidentiality Levels

| Level | Description | Sharing Rules |
|-------|-------------|---------------|
| Public | External sharing allowed | Anyone with link |
| Internal | Company internal | All authenticated users |
| Department | Department only | Department members |
| Confidential | Restricted access | Explicit permission required |
| Restricted | Highly sensitive | Owner + Admin only |

### Archive Rules

1. **Auto-Archive**: Documents older than defined threshold
2. **Manual Archive**: User-initiated with reason
3. **Legal Hold**: Preserve despite retention policy
4. **Immutable Archive**: Archived documents cannot be modified

## Compliance Features

### GDPR Compliance

- **Right to Access**: Users can view their data
- **Right to Rectification**: Data can be corrected
- **Right to Erasure**: Data can be deleted (with audit)
- **Data Portability**: Data export in standard formats
- **Consent Tracking**: Document consent records

### SOX Compliance

- **Access Controls**: Role-based access to financial docs
- **Audit Trail**: Complete history of changes
- **Change Management**: Version control with approval
- **Segregation of Duties**: Multiple approvers for critical actions

### ISO 27001 Alignment

- **Asset Management**: Document inventory
- **Access Control**: Permission management
- **Cryptography**: File encryption at rest
- **Incident Management**: Security incident logging
- **Compliance**: Regular audit reviews

## Security Controls

### File-Level Security

1. **File Encryption**: Files encrypted at rest
2. **Secure Download**: Time-limited download links
3. **Watermarking**: Documents watermarked on view
4. **DRM**: Digital rights management for sensitive docs

### Access Control

1. **Authentication**: User login required
2. **Authorization**: Permission-based access
3. **Session Management**: Timeout and re-auth
4. **IP Restrictions**: Optional IP allowlisting

### Monitoring

1. **Real-time Alerts**: Suspicious activity notifications
2. **Dashboard**: Security metrics overview
3. **Reports**: Access and activity reports
4. **Anomaly Detection**: Unusual pattern alerts

## Audit Log Access

### Who Can View Logs

| Role | Access Level |
|------|--------------|
| Super Admin | All logs, all users |
| Document Admin | All document/folder logs |
| Auditor | Read-only access |
| Department Manager | Own department logs |
| User | Own activity only |

### Log Retention

- **Active Logs**: 1 year online
- **Archived Logs**: 7 years offline
- **Critical Events**: Permanent retention

## Folder Activity Monitoring

### Activity Types

| Action | Description |
|--------|-------------|
| `view` | User viewed folder contents |
| `create` | Subfolder created |
| `upload` | Document uploaded |
| `edit` | Folder details modified |
| `delete` | Folder deleted/moved to trash |
| `restore` | Folder restored from trash |
| `permission_change` | Permissions modified |
| `share` | Folder shared |
| `move` | Folder moved to new parent |

### Activity Log API

```python
# Log folder activity
log_folder_activity(folder_id, user_id, 'view', details=None)

# Get folder activity
activities = get_all("""
    SELECT * FROM folder_activity_log
    WHERE folder_id = ?
    ORDER BY created_at DESC
""", (folder_id,))

# Get user activity
activities = get_all("""
    SELECT * FROM folder_activity_log
    WHERE user_id = ?
    ORDER BY created_at DESC
""", (user_id,))
```

## Document Access Logging

### Access Events

| Event | Logged |
|-------|--------|
| Document View | Yes |
| Document Download | Yes |
| Document Edit | Yes |
| Document Print | Yes (optional) |
| Failed Access | Yes |
| Permission Denied | Yes |

### Access Log Fields

```python
{
    'document_id': 123,
    'user_id': 456,
    'action': 'View',
    'ip_address': '192.168.1.100',
    'user_agent': 'Mozilla/5.0...',
    'accessed_at': '2024-01-15 10:30:00',
    'duration': 45,  # seconds
    'details': {}
}
```

## Governance Dashboard

### Key Metrics

1. **Total Documents**: Count of all documents
2. **Active Documents**: Currently active count
3. **Archived Documents**: Archived count
4. **Expiring Soon**: Documents expiring in 30 days
5. **Retention Compliance**: % compliant with policies
6. **Storage Used**: Total storage consumption

### Alert Types

| Alert | Trigger | Action |
|-------|---------|--------|
| Expiry Warning | 30 days before expiry | Notify owner |
| Expiry Critical | 7 days before expiry | Escalate to manager |
| Retention Breach | Past retention date | Flag for review |
| Unusual Access | Abnormal pattern detected | Security alert |
| Large File Upload | File > 100MB | Admin notification |

## Reporting

### Standard Reports

1. **Access Audit Report**: Who accessed what and when
2. **Retention Status Report**: Documents by retention stage
3. **Activity Summary**: User activity aggregation
4. **Compliance Report**: Policy adherence status
5. **Security Report**: Anomalies and incidents

### Custom Reports

Administrators can create custom reports with:
- Date range filters
- User/department filters
- Action type filters
- Resource type filters
- Export to CSV/Excel

## Best Practices

### For Administrators

1. **Review logs weekly** for suspicious activity
2. **Monitor retention** compliance monthly
3. **Update policies** annually or when regulations change
4. **Train users** on document handling procedures
5. **Backup logs** regularly to secure storage

### For Users

1. **Classify documents** correctly at creation
2. **Set appropriate permissions** before sharing
3. **Remove outdated documents** regularly
4. **Follow naming conventions** for easy discovery
5. **Report security incidents** immediately

### For Auditors

1. **Review access logs** for compliance testing
2. **Verify retention** policy enforcement
3. **Test permission** controls
4. **Validate audit trail** integrity
5. **Check user training** records

## Integration with Flow

Audit events can trigger Flow notifications:

```python
# Send notification on sensitive document access
if document.confidentiality == 'restricted':
    create_notification(
        user_id=document.owner_id,
        title='Restricted Document Accessed',
        message=f'{user.name} accessed {document.title}',
        type='security_alert'
    )
```

## Audit Log API

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/audit/log` | GET | Get audit logs |
| `/documents/audit/export` | GET | Export audit report |
| `/documents/folder/<id>/activity` | GET | Get folder activity |
| `/documents/report/access-audit` | GET | Access audit report |

### Query Parameters

- `start_date`: Filter from date
- `end_date`: Filter to date
- `user_id`: Filter by user
- `action`: Filter by action type
- `resource_type`: Filter by document/folder
- `resource_id`: Filter by specific resource

## Data Retention

### Log Retention Schedule

| Log Type | Online Retention | Offline Retention | Permanent |
|----------|-----------------|-------------------|-----------|
| Access Logs | 1 year | 6 years | No |
| Activity Logs | 1 year | 6 years | No |
| Security Logs | 1 year | 6 years | Critical only |
| Audit Reports | 1 year | 6 years | No |
| Compliance Docs | N/A | N/A | Yes |

### Document Retention Schedule

| Category | Retention | Archive | Destroy |
|----------|-----------|---------|---------|
| Contracts | 7 years | After expiry | After 10 years |
| Financial | 7 years | After 7 years | Never |
| HR | 5 years post-term | After 5 years | After 7 years |
| Legal | Permanent | N/A | Never |
| Operations | 3 years | After 3 years | After 7 years |
| Tax | 7 years | After 7 years | Never |

## Governance Review Process

### Monthly Review

1. Review expiring documents
2. Check retention compliance
3. Monitor storage usage
4. Review security alerts

### Quarterly Review

1. Audit access patterns
2. Review permission assignments
3. Update user training
4. Assess policy effectiveness

### Annual Review

1. Comprehensive compliance audit
2. Policy updates
3. Risk assessment
4. Governance reporting

## Appendix: SQL Queries

### Get Document Access History

```sql
SELECT dal.*, d.title, u.username
FROM document_access_log dal
JOIN documents d ON dal.document_id = d.id
JOIN users u ON dal.user_id = u.id
WHERE dal.document_id = ?
ORDER BY dal.accessed_at DESC;
```

### Get User Activity Summary

```sql
SELECT
    u.username,
    COUNT(DISTINCT dal.document_id) as docs_accessed,
    COUNT(dal.id) as total_accesses,
    MAX(dal.accessed_at) as last_access
FROM users u
LEFT JOIN document_access_log dal ON u.id = dal.user_id
WHERE dal.accessed_at > datetime('now', '-30 days')
GROUP BY u.id;
```

### Get Retention Compliance Status

```sql
SELECT
    d.title,
    d.expiry_date,
    CASE
        WHEN d.expiry_date < datetime('now') THEN 'EXPIRED'
        WHEN d.expiry_date < datetime('now', '+30 days') THEN 'EXPIRING SOON'
        ELSE 'ACTIVE'
    END as status
FROM documents d
WHERE d.archived = 0
ORDER BY d.expiry_date ASC;
```
