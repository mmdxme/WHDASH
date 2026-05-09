# Marketing Automation Sample Data Guide

## Overview

The Marketing Automation module includes comprehensive seed data to demonstrate functionality and provide realistic starting points for each feature area. Sample data is automatically created when running database migrations.

## Seed Data Tables

### 1. Marketing Settings (`marketing_settings`)

Default configuration settings:
- Lead scoring thresholds (MQL: 50, SQL: 80)
- Attribution model defaults
- Channel configurations
- Notification preferences
- Date/time formats
- Currency settings

### 2. Lead Sources (`marketing_lead_sources`)

| Code | Name | Type | Status |
|------|------|------|--------|
| LS-WEB | Website | digital | Active |
| LS-SOC | Social Media | digital | Active |
| LS-REF | Referral | referral | Active |
| LS-EVT | Event | event | Active |
| LS-PART | Partner | partner | Active |
| LS-AD | Advertisement | advertising | Active |
| LS-EM | Email Campaign | email | Active |
| LS-COLD | Cold Outreach | outbound | Active |

### 3. Marketing Channels (`marketing_channels`)

| Name | Code | Type | Status |
|------|------|------|--------|
| Email Marketing | CH-EMAIL | email | Active |
| SMS Campaigns | CH-SMS | sms | Active |
| WhatsApp | CH-WHATS | whatsapp | Active |
| Push Notifications | CH-PUSH | push | Active |
| Facebook Ads | CH-FB | social | Active |
| Instagram | CH-IG | social | Active |
| LinkedIn | CH-LI | social | Active |
| Google Ads | CH-GOOGLE | advertising | Active |
| Website/Blog | CH-WEB | digital | Active |
| Trade Shows | CH-TRADE | event | Active |

### 4. Funnel Stages (`marketing_funnel_stages`)

| Name | Stage Order | Probability |
|------|-------------|-------------|
| Prospect Identified | 1 | 10% |
| Initial Contact | 2 | 20% |
| Qualification | 3 | 35% |
| Proposal | 4 | 50% |
| Negotiation | 5 | 70% |
| Closed Won | 6 | 100% |
| Closed Lost | 7 | 0% |

### 5. Seasonality Data (`marketing_seasonality`)

| Name | Type | Period | Peak |
|------|------|--------|------|
| Peak Sales Season | peak | Jan-Mar | Yes |
| Ramadan Pre-Season | pre_ramadan | Feb | No |
| Ramadan Season | ramadan | Mar-Apr | Yes |
| Post-Ramadan/Eid | eid | Apr | Yes |
| Summer Season | summer | Jun-Aug | No |
| Back to School | back_to_school | Aug-Sep | No |
| Year End | year_end | Nov-Dec | No |
| Low Season | low | May | No |

### 6. Marketing Roles (`marketing_roles`)

| Name | Description | Status |
|------|-------------|--------|
| Marketing Admin | Full access | Active |
| Marketing Manager | Team management | Active |
| Campaign Manager | Campaign execution | Active |
| Content Reviewer | Content approval | Active |
| Lead Reviewer | Lead management | Active |
| Sales Reviewer | Sales alignment | Active |
| Executive Viewer | Dashboard access | Active |
| Auditor | Audit trail | Active |

### 7. Lead Scoring Rules (`marketing_lead_scoring_rules`)

| Rule Name | Category | Type | Score |
|-----------|----------|------|-------|
| Auto Parts Industry | demographic | positive | 20 |
| Manufacturing | demographic | positive | 15 |
| Retail Business | demographic | positive | 10 |
| Small Business | demographic | negative | -5 |
| Enterprise | demographic | positive | 25 |
| Website Visit 3+ | behavioral | positive | 15 |
| Email Open | behavioral | positive | 5 |
| Form Submit | behavioral | positive | 20 |
| Campaign Response | engagement | positive | 25 |
| Event Attendance | engagement | positive | 30 |
| No Activity 30d | engagement | negative | -10 |
| Unsubscribe | engagement | negative | -30 |

### 8. Attribution Models (`marketing_attribution_models`)

| Name | Type | Default | Description |
|------|------|---------|-------------|
| First Touch | first_touch | Yes | 100% credit to first touchpoint |
| Last Touch | last_touch | No | 100% credit to last touchpoint |
| Linear | linear | No | Equal credit across all touchpoints |
| Time Decay | time_decay | No | More credit to recent touchpoints |
| Position Based | position_based | No | 40% first, 20% last, 40% middle |

### 9. SLA Policies (`marketing_sla_policies`)

| Policy Name | Type | Priority | Response Time |
|-------------|------|----------|---------------|
| Lead Response | lead_response | High | 4 hours |
| Campaign Approval | campaign_approval | Medium | 24 hours |
| Content Approval | content_approval | Medium | 48 hours |
| Offer Response | offer_response | High | 8 hours |

### 10. Marketing Templates (`marketing_templates`)

**Email Templates:**
| Name | Type | Subject |
|------|------|---------|
| Welcome Email | welcome | Welcome to {{brand_name}}! |
| Newsletter | newsletter | Your Monthly Update |
| Promotion | promotional | Special Offer Inside |
| Follow-up | followup | Following Up on Your Inquiry |

**SMS Templates:**
| Name | Type |
|------|------|
| Appointment Reminder | reminder | Your appointment is tomorrow at {{time}} |
| Flash Sale | promotional | Flash sale! {{discount}}% off today only |
| Cart Abandonment | recovery | You left something behind |

**WhatsApp Templates:**
| Name | Type |
|------|------|
| Order Confirmation | transactional | Your order #{{order_id}} is confirmed |
| Shipping Update | transactional | Your order is on the way! |
| Re-engagement | promotional | We miss you! {{offer}} |

### 11. Export Configurations (`marketing_export_configs`)

| Name | Entity | Format |
|------|--------|--------|
| Campaign Export Standard | campaign | CSV |
| Lead Export Standard | lead | CSV |
| Segment Export | segment | CSV |
| Channel Performance Export | channel | Excel |
| Journey Performance Export | journey | Excel |
| ROI Summary Export | roi | Excel |
| Attribution Export | attribution | CSV |

### 12. Sample Lead Scores (`marketing_lead_scores`)

Generated for existing leads:
- Total Score: 0-100
- Demographic Score: 10-40
- Behavioral Score: 5-35
- Engagement Score: 0-30
- Grades: Hot (80+), Warm (50-79), Cold (<50)

### 13. Sample Nurture Journeys (`marketing_nurture_journeys`)

| Name | Code | Type | Status |
|------|------|------|--------|
| Welcome Series | JRN-WELCOME-001 | welcome | Draft |
| Hot Lead Nurture | JRN-HOT-001 | lead_nurture | Active |
| Re-engagement Campaign | JRN-REENGAGE-001 | reengagement | Active |
| Product Launch Series | JRN-LAUNCH-001 | lead_nurture | Draft |
| Upsell Journey | JRN-UPSELL-001 | upsell | Active |

### 14. Sample A/B Tests (`marketing_ab_tests`)

| Name | Code | Type | Status |
|------|------|------|--------|
| Email Subject Line Test | AB-SUBJ-001 | subject_line | Active |
| CTA Button Color Test | AB-CTA-001 | cta | Active |
| Email Content Length | AB-CONTENT-001 | content | Draft |

### 15. Sample Journey Intelligence (`marketing_journey_intelligence`)

Generated touchpoints for leads:
- Stages: Awareness, Consideration, Conversion, Retention, Advocacy
- Touchpoints: Website Visit, Email Open, Form Submit, Purchase
- Engagement Scores: 20-95
- Churn Risk: 5-80
- Next Best Actions: Various promotional actions

### 16. Sample SLA Instances (`marketing_sla_instances`)

Created for pending approval campaigns:
- Status: Active, Breached
- Priority: High, Medium, Low
- Tracks campaign approval SLAs

### 17. Sample Branch Configs (`marketing_branch_configs`)

| Name | Code | Type | Budget | Leads/Month |
|------|------|------|--------|-------------|
| Tehran Main Branch | TEH-MAIN | Retail | $50,000 | 500 |
| Isfahan Branch | ISF-BRANCH | Retail | $30,000 | 300 |
| Shiraz Branch | SHI-BRANCH | Wholesale | $40,000 | 200 |
| Online Channel | ONLINE-CH | Digital | $60,000 | 800 |

### 18. Sample Notifications (`marketing_notifications`)

| Title | Type | Priority |
|-------|------|----------|
| Campaign Approval Required | approval | Medium |
| Lead Score Alert | alert | High |
| Journey Milestone | milestone | Low |
| Budget Alert | alert | Medium |
| A/B Test Complete | test | Medium |
| SLA Warning | sla | High |

### 19. Sample Communications (`marketing_communications`)

Delivery logs for channels:
- Status: Sent, Delivered, Opened, Clicked, Bounced, Unsubscribed
- Cost tracking per message
- Timestamp tracking for each stage

## Refreshing Sample Data

To reset sample data:

```python
# Run migrations (creates fresh sample data)
from marketing_models import run_marketing_migrations
run_marketing_migrations()
```

## Customizing Sample Data

Edit seed functions in `marketing_models.py`:
- `seed_*` functions populate initial data
- Each function checks for existing data before inserting
- Modify seed values to match business requirements

## Testing with Sample Data

Sample data is useful for:
1. UI development and testing
2. Workflow validation
3. Report generation
4. Training demonstrations
5. Performance testing
