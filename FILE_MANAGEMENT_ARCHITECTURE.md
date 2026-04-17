# File Management Architecture

## Overview

The File Management module is an enterprise-grade Document Management System (DMS) integrated into the WHDASH ERP platform. It provides comprehensive file and folder management capabilities with hierarchical organization, version control, check-in/check-out, and deep integration with business records.

## Architecture Principles

### 1. File-Centric Design
- Every document is a first-class entity with metadata, versions, and relationships
- Files can exist independently or within folder structures
- Documents maintain links to business records (Assets, HR, Finance, etc.)

### 2. Folder Hierarchy
- Unlimited nested folder hierarchy
- Parent-child relationships with referential integrity
- Folder-level permissions that cascade to children
- Activity tracking at folder level

### 3. Integration Points
- **Navigation**: Menu system with full folder browsing capability
- **Permissions**: RBAC integration for access control
- **Flow**: Real-time notifications and workflow triggers
- **Translations**: 8-language support with RTL compatibility

## Database Schema

### Core Tables

#### `document_folders`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique identifier |
| folder_code | TEXT UNIQUE | Human-readable code (e.g., FLD-HR-001) |
| name | TEXT NOT NULL | Folder display name |
| description | TEXT | Optional description |
| folder_type | TEXT | Type classification |
| parent_id | INTEGER | Reference to parent folder (NULL for root) |
| owner_user_id | INTEGER | Folder owner |
| status | TEXT | Active/Archived |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `documents`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Unique identifier |
| document_code | TEXT UNIQUE | Human-readable code |
| title | TEXT NOT NULL | Document title |
| description | TEXT | Document description |
| document_type | TEXT | Type classification |
| folder_id | INTEGER | Parent folder (FK to document_folders) |
| category_id | INTEGER | Category reference |
| owner_user_id | INTEGER | Document owner |
| visibility | TEXT | visibility level |
| department | TEXT | Owning department |
| confidentiality | TEXT | Confidentiality classification |
| file_type | TEXT | File extension |
| file_size | INTEGER | Size in bytes |
| current_version_id | INTEGER | Current version reference |
| status | TEXT | Document status |
| archived | BOOLEAN | Archive flag |
| archived_at | DATETIME | Archive timestamp |
| expiry_date | DATETIME | Expiration date |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

#### `document_versions`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Version identifier |
| document_id | INTEGER | Parent document (FK) |
| version_number | INTEGER | Sequential version number |
| notes | TEXT | Version notes |
| file_path | TEXT | Server file path |
| file_name | TEXT | Original filename |
| mime_type | TEXT | MIME type |
| file_size | INTEGER | Size in bytes |
| uploaded_by_user_id | INTEGER | Uploader |
| uploaded_at | DATETIME | Upload timestamp |
| is_current | BOOLEAN | Current version flag |

#### `document_locks`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Lock identifier |
| document_id | INTEGER | Locked document (FK) |
| user_id | INTEGER | Lock owner |
| lock_type | TEXT | Lock type |
| reason | TEXT | Lock reason |
| locked_at | DATETIME | Lock timestamp |
| expires_at | DATETIME | Lock expiration |
| released_at | DATETIME | Release timestamp |

#### `folder_permissions`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Permission identifier |
| folder_id | INTEGER | Folder (FK) |
| user_id | INTEGER | User (FK) |
| permission_level | TEXT | read/write/admin/full_control |
| granted_by_user_id | INTEGER | Granting user |
| expires_at | DATETIME | Expiration |
| created_at | DATETIME | Grant timestamp |

## Module Structure

### Routes (`document_routes.py`)

| Route | Description |
|-------|-------------|
| `/documents/` | Main dashboard |
| `/documents/file-manager` | File manager with folder tree |
| `/documents/folders` | Folder tree view |
| `/documents/folder/<id>` | Folder detail |
| `/documents/folder/create` | Create folder API |
| `/documents/folder/<id>/edit` | Edit folder API |
| `/documents/folder/<id>/delete` | Delete folder API |
| `/documents/folder/<id>/permissions` | Folder permissions |
| `/documents/folder/<id>/activity` | Folder activity log |
| `/documents/<id>/preview` | Document preview |
| `/documents/<id>/checkout` | Check out document |
| `/documents/<id>/checkin` | Check in document |
| `/documents/<id>/lock` | Lock document |
| `/documents/<id>/unlock` | Unlock document |
| `/documents/<id>/versions` | Version history |
| `/documents/<id>/new-version` | Upload new version |
| `/documents/advanced-search` | Advanced search |
| `/documents/favorites` | User favorites |
| `/documents/quick-access` | Quick access items |
| `/documents/checkouts` | Checked out files |
| `/documents/workspace` | Personal workspace |
| `/documents/executive-dashboard` | Executive dashboard |
| `/documents/reports-center` | Reports hub |
| `/documents/report/*` | Various reports |

### Helper Functions (`document_models.py`)

#### Folder Management
- `generate_folder_code()` - Generate unique folder codes
- `get_folder_by_id()` - Get folder details
- `get_folder_tree()` - Get hierarchical tree
- `get_folder_path()` - Get breadcrumb path
- `get_folder_children()` - Get subfolders
- `get_folder_documents()` - Get folder contents
- `get_folder_stats()` - Get folder statistics
- `get_user_root_folders()` - Get user's root folders

#### Permissions
- `check_folder_access()` - Check user access
- `log_folder_activity()` - Log folder activity
- `get_folder_permitted_users()` - Get permitted users
- `set_folder_permission()` - Set folder permission
- `remove_folder_permission()` - Remove permission

#### Check-in/Check-out
- `get_document_lock()` - Get document lock
- `lock_document()` - Lock document
- `unlock_document()` - Unlock document
- `get_user_locks()` - Get user's locks
- `get_overdue_locks()` - Get expired locks

#### Search
- `search_documents_advanced()` - Advanced search
- `save_search()` - Save search query
- `get_user_saved_searches()` - Get saved searches
- `execute_saved_search()` - Execute saved search

#### Quick Access & Favorites
- `get_user_favorites()` - Get user favorites
- `get_user_quick_access()` - Get quick access items
- `update_quick_access()` - Update quick access
- `add_document_favorite()` - Add to favorites
- `remove_document_favorite()` - Remove from favorites
- `is_document_favorited()` - Check if favorited

## Integration

### Navigation Integration
The Documents menu is defined in `navigation.py` with the following structure:
- Dashboard
- Executive Dashboard
- File Manager
- My Workspace
- All Documents
- Folders
- My Documents
- Favorites
- Quick Access
- Shared with Me
- Recent
- Checked Out
- Archived
- Pending Signature
- Signed
- Templates
- Generated Documents
- Signature Requests
- Advanced Search
- Reports Center
- Audit Logs
- Settings

### Permission Integration
Permissions are checked via `user_has_permission()` from the permissions module:
- Module: `documents`
- Resources: `files`, `folders`, `versions`, `checkin_checkout`, `access_control`
- Actions: `view`, `create`, `edit`, `delete`, `admin`, `manage`

### Flow Integration
Flow notifications are sent for:
- Document share events
- Check-out reminders
- Signature requests
- Approval notifications
- Retention alerts

## Security

### Access Control Layers
1. **Module Level**: User must have document module access
2. **Menu Level**: Navigation items respect permissions
3. **Folder Level**: Folder permissions control tree visibility
4. **Document Level**: Document permissions control individual access
5. **Action Level**: Specific actions require specific permissions

### Audit Trail
All significant actions are logged:
- Document uploads/downloads
- Folder creation/modification/deletion
- Permission changes
- Check-in/check-out events
- Document sharing
- Metadata changes

## Performance Considerations

### Database Indexes
Key indexes for performance:
- `idx_documents_folder` - Fast folder content queries
- `idx_documents_owner` - Quick owner lookups
- `idx_documents_status` - Status filtering
- `idx_folder_permissions_user` - Permission checks
- `idx_folder_activity_user` - Activity logging

### Query Optimization
- Folder tree loaded lazily (AJAX)
- Document lists paginated
- Quick access items cached
- Search uses indexed columns
