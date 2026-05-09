# File Management Permission Matrix

## Overview

This document defines the complete permission model for the File Management module, including role-based access control, folder-level permissions, and document-level permissions.

## Permission Structure

### Permission Levels

| Level | Code | Description |
|-------|------|-------------|
| View Only | `view` | Can view documents and folders |
| Read | `read` | Can view and download documents |
| Write | `write` | Can create, edit, upload documents |
| Manage | `manage` | Can manage folder structure |
| Full Control | `full_control` | Can manage permissions and delete |
| Admin | `admin` | Full system access |

### Resource Types

| Resource | Code | Description |
|----------|------|-------------|
| Files | `files` | Document file operations |
| Folders | `folders` | Folder management |
| Versions | `versions` | Version control |
| Check-in/Check-out | `checkin_checkout` | Lock management |
| Access Control | `access_control` | Permission management |
| Templates | `templates` | Template operations |
| Signatures | `signatures` | E-signature workflows |
| Reports | `reports` | Report generation |
| Audit | `audit` | Audit log access |

## Role Definitions

### System Roles

| Role | Description | Module Permissions |
|------|-------------|-------------------|
| Super Admin | Full system access | All permissions |
| Document Admin | Document management | files:*.*, folders:*.*, versions:*.*, templates:*.* |
| File Manager | File operations | files:read,write,view; folders:read,write,view |
| Department Manager | Department documents | files:read,write,view; folders:read,write,view (own dept) |
| Team Member | Basic file access | files:read,view; folders:read,view (shared) |
| Auditor | Read-only access | files:read; folders:read; reports:read; audit:read |
| Guest | External access | files:read (shared only) |

### Folder-Level Roles

| Role | Permissions |
|------|-------------|
| Owner | full_control on folder and contents |
| Editor | read_write on folder |
| Contributor | write on folder (create subfolders, upload) |
| Reviewer | read on folder and contents |
| Viewer | view on folder only |

## Permission Matrix

### Document Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| Create document | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| View document | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Edit document | ✓ | ✓ | ✓ | ✓ | Own only | ✗ |
| Delete document | ✓ | ✓ | Own only | Own dept | ✗ | ✗ |
| Download document | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Share document | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Archive document | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Restore document | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |

### Folder Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| Create folder | ✓ | ✓ | ✓ | ✓ | ✓ (limited) | ✗ |
| View folder | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Edit folder | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Delete folder | ✓ | ✓ | Own only | Own dept | ✗ | ✗ |
| Move folder | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Set permissions | ✓ | ✓ | Owner only | ✗ | ✗ | ✗ |
| View activity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Version Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| View versions | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Upload version | ✓ | ✓ | ✓ | ✓ | ✓ (checked-out) | ✗ |
| Set current | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Delete version | ✓ | ✓ | Own only | ✗ | ✗ | ✗ |
| Compare versions | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Check-in/Check-out Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| Check out | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Check in | ✓ | ✓ | ✓ | ✓ | Own locks | ✗ |
| Force unlock | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| View locks | ✓ | ✓ | ✓ | ✓ | Own only | ✓ |
| Lock overdue | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |

### Template Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| Create template | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Edit template | ✓ | ✓ | ✓ | Own dept | ✗ | ✗ |
| Delete template | ✓ | ✓ | Own only | ✗ | ✗ | ✗ |
| Generate doc | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

### Signature Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| Request signature | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Sign document | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Cancel signature | ✓ | ✓ | Own only | ✗ | ✗ | ✗ |
| View pending | ✓ | ✓ | ✓ | ✓ | Own only | ✓ |

### Report Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| View all reports | ✓ | ✓ | ✓ | Own dept | ✗ | ✓ |
| Export reports | ✓ | ✓ | ✓ | Own dept | ✗ | ✓ |
| Create custom | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |

### Audit Operations

| Action | Super Admin | Doc Admin | File Manager | Dept Manager | Team Member | Auditor |
|--------|-------------|-----------|--------------|--------------|-------------|---------|
| View audit log | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| View folder activity | ✓ | ✓ | ✓ | Own dept | Own | ✓ |
| Export audit log | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |

## Folder Permission Inheritance

### Inheritance Rules

1. **Root folders**: Require admin permission to create
2. **Subfolders**: Inherit parent permissions by default
3. **Override**: Explicit permissions override inherited ones
4. **Document permissions**: Can be more restrictive than folder, not more permissive

### Permission Propagation

```
Root Folder (admin:true)
├── Subfolder A (inherited: admin, editor, viewer)
│   ├── Subfolder A1 (explicit: editor) - overrides inherited
│   └── Subfolder A2 (inherited)
└── Subfolder B (explicit: editor, contributor)
```

## Confidentiality Levels

| Level | Code | Description | Viewable By |
|-------|------|-------------|-------------|
| Public | `public` | External sharing allowed | All authenticated users |
| Internal | `internal` | Company internal only | All employees |
| Department | `department` | Department only | Department members |
| Confidential | `confidential` | Restricted access | Explicitly permitted |
| Restricted | `restricted` | Highly sensitive | Owner + admin only |

## Visibility Levels

| Level | Description |
|-------|-------------|
| `private` | Owner only |
| `department` | Department members |
| `company` | All company employees |
| `public` | Anyone with link |

## Implementation

### Checking Permissions

```python
# Check folder access
if check_folder_access(user_id, folder_id, 'write'):
    # User can write to folder

# Check document permission
if document_has_permission(user_id, document_id, 'view'):
    # User can view document

# Check system permission
if user_has_permission(user_id, 'documents', 'files', 'admin'):
    # User is document admin
```

### Setting Folder Permissions

```python
# Add user permission
set_folder_permission(folder_id, user_id, 'read_write', expires_at=None)

# Remove user permission
remove_folder_permission(folder_id, user_id)

# Check effective permission
permission = get_effective_folder_permission(folder_id, user_id)
```

## Security Considerations

### Least Privilege
Always grant the minimum permissions needed for the role.

### Regular Review
Periodically review folder permissions for:
- Unused permissions
- Overly broad access
- Orphaned permissions (user no longer exists)

### Audit Trail
All permission changes are logged with:
- Who made the change
- What changed
- When it changed
- Before/after values

## API Endpoints

| Endpoint | Method | Permission |
|----------|--------|------------|
| `/documents/folder/<id>/permissions` | GET | `folders:read` |
| `/documents/folder/<id>/permissions` | POST | `access_control:manage` |
| `/documents/folder/<id>/permission/<uid>` | DELETE | `access_control:manage` |
| `/documents/<id>/share` | POST | `files:share` |
| `/documents/share/<id>/revoke` | POST | `files:share` |
