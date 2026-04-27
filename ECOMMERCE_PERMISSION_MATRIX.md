# Marketing Automation Permission Matrix

## Overview

The Marketing Automation module implements a comprehensive Role-Based Access Control (RBAC) system that controls access at module, menu, page, and action levels. Permissions are managed through the `marketing_user_roles` table and evaluated using the `mkt_permission_required` decorator.

## Marketing Roles

### Role Definitions

| Role | Description | Access Level |
|------|-------------|--------------|
| Marketing Admin | Full administrative access to all marketing functions | All |
| Marketing Manager | Manages campaigns, leads, and team | Most functions |
| Campaign Manager | Focused on campaign execution | Campaign-focused |
| Content Reviewer | Reviews and approves content | Content only |
| Lead Reviewer | Manages leads and scoring | Lead-focused |
| Sales Reviewer | Views marketing data relevant to sales | Read-only |
| Executive Viewer | Executive dashboard access | Dashboard only |
| Auditor | Full audit trail access | Read-only audit |

## Permission Categories

### Dashboard Permissions
- `view_dashboard` - Access to marketing dashboard

### Campaign Permissions
- `view_campaigns` - View campaign list and details
- `create_campaigns` - Create new campaigns
- `edit_campaigns` - Edit existing campaigns
- `delete_campaigns` - Delete campaigns
- `approve_campaigns` - Approve campaign launch
- `launch_campaigns` - Launch active campaigns

### Lead Permissions
- `view_leads` - View lead list and details
- `create_leads` - Create new leads
- `edit_leads` - Edit existing leads
- `delete_leads` - Delete leads
- `assign_leads` - Assign leads to team members
- `convert_leads` - Convert leads to customers

### Segment Permissions
- `view_segments` - View segments
- `create_segments` - Create new segments
- `edit_segments` - Edit segments
- `delete_segments` - Delete segments
- `assign_segments` - Assign leads to segments

### Channel Permissions
- `view_channels` - View channel performance
- `manage_channels` - Manage channels

### Content Permissions
- `view_content` - View content library
- `create_content` - Create content
- `edit_content` - Edit content
- `approve_content` - Approve content

### Offer Permissions
- `view_offers` - View offers
- `create_offers` - Create offers
- `edit_offers` - Edit offers
- `approve_offers` - Approve special offers

### Budget Permissions
- `view_budgets` - View budgets
- `create_budgets` - Create budgets
- `edit_budgets` - Edit budgets
- `approve_budgets` - Approve budget allocation

### Report Permissions
- `view_reports` - Access all marketing reports
- `export_reports` - Export report data

### Settings Permissions
- `manage_settings` - Configure marketing settings
- `manage_roles` - Manage marketing role assignments

## Permission Matrix by Role

### Marketing Admin

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | ✓ | ✓ | ✓ | ✓ |
| Leads | ✓ | ✓ | ✓ | ✓ | ✓ |
| Segments | ✓ | ✓ | ✓ | ✓ | ✓ |
| Channels | ✓ | ✓ | ✓ | ✓ | ✓ |
| Content | ✓ | ✓ | ✓ | ✓ | ✓ |
| Offers | ✓ | ✓ | ✓ | ✓ | ✓ |
| Budgets | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reports | ✓ | - | - | - | ✓ |
| Settings | ✓ | - | ✓ | - | - |

### Marketing Manager

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | ✓ | ✓ | - | ✓ |
| Leads | ✓ | ✓ | ✓ | ✓ | - |
| Segments | ✓ | ✓ | ✓ | - | - |
| Channels | ✓ | ✓ | ✓ | - | - |
| Content | ✓ | ✓ | ✓ | - | ✓ |
| Offers | ✓ | ✓ | ✓ | - | ✓ |
| Budgets | ✓ | ✓ | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | ✓ | - | - | - | - |

### Campaign Manager

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | ✓ | ✓ | - | - |
| Leads | ✓ | ✓ | ✓ | - | - |
| Segments | ✓ | - | - | - | - |
| Channels | ✓ | - | - | - | - |
| Content | ✓ | ✓ | ✓ | - | - |
| Offers | ✓ | ✓ | ✓ | - | - |
| Budgets | ✓ | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | - | - | - | - | - |

### Content Reviewer

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | - | - | - | - |
| Leads | - | - | - | - | - |
| Segments | - | - | - | - | - |
| Channels | - | - | - | - | - |
| Content | ✓ | ✓ | ✓ | - | ✓ |
| Offers | - | - | - | - | - |
| Budgets | - | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | - | - | - | - | - |

### Lead Reviewer

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | - | - | - | - |
| Leads | ✓ | ✓ | ✓ | ✓ | - |
| Segments | ✓ | - | - | - | - |
| Channels | - | - | - | - | - |
| Content | - | - | - | - | - |
| Offers | - | - | - | - | - |
| Budgets | - | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | - | - | - | - | - |

### Sales Reviewer

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | - | - | - | - |
| Leads | ✓ | - | ✓ | - | - |
| Segments | ✓ | - | - | - | - |
| Channels | ✓ | - | - | - | - |
| Content | ✓ | - | - | - | - |
| Offers | ✓ | - | - | - | - |
| Budgets | ✓ | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | - | - | - | - | - |

### Executive Viewer

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | - | - | - | - |
| Leads | ✓ | - | - | - | - |
| Segments | ✓ | - | - | - | - |
| Channels | ✓ | - | - | - | - |
| Content | ✓ | - | - | - | - |
| Offers | ✓ | - | - | - | - |
| Budgets | ✓ | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | - | - | - | - | - |

### Auditor

| Function | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| Dashboard | ✓ | - | - | - | - |
| Campaigns | ✓ | - | - | - | - |
| Leads | ✓ | - | - | - | - |
| Segments | ✓ | - | - | - | - |
| Channels | ✓ | - | - | - | - |
| Content | ✓ | - | - | - | - |
| Offers | ✓ | - | - | - | - |
| Budgets | ✓ | - | - | - | - |
| Reports | ✓ | - | - | - | - |
| Settings | ✓ | - | - | - | - |

## Advanced Permissions

### Branch/Entity Scope
Permissions can be scoped to specific branches or entities:
- `branch_id` - Restrict access to specific branch
- `entity_scope` - Limit to specific entity types

### Field-Level Security
Sensitive fields can have restricted access:
- Budget visibility (Managers only)
- Cost data (Admin only)
- ROI calculations (Manager+)

### Time-Based Access
- Campaign access limited to campaign period
- Temporary role elevations
- Campaign-specific permissions

## Implementation

### Permission Decorator
```python
@mkt_permission_required('view_campaigns')
def campaigns_list():
    # Only users with view_campaigns permission can access
```

### Permission Evaluation
1. Check if user is Global Admin (bypass all)
2. Check marketing role permissions
3. Check specific permission for action
4. Check branch/entity scope
5. Return permission result

### Audit Logging
All permission-gated actions are logged:
```python
log_marketing_audit(db, 'campaign', id, 'UPDATE', actor_user_id=user['id'])
```

## Security Best Practices

1. **Principle of Least Privilege** - Grant minimum necessary permissions
2. **Role Separation** - Separate operational and approval roles
3. **Regular Review** - Audit role assignments quarterly
4. **Sensitive Data** - Restrict budget/cost visibility
5. **Audit Trail** - Log all permission-gated actions
