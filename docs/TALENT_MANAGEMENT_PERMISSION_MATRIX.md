# Talent Management Permission Matrix

## Role Definitions

### Role: Global Admin
**Description**: Full system administrator with unrestricted access to all Talent Management functions.
- Access: All modules, pages, actions
- Permissions: view, edit, delete, approve, admin, export, audit

### Role: Talent Admin
**Description**: HR professional responsible for talent management configuration and oversight.
- Access: All talent modules
- Permissions: view, edit, approve, export, configure

### Role: HR Manager
**Description**: HR manager responsible for day-to-day HR operations including talent.
- Access: Talent profiles, pools, development, reviews
- Permissions: view, edit, approve (own department)

### Role: Talent Manager
**Description**: Dedicated talent management professional.
- Access: Talent profiles, succession, development, reviews
- Permissions: view, edit, configure

### Role: Department Manager
**Description**: Line manager responsible for team talent.
- Access: Team talent profiles, development plans, succession input
- Permissions: view (own team), edit (own team development)

### Role: Reviewer
**Description**: Participant in talent review processes.
- Access: Talent review cycles, calibration
- Permissions: view, submit_input

### Role: Development Owner
**Description**: Employee owning their own development plan.
- Access: Own talent profile, own IDP
- Permissions: view (self), edit (self development)

### Role: Executive Viewer
**Description**: C-level executive needing talent overview.
- Access: Executive dashboards, aggregate reports
- Permissions: view (executive summary only)

### Role: Employee Self-View
**Description**: Regular employee viewing own information.
- Access: Own talent profile (limited view)
- Permissions: view (self only)

### Role: Auditor
**Description**: Compliance and audit personnel.
- Access: Audit logs, reports
- Permissions: view_logs, export_audit

---

## Permission Matrix by Feature

### Talent Dashboard

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Dashboard | ✓ | ✓ | ✓ | ✓ | View Own |
| View Executive Dashboard | ✓ | ✓ | ✓ | - | - |
| View Metrics | ✓ | ✓ | ✓ | Team Only | - |
| View Recent Activity | ✓ | ✓ | ✓ | ✓ | Own Only |
| View Pending Approvals | ✓ | ✓ | ✓ | Team Only | - |

### Talent Profiles

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View All Profiles | ✓ | ✓ | ✓ | Team Only | Own Only |
| View Profile Detail | ✓ | ✓ | ✓ | Team Only | Limited |
| Edit Profile | ✓ | ✓ | Own Team | Team | Own Notes |
| Edit Potential/Readiness | ✓ | ✓ | - | - | - |
| Edit Career Interests | ✓ | ✓ | Own Team | Team | Own |
| Edit Mobility | ✓ | ✓ | Own Team | Team | Own |
| Delete Profile | ✓ | - | - | - | - |
| Export Profiles | ✓ | ✓ | ✓ | - | - |

### Talent Pools

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Pools | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create Pool | ✓ | ✓ | - | - | - |
| Edit Pool | ✓ | ✓ | - | - | - |
| Delete Pool | ✓ | - | - | - | - |
| Add Member | ✓ | ✓ | ✓ | - | Self-Nominate |
| Remove Member | ✓ | ✓ | ✓ | - | - |
| Approve Membership | ✓ | ✓ | Pool Owner | - | - |

### Succession Planning

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Critical Roles | ✓ | ✓ | ✓ | ✓ | - |
| Manage Critical Roles | ✓ | ✓ | - | - | - |
| View Successor Plans | ✓ | ✓ | ✓ | Own Team | - |
| Create Successor Plan | ✓ | ✓ | ✓ | - | - |
| Edit Successor Plan | ✓ | ✓ | ✓ | - | - |
| Approve Successor Plan | ✓ | ✓ | ✓ | - | - |
| Delete Successor Plan | ✓ | - | - | - | - |

### Development Plans

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View All Plans | ✓ | ✓ | Own Dept | Team | Own |
| View Plan Detail | ✓ | ✓ | Own Dept | Team | Own |
| Create Plan | ✓ | ✓ | Own Dept | Team | Request |
| Edit Plan | ✓ | ✓ | Own Dept | Team | Own Goals |
| Approve Plan | ✓ | ✓ | Manager | - | - |
| Add Goal | ✓ | ✓ | ✓ | ✓ | Own |
| Complete Action | ✓ | ✓ | ✓ | ✓ | Own |

### Talent Reviews

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Review Cycles | ✓ | ✓ | ✓ | Team | Own |
| Create Review Cycle | ✓ | ✓ | - | - | - |
| Edit Review Cycle | ✓ | ✓ | - | - | - |
| Submit Manager Input | ✓ | ✓ | ✓ | Team | - |
| Submit HR Input | ✓ | ✓ | HR Only | - | - |
| Calibrate | ✓ | ✓ | ✓ | - | - |
| Finalize Decisions | ✓ | ✓ | ✓ | - | - |

### Competencies

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Library | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manage Competencies | ✓ | ✓ | - | - | - |
| Assess Employee | ✓ | ✓ | Team | Team | Self |
| View Gap Analysis | ✓ | ✓ | ✓ | Team | Own |
| Export Gap Report | ✓ | ✓ | ✓ | - | - |

### Workforce Capability

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Bench Strength | ✓ | ✓ | ✓ | Team | - |
| View Capability Heatmap | ✓ | ✓ | ✓ | - | - |
| View Leadership Pipeline | ✓ | ✓ | ✓ | - | - |
| Export Capability Report | ✓ | ✓ | ✓ | - | - |

### Reports & Analytics

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View All Reports | ✓ | ✓ | ✓ | Team | Own |
| Create Custom Report | ✓ | ✓ | ✓ | - | - |
| Export Reports | ✓ | ✓ | ✓ | - | Limited |
| Schedule Reports | ✓ | ✓ | - | - | - |

### Settings

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Settings | ✓ | ✓ | - | - | - |
| Edit Settings | ✓ | ✓ | - | - | - |
| Manage Approval Rules | ✓ | ✓ | - | - | - |
| Manage Notifications | ✓ | ✓ | - | - | - |

### Audit

| Feature | Global Admin | Talent Admin | HR Manager | Dept Manager | Employee |
|---------|-------------|--------------|------------|--------------|----------|
| View Audit Logs | ✓ | ✓ | - | - | - |
| Export Audit Logs | ✓ | ✓ | - | - | - |
| View Change History | ✓ | ✓ | ✓ | Team | Own |

---

## Permission Scope Rules

### Department Scope
- HR Manager: Can view/edit employees in assigned departments only
- Department Manager: Can view/edit direct reports only

### Field-Level Restrictions
- Potential Rating: Editable by HR Manager and above only
- Readiness Level: Editable by HR Manager and above only
- Flight Risk Flag: Editable by Talent Admin and above only
- Hi-Po Flag: Editable by HR Manager and above only

### Action Restrictions
- Profile Deletion: Global Admin only
- Pool Deletion: Global Admin only
- Succession Plan Approval: Requires HR Manager sign-off
- Development Plan Approval: Requires direct manager approval

---

## Branch/Entity Access Control

### Multi-Entity Support
- Global Admin: Access to all entities
- Entity HR Manager: Access to employees within their entity
- Entity Department Manager: Access to team within their entity and entity

### Data Isolation
- Reports: Filtered by accessible entities
- Pools: Can be entity-specific or global
- Settings: Can be entity-specific or global

---

## Session & Security

### Session Management
- Session timeout: Configurable (default 30 minutes)
- Concurrent sessions: Limited by role
- MFA: Required for Admin roles

### Audit Logging
All permission-changed operations are logged with:
- User ID
- Action performed
- Timestamp
- IP address
- Before/after values
- Entity/Department scope
