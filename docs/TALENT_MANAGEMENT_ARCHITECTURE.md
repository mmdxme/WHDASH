# Talent Management Module - Architecture Guide
## WHDASH Enterprise Talent Management Platform

---

## 1. Module Vision & Design Philosophy

The Talent Management module is designed as an **enterprise-grade Talent Operating Platform** that integrates deeply with the entire WHDASH ecosystem. It surpasses SAP SuccessFactors in usability, operational clarity, talent visibility, succession practicality, manager actionability, multilingual experience, and dashboard quality.

### Design Principles
- **People-Development Driven**: Every feature focuses on employee growth and potential
- **Succession-Aware**: Critical roles and successor planning are first-class citizens
- **Competency-Based**: Skills and competencies form the foundation of all talent decisions
- **Manager-Friendly**: Department managers can manage their talent pipeline
- **Employee-Growth Friendly**: Employees can view their development path and career options
- **Audit-Safe**: Every change is logged with before/after values
- **Branch/Entity Aware**: Supports multi-entity, multi-branch organizations
- **Flow-Connected**: Talent events trigger workflow and notification flows
- **Multilingual**: Full support for 8 languages (EN, AR, FA, RU, HI, ES, ZH, DE)
- **RTL-Ready**: Full RTL support for Arabic and Persian interfaces

---

## 2. Database Architecture

### 2.1 Core Talent Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `tm_competencies` | Competency/Skill library | id, name, category, description, proficiency_levels, is_active |
| `tm_competency_categories` | Skill categories | id, name, description, parent_id, sort_order |
| `tm_employee_competencies` | Employee skill assessments | id, employee_id, competency_id, proficiency_level, assessed_by, assessment_date, expiry_date |
| `tm_talent_profiles` | Extended talent data | id, employee_id, potential_rating, readiness_level, career_interests, mobility_preference, last_reviewed |
| `tm_talent_pools` | Talent pool definitions | id, name, pool_type, description, criteria_json, owner_id, is_active |
| `tm_talent_pool_members` | Pool memberships | id, pool_id, employee_id, joined_date, exit_date, reason, status |
| `tm_critical_roles` | Critical position tracking | id, position_id, department_id, is_critical, criticality_level, backup_required |
| `tm_succession_plans` | Succession planning | id, critical_role_id, successor_id, readiness_level, relationship_type, development_needs, status |
| `tm_career_paths` | Career path definitions | id, from_position_id, to_position_id, path_type, is_approved, avg_duration_months |
| `tm_development_plans` | IDP records | id, employee_id, plan_year, status, manager_id, created_at, approved_at |
| `tm_development_goals` | Development goals | id, plan_id, goal_title, description, target_date, status, priority |
| `tm_development_actions` | IDP action items | id, goal_id, action_title, type, due_date, status, completed_at, linked_learning_id |
| `tm_talent_reviews` | Talent review cycles | id, cycle_name, period_start, period_end, status, participants, calibration_date |
| `tm_talent_review_participants` | Review participants | id, review_id, employee_id, manager_input, hr_input, final_rating, decision |
| `tm_talent_notes` | Talent annotations | id, employee_id, note_type, content, created_by, created_at |
| `tm_talent_history` | Talent audit trail | id, employee_id, field_name, old_value, new_value, changed_by, changed_at |
| `tm_mentoring_assignments` | Mentoring relationships | id, mentor_id, mentee_id, start_date, end_date, status, objectives |
| `tm_mobility_requests` | Internal mobility | id, employee_id, from_position, to_position, request_type, status, approved_by |
| `tm_talent_settings` | Configuration | id, setting_key, setting_value, category, updated_at |
| `tm_talent_audit_logs` | Audit trail | id, entity_type, entity_id, action, field_name, old_value, new_value, user_id, ip_address, created_at |

### 2.2 Entity Relationships

```
tm_competencies (1) ──────< tm_employee_competencies
        │
        └──< tm_competency_categories

hr_employees (1) ──────< tm_talent_profiles
        │
        ├──< tm_talent_pools >──────< tm_talent_pool_members
        │
        ├──< tm_critical_roles ──────< tm_succession_plans
        │
        ├──< tm_development_plans ───< tm_development_goals ───< tm_development_actions
        │
        ├──< tm_talent_reviews >──────< tm_talent_review_participants
        │
        ├──< tm_talent_notes
        ├──< tm_talent_history
        ├──< tm_mentoring_assignments
        └──< tm_mobility_requests

tm_career_paths (1) ──────< hr_positions (from/to)
```

---

## 3. Module Structure

### 3.1 Talent Management Menu / Navigation

```
Talent Management (Top-Level Module)
├─ Talent Dashboard              → /hr/talent/dashboard
├─ Executive Talent Dashboard    → /hr/talent/executive-dashboard
├─ Talent Workspace              → /hr/talent/workspace
├─ Talent Profiles
│  ├─ Employee Talent Profiles   → /hr/talent/profiles
│  ├─ Skills & Competencies     → /hr/talent/competencies
│  ├─ Potential Ratings         → /hr/talent/potential-ratings
│  ├─ Readiness Levels          → /hr/talent/readiness
│  ├─ Career Interests          → /hr/talent/career-interests
│  ├─ Mobility Preferences      → /hr/talent/mobility
│  ├─ Talent Notes             → /hr/talent/notes
│  ├─ Talent History           → /hr/talent/history
│  └─ Talent Reports           → /hr/talent/profile-reports
├─ Competency Framework
│  ├─ Competency Library       → /hr/talent/competency-library
│  ├─ Skill Categories        → /hr/talent/skill-categories
│  ├─ Role Competency Mapping  → /hr/talent/role-mapping
│  ├─ Skill Proficiency Levels → /hr/talent/proficiency-levels
│  ├─ Gap Analysis            → /hr/talent/gap-analysis
│  ├─ Certification Linkage   → /hr/talent/cert-linkage
│  ├─ Competency Reviews      → /hr/talent/competency-reviews
│  └─ Competency Reports      → /hr/talent/competency-reports
├─ Talent Pools
│  ├─ Talent Pool List        → /hr/talent/pools
│  ├─ Hi-Po Pool             → /hr/talent/pools/hipo
│  ├─ Successor Pool         → /hr/talent/pools/successor
│  ├─ Critical Role Pool     → /hr/talent/pools/critical
│  ├─ Future Leaders Pool     → /hr/talent/pools/future-leaders
│  ├─ Specialist Talent Pool  → /hr/talent/pools/specialist
│  ├─ Pool Criteria          → /hr/talent/pools/criteria
│  ├─ Pool Membership History → /hr/talent/pools/history
│  └─ Pool Reports           → /hr/talent/pool-reports
├─ Succession Planning
│  ├─ Critical Roles          → /hr/talent/critical-roles
│  ├─ Successor Mapping       → /hr/talent/successor-mapping
│  ├─ Bench Strength View    → /hr/talent/bench-strength
│  ├─ Readiness Levels       → /hr/talent/succession-readiness
│  ├─ Risk of Vacancy        → /hr/talent/vacancy-risk
│  ├─ Emergency Successors   → /hr/talent/emergency-successors
│  ├─ Long-Term Successors   → /hr/talent/longterm-successors
│  ├─ Succession Review Cycle → /hr/talent/succession-review
│  └─ Succession Reports     → /hr/talent/succession-reports
├─ Career & Mobility
│  ├─ Career Paths           → /hr/talent/career-paths
│  ├─ Promotion Paths       → /hr/talent/promotion-paths
│  ├─ Lateral Move Paths    → /hr/talent/lateral-paths
│  ├─ Internal Opportunities → /hr/talent/internal-opps
│  ├─ Transfer Requests      → /hr/talent/transfer-requests
│  ├─ Career Aspirations    → /hr/talent/aspirations
│  ├─ Mobility Readiness    → /hr/talent/mobility-readiness
│  └─ Career Reports        → /hr/talent/career-reports
├─ Development Planning
│  ├─ Individual Development Plans → /hr/talent/idp
│  ├─ Development Goals      → /hr/talent/dev-goals
│  ├─ Action Plans          → /hr/talent/action-plans
│  ├─ Mentoring / Coaching   → /hr/talent/mentoring
│  ├─ Stretch Assignments    → /hr/talent/stretch
│  ├─ Learning Linkage       → /hr/talent/dev-learning
│  ├─ Development Progress   → /hr/talent/dev-progress
│  ├─ Blockers / Risks      → /hr/talent/dev-blockers
│  └─ Development Reports   → /hr/talent/dev-reports
├─ Talent Reviews
│  ├─ Talent Review Cycles   → /hr/talent/review-cycles
│  ├─ Review Sessions       → /hr/talent/review-sessions
│  ├─ Manager Input         → /hr/talent/manager-input
│  ├─ HR Review            → /hr/talent/hr-review
│  ├─ Calibration          → /hr/talent/calibration
│  ├─ Talent Matrix        → /hr/talent/matrix
│  ├─ Review Notes         → /hr/talent/review-notes
│  ├─ Review Decisions     → /hr/talent/review-decisions
│  └─ Review Reports      → /hr/talent/review-reports
├─ Performance Linkage
│  ├─ Performance Summary   → /hr/talent/performance-summary
│  ├─ Goals Linkage        → /hr/talent/goals-linkage
│  ├─ Performance Trends   → /hr/talent/performance-trends
│  ├─ Talent vs Performance → /hr/talent/talent-vs-performance
│  ├─ High Performance Watchlist → /hr/talent/high-performers
│  ├─ Low Performance Risk → /hr/talent/low-perf-risk
│  ├─ Promotion Readiness  → /hr/talent/promotion-readiness
│  └─ Performance-Talent Reports → /hr/talent/perf-talent-reports
├─ Learning & Certification
│  ├─ Learning Plans        → /hr/talent/learning-plans
│  ├─ Certification Status  → /hr/talent/cert-status
│  ├─ Mandatory Learning    → /hr/talent/mandatory-learning
│  ├─ Development Learning Path → /hr/talent/dev-learning-path
│  ├─ Skill Gap Learning    → /hr/talent/skill-gap-learning
│  ├─ Readiness Improvement → /hr/talent/readiness-improvement
│  ├─ Expiry / Renewal     → /hr/talent/expiry-tracking
│  └─ Learning-Talent Reports → /hr/talent/learning-reports
├─ Workforce Capability
│  ├─ Bench Strength        → /hr/talent/bench-strength-view
│  ├─ Capability Heatmap    → /hr/talent/capability-heatmap
│  ├─ Leadership Pipeline   → /hr/talent/leadership-pipeline
│  ├─ Critical Skill Risk   → /hr/talent/skill-risk
│  ├─ Succession Coverage   → /hr/talent/succession-coverage
│  ├─ Talent Gaps           → /hr/talent/talent-gaps
│  ├─ Readiness by Role    → /hr/talent/readiness-by-role
│  ├─ Attrition Risk       → /hr/talent/attrition-risk
│  └─ Workforce Capability Reports → /hr/talent/workforce-reports
├─ Employee Experience Signals
│  ├─ Engagement Signals    → /hr/talent/engagement-signals
│  ├─ Pulse / Survey Linkage → /hr/talent/pulse-linkage
│  ├─ Retention Signals     → /hr/talent/retention-signals
│  ├─ Development Satisfaction → /hr/talent/dev-satisfaction
│  ├─ Recognition Linkage   → /hr/talent/recognition
│  ├─ Manager Feedback Themes → /hr/talent/manager-feedback
│  └─ Experience Reports   → /hr/talent/experience-reports
├─ Reports & Analytics
│  ├─ Talent Dashboard      → /hr/talent/reports/dashboard
│  ├─ Succession Dashboard  → /hr/talent/reports/succession
│  ├─ Development Dashboard → /hr/talent/reports/development
│  ├─ Competency Dashboard  → /hr/talent/reports/competency
│  ├─ Hi-Po Dashboard      → /hr/talent/reports/hipo
│  ├─ Mobility Dashboard   → /hr/talent/reports/mobility
│  ├─ Workforce Capability  → /hr/talent/reports/workforce
│  ├─ Branch / Entity      → /hr/talent/reports/branch
│  ├─ Custom Reports       → /hr/talent/reports/custom
│  └─ Export Center       → /hr/talent/export
├─ Workflow & Approvals
│  ├─ Approval Rules       → /hr/talent/approval-rules
│  ├─ Pending Approvals    → /hr/talent/pending
│  ├─ Escalations          → /hr/talent/escalations
│  ├─ Delegations          → /hr/talent/delegations
│  ├─ SLA Policies         → /hr/talent/sla
│  └─ Approval History    → /hr/talent/approval-history
└─ Settings
   ├─ Talent Settings       → /hr/talent/settings
   ├─ Competency Settings   → /hr/talent/settings/competency
   ├─ Succession Settings   → /hr/talent/settings/succession
   ├─ Talent Review Settings → /hr/talent/settings/review
   ├─ Development Plan Settings → /hr/talent/settings/development
   ├─ Mobility Settings    → /hr/talent/settings/mobility
   ├─ Output / Export Settings → /hr/talent/settings/export
   ├─ Branch / Entity Settings → /hr/talent/settings/branch
   ├─ Notification Settings → /hr/talent/settings/notifications
   └─ Translation / Label Settings → /hr/talent/settings/translations
```

---

## 4. Key Features by Area

### 4.1 Talent Dashboard
- Real-time talent metrics overview
- Quick actions for managers
- Alerts and notifications
- Recent talent activity feed
- Branch/Entity filtering
- Role-based widget composition

### 4.2 Executive Talent Dashboard
- CEO/CHRO level talent overview
- Succession risk indicators
- Hi-Po pipeline health
- Critical role coverage
- Talent spend vs productivity
- Board-ready talent reports

### 4.3 Talent Profiles
- Extended employee talent data
- Skills and competencies with proficiency levels
- Potential and readiness ratings
- Career interests and mobility preferences
- Development history timeline
- Talent notes and annotations
- Performance linkage
- Learning history linkage
- Full audit trail

### 4.4 Competency Framework
- Centralized competency library
- Skill categories with hierarchy
- Role-to-competency mapping
- Employee skill assessments
- Competency gap analysis
- Certification linkage
- Review history
- Competency reports

### 4.5 Talent Pools
- Pool creation and management
- Hi-Po Pool
- Successor Pool
- Critical Role Pool
- Future Leaders Pool
- Specialist Talent Pool
- Automatic and manual membership
- Pool analytics and reports
- Entry/exit history tracking

### 4.6 Succession Planning
- Critical roles identification
- Successor candidate mapping
- Multiple successor support (primary, secondary, emergency)
- Readiness levels (Ready Now, 6 months, 1 year, 2+ years, Not Ready)
- Vacancy risk assessment
- Development needs tracking
- Succession review cycles
- Succession reports and analytics
- Emergency successor management

### 4.7 Career & Mobility
- Career path definitions
- Promotion paths
- Lateral movement options
- Internal opportunity postings
- Transfer request workflow
- Career aspiration capture
- Mobility readiness assessment
- Department transfer support
- Role matching suggestions

### 4.8 Development Planning
- Individual Development Plan (IDP)
- SMART development goals
- Target competencies alignment
- Action steps with due dates
- Learning linkage (courses, certifications)
- Mentoring/coaching assignments
- Stretch assignments
- Progress tracking
- Blocker identification
- Manager visibility and approval
- Development reports

### 4.9 Talent Reviews
- Review cycle setup
- Participant management
- Manager input collection
- HR review and calibration
- Talent matrix (9-box or custom)
- Review notes and rationale
- Final decisions (promotion, development, retention)
- Approval workflow
- Review history

### 4.10 Performance Linkage
- Performance summary in talent profile
- Goal achievement tracking
- Performance trend analysis
- Performance vs Potential view
- High performer identification
- Low performer risk assessment
- Promotion readiness linkage
- Development actions from performance

### 4.11 Learning & Certification Linkage
- Development learning plans
- Certification tracking
- Readiness improvement learning
- Competency gap training suggestions
- Mandatory learning management
- Learning history in talent profile
- Expiry and renewal alerts
- Learning effectiveness tracking

### 4.12 Workforce Capability
- Bench strength by role/department
- Capability heatmaps
- Leadership pipeline visualization
- Critical skill risk assessment
- Succession coverage ratios
- Talent gaps identification
- Readiness distribution by role
- Branch/entity capability comparison
- Attrition risk indicators

### 4.13 Employee Experience Signals
- Engagement survey linkage
- Recognition tracking
- Development satisfaction metrics
- Retention risk indicators
- Manager feedback themes
- Employee growth feedback
- Team sentiment indicators

---

## 5. Reports & Analytics

### 5.1 Standard Reports
- Talent Profile Report
- Competency Gap Report
- Talent Pool Report
- Hi-Po Identification Report
- Succession Coverage Report
- Critical Role Successor Report
- Development Plan Report
- Development Progress Report
- Career Mobility Report
- Talent Review Report
- Workforce Capability Report
- Bench Strength Report
- Branch Talent Report
- Entity Talent Report
- Talent Risk Report
- Talent History Report
- Custom Report Builder

### 5.2 Dashboards
- Executive Talent Dashboard
- Succession Dashboard
- Development Dashboard
- Competency Dashboard
- Hi-Po Dashboard
- Mobility Dashboard
- Workforce Capability Dashboard
- Branch/Entity Talent Dashboard

### 5.3 Export Capabilities
- PDF reports
- Excel export with column selection
- CSV data export
- Printable views
- Scheduled report delivery
- Export configuration per report

---

## 6. Workflow Integration

### 6.1 Approval Workflows
- Talent pool membership changes
- Succession plan approvals
- Readiness rating changes
- Development plan approvals
- Promotion readiness approvals
- Talent review cycle approvals
- Mobility/transfer approvals

### 6.2 Flow Integration
- Talent review reminders via Flow
- Succession review notices via Flow
- Development plan reminders via Flow
- Critical talent risk alerts via Flow
- Mobility review notices via Flow
- Leadership review notifications via Flow
- Performance calibration alerts via Flow

### 6.3 SLA & Escalation
- Configurable SLA for approvals
- Escalation rules
- Delegation support
- Auto-escalation triggers
- SLA compliance tracking

---

## 7. Permissions & Security

### 7.1 Roles
| Role | Access Level |
|------|-------------|
| Global Admin | Full access to all talent functions |
| Talent Admin | Full talent management access |
| HR Manager | Manage talent pools, reviews, development |
| Talent Manager | Manage talent profiles, succession |
| Department Manager | View/manage team talent |
| Reviewer | Participate in talent reviews |
| Development Owner | Manage own development plans |
| Executive Viewer | Executive dashboards and reports |
| Employee Self-View | View own talent profile |
| Auditor | View-only audit and logs |

### 7.2 Access Control
- Module-level permissions
- Menu-level permissions
- Page-level permissions
- Action-level permissions (view, edit, approve, delete)
- Branch/Entity scope restrictions
- Field-level restrictions for sensitive data

### 7.3 Audit Trail
- Before/after values for critical changes
- Who changed what and when
- Approval history
- Review history
- Export action logging
- Login and access logging

---

## 8. Integration Points

### 8.1 Internal Module Integration
- HR (employee data, org structure)
- Recruitment (candidates to talent pipeline)
- Performance (reviews to talent decisions)
- Training/Learning (learning to development plans)
- Documents (talent documents, review packs)
- Workflow (approvals, notifications)
- Reports (BI integration)
- Flow (automation and notifications)

### 8.2 Data Flow
- Recruitment → Talent Pipeline → Talent Profiles
- Performance Reviews → Talent Ratings → Succession
- Training → Competencies → Development Plans
- Employee Profile → Org Structure → Career Paths

---

## 9. Technical Implementation

### 9.1 Routes Structure
All routes use the `/hr/talent/` prefix and follow RESTful conventions:
- GET /hr/talent/dashboard - Main dashboard
- GET /hr/talent/profiles - List talent profiles
- GET /hr/talent/profiles/<id> - View talent profile
- POST /hr/talent/profiles/<id>/update - Update talent profile
- GET /hr/talent/competencies - Competency management
- GET /hr/talent/pools - Talent pool list
- POST /hr/talent/pools - Create talent pool
- GET /hr/talent/succession - Succession planning
- POST /hr/talent/succession/plan - Create succession plan
- GET /hr/talent/development - Development plans
- POST /hr/talent/development/plan - Create IDP
- GET /hr/talent/reviews - Talent reviews
- POST /hr/talent/reviews/cycle - Create review cycle
- GET /hr/talent/reports - Reports center
- POST /hr/talent/export - Export data

### 9.2 Database Schema
- All tables use `tm_` prefix (Talent Management)
- Foreign keys to hr_employees for employee data
- JSON fields for flexible criteria and settings
- Audit fields on all tables (created_at, updated_at)
- Soft delete support where needed

### 9.3 Templates
- Follow existing WHDASH design patterns
- Use glass-panel styling
- Responsive layout
- RTL support via CSS classes
- Multilingual via t() function
- Chart.js for visualizations

---

## 10. Supported Languages

| Code | Language | Direction |
|------|----------|-----------|
| en | English | LTR |
| ar | Arabic | RTL |
| fa | Persian/Farsi | RTL |
| ru | Russian | LTR |
| hi | Hindi | LTR |
| es | Spanish | LTR |
| zh | Chinese | LTR |
| de | German | LTR |

All labels, menus, statuses, and content are translated.
