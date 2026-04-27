# Marketing Automation Architecture

## Overview

The WHDASH Marketing Automation module is built as an enterprise-grade marketing operating platform that extends the existing Marketing/Customer Intelligence/CRM infrastructure. It provides comprehensive capabilities for campaign management, lead nurturing, journey orchestration, and performance analytics.

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Marketing Automation Platform                 │
├─────────────────────────────────────────────────────────────────┤
│  Presentation Layer (Templates)                                  │
│  - Modern glass-panel UI with Tailwind CSS                      │
│  - RTL/LTR multilingual support (8 languages)                    │
│  - Responsive design for all devices                            │
├─────────────────────────────────────────────────────────────────┤
│  Business Logic Layer (Routes)                                  │
│  - Campaign lifecycle management                                 │
│  - Lead scoring engine                                          │
│  - Journey orchestration                                        │
│  - A/B testing framework                                        │
│  - Attribution & ROI calculation                                │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer (Models)                                            │
│  - 45+ SQLite tables                                            │
│  - Comprehensive seed data                                      │
│  - Audit logging                                                │
├─────────────────────────────────────────────────────────────────┤
│  Integration Layer                                              │
│  - CRM/Sales linkage                                            │
│  - Flow integration                                             │
│  - Workflow/Approval engine                                     │
│  - Export center                                                │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

#### Core Marketing Tables
- `marketing_campaigns` - Campaign master records
- `marketing_leads` - Lead/prospect management
- `marketing_customer_segments` - Audience segmentation
- `marketing_channels` - Multi-channel management
- `marketing_content` - Content library
- `marketing_offers` - Offers and promotions
- `marketing_budgets` - Budget planning

#### Lead Scoring Tables
- `marketing_lead_scoring_rules` - Configurable scoring rules
- `marketing_lead_scores` - Current lead scores
- `marketing_lead_score_history` - Score change tracking

#### Journey Automation Tables
- `marketing_nurture_journeys` - Journey definitions
- `marketing_journey_steps` - Step configurations
- `marketing_journey_participants` - Enrolled leads
- `marketing_journey_step_events` - Step execution logs

#### Testing & Optimization Tables
- `marketing_ab_tests` - A/B test definitions
- `marketing_ab_test_variants` - Variant tracking
- `marketing_journey_intelligence` - Customer journey data

#### Attribution & ROI Tables
- `marketing_attribution_models` - Attribution model configs
- `marketing_roi_metrics` - ROI calculations
- `marketing_funnel_tracking` - Funnel stage data

#### Operations Tables
- `marketing_templates` - Message templates
- `marketing_communications` - Delivery logs
- `marketing_channel_deliverability` - Deliverability metrics
- `marketing_notifications` - Alert system
- `marketing_sla_policies` - SLA definitions
- `marketing_sla_instances` - Active SLA tracking
- `marketing_export_configs` - Export configurations
- `marketing_activity_log` - Activity audit

## Key Features

### 1. Campaign Management
- Full lifecycle: Draft → Review → Approved → Scheduled → Active → Paused → Completed
- Multi-channel campaign support
- Budget tracking and approval workflow
- ROI calculation per campaign
- Calendar view for scheduling

### 2. Lead Scoring Engine
- **Demographic Scoring**: Industry, company size, job title, location
- **Behavioral Scoring**: Website visits, email engagement, content downloads
- **Engagement Scoring**: Campaign response, event attendance, form submissions
- Configurable rule weights
- MQL (Marketing Qualified Lead) and SQL (Sales Qualified Lead) thresholds
- Score history and trend analysis

### 3. Nurture Journeys
- Visual journey builder
- Multi-step automation flows
- Entry triggers: Segment join, form submit, score threshold, campaign enroll
- Delay and wait logic
- Branching and conditional paths
- Exit conditions and re-entry rules
- Performance metrics and analytics

### 4. A/B Testing Framework
- Subject line testing
- CTA testing
- Content variant testing
- Audience split testing
- Statistical significance calculation
- Winner determination
- Automated winner promotion

### 5. Customer Journey Intelligence
- Touchpoint tracking
- Journey stage mapping (Awareness → Consideration → Conversion → Retention → Advocacy)
- Engagement scoring
- Churn risk scoring
- Next Best Action recommendations
- Drop-off analysis

### 6. Channel Orchestration
- Email campaigns with delivery tracking
- SMS scaffolding
- WhatsApp integration scaffold
- Push notification support
- Social media linkage
- Delivery, open, click, bounce tracking
- Unsubscribed management

### 7. Attribution & ROI
- Multiple attribution models:
  - First Touch
  - Last Touch
  - Linear
  - Time Decay
  - Position Based (U-Shaped)
- Campaign-to-revenue tracking
- Channel attribution
- Cost per lead/acquisition
- Marketing ROI dashboard

### 8. Workflow & Approvals
- Campaign approval workflow
- Budget approval workflow
- Content approval queue
- SLA monitoring
- Escalation support
- Delegation capabilities

## Menu Structure

```
Marketing Automation
├─ Marketing Dashboard
├─ Campaigns
│  ├─ Campaign List
│  ├─ Lead Scoring
│  ├─ Nurture Journeys
│  ├─ A/B Testing
│  └─ Journey Intelligence
├─ ROI Dashboard
├─ Channel Deliverability
├─ Leads
├─ Segments
├─ Channels
├─ Content
├─ Assets Library
├─ Templates
├─ Funnel & Attribution
├─ Budgets
├─ Export Center
├─ Approvals
├─ SLA Monitoring
├─ Branch Marketing
├─ Notifications
├─ Reports
└─ Settings
```

## Integration Points

### CRM Integration
- Lead handoff to CRM
- Customer 360 marketing view
- Opportunity influence tracking
- Won/lost feedback loop

### Flow Integration
- Campaign approval notifications
- Urgent lead alerts
- Journey activation notices
- SLA breach alerts
- ROI review reminders

### Cross-Module Integration
- Social media scheduling
- Documents/asset management
- Workflow engine
- Reports/BI module

## Security Model

### Role-Based Access Control
- Marketing Admin
- Marketing Manager
- Campaign Manager
- Content Reviewer
- Lead Reviewer
- Sales Reviewer
- Executive Viewer
- Auditor

### Permission Categories
- Dashboard viewing
- Campaign management
- Lead management
- Channel management
- Content management
- Budget management
- Report access
- Settings management
- Approval authority

### Audit Trail
- All marketing changes logged
- Before/after values
- Actor tracking
- Timestamp recording
- Export action logging

## Technical Specifications

### Frontend
- Tailwind CSS for styling
- Chart.js for visualizations
- Font Awesome for icons
- Responsive design (mobile, tablet, desktop)
- RTL support for Arabic/Persian

### Backend
- Python/Flask
- SQLite database
- Blueprint-based routing
- Session-based authentication
- JSON APIs

### Performance
- Optimized queries with indexes
- Pagination for large datasets
- Lazy loading where appropriate
- Efficient seed data management

## Future Enhancements

1. **Advanced AI Scoring** - Machine learning-based lead scoring
2. **Real-time Journey Execution** - Event-driven automation
3. **Predictive Analytics** - Churn prediction, next best action
4. **Advanced Personalization** - Dynamic content customization
5. **Multi-tenant Architecture** - Branch-level isolation
6. **Advanced CRM Sync** - Bi-directional CRM integration
