# CRM Sample Data Guide

## Overview

The CRM module includes a comprehensive seed script that creates realistic demo data for testing and demonstration purposes.

## Seed Script: `seed_crm_data.py`

### What It Creates

#### Customer Segments (5)
- Premium Customers
- Growth Accounts
- At Risk
- New Customers
- Dormant

#### CRM Leads (50)
Realistic leads with:
- Unique lead numbers (LEAD-YYYY-NNNNN)
- Company names from Gulf/Arabian business naming conventions
- Contact details (name, phone, email, WhatsApp)
- Lead sources (Website, Phone Inquiry, Referral, Partner, etc.)
- Lifecycle statuses (New, Contacted, Qualified, etc.)
- Priority levels (Low, Medium, High, Urgent)
- Lead scores (20-95)
- Estimated values (AED 5,000 - 500,000)
- Industry classifications
- Assigned salespeople

#### Lead Activities (100)
Activity log entries including:
- Calls, meetings, visits, emails, tasks
- Subjects (Initial contact, Follow-up, Proposal, etc.)
- Outcomes (Positive response, Needs follow-up, etc.)
- Duration (15-120 minutes)
- Next follow-up dates

#### Complaints (20)
Customer complaints with:
- Unique complaint numbers (CMP-YYYY-NNNNN)
- Categories (Product Quality, Delivery Issue, Pricing, etc.)
- Priorities (Low, Medium, High, Critical)
- Statuses (New, In Progress, Escalated, Resolved, Closed)
- Timeline entries

#### Key Accounts (10)
Strategic account records with:
- Account tiers (Standard, Preferred, Key Account, Strategic, Premium)
- Assigned account managers
- Business objectives
- Success metrics
- Review dates
- Objectives with progress tracking

#### Journey Events (50)
Customer journey touchpoints including:
- Event types (Awareness, Inquiry, Quote, Purchase, Delivery, etc.)
- Channels (Website, Phone, Email, Walk-in, Partner, etc.)
- Reference types linking to Sales documents

## Running the Seed Script

```bash
# From the WHDASH directory
python seed_crm_data.py
```

## Sample Data Characteristics

### Leads
- Mix of Gulf/Arabian business naming conventions
- Realistic industry spread (Construction, Manufacturing, Retail, Healthcare, etc.)
- Geographic distribution (Dubai, Abu Dhabi, Riyadh, Manama, Doha, etc.)
- Variety of lead sources reflecting real marketing channels
- Hot leads (~20%) for urgency demonstration
- Full lifecycle representation (new to converted/lost)

### Activities
- Realistic distribution of activity types
- Follow-up patterns that mirror sales best practices
- Outcome variety for reporting depth

### Complaints
- Priority distribution skewed toward Medium/Low (reflecting reality)
- Mix of categories to test workflow routing
- Timeline progression for resolution tracking

### Key Accounts
- Tier distribution favoring Standard/Preferred (realistic)
- Objectives with progress toward targets
- Regular review schedule representation

## Resetting Sample Data

To reset CRM demo data:

```python
import sqlite3
conn = sqlite3.connect('warehouse.db')
cursor = conn.cursor()

# Delete in correct order (respecting foreign keys)
cursor.execute("DELETE FROM crm_journey_events")
cursor.execute("DELETE FROM crm_account_objectives")
cursor.execute("DELETE FROM crm_account_reviews")
cursor.execute("DELETE FROM crm_relationship_map")
cursor.execute("DELETE FROM crm_key_accounts")
cursor.execute("DELETE FROM crm_complaint_timeline")
cursor.execute("DELETE FROM crm_complaints")
cursor.execute("DELETE FROM crm_lead_activities")
cursor.execute("DELETE FROM crm_lead_notes")
cursor.execute("DELETE FROM crm_lead_qualifications")
cursor.execute("DELETE FROM crm_lead_conversion_log")
cursor.execute("DELETE FROM crm_lead_contacts")
cursor.execute("DELETE FROM crm_leads")
cursor.execute("DELETE FROM crm_customer_segments")
cursor.execute("DELETE FROM crm_segments")
cursor.execute("DELETE FROM crm_customer_engagement")
cursor.execute("DELETE FROM crm_customer_churn_risk")

conn.commit()
conn.close()

# Re-run seed script
python seed_crm_data.py
```

## Integration with Existing Data

The seed script is designed to work alongside existing data:
- It uses existing user IDs for assignments
- It references existing customers and orders
- It creates new CRM-specific records without modifying Sales data
- Safe to run multiple times (uses auto-increment IDs)

## Demo Scenarios

### Scenario 1: Lead to Customer Conversion
1. Find a Lead in "Qualified" status
2. Review lead score and activities
3. Convert to Customer via `/crm/leads/<id>/convert/`
4. Verify customer appears in Sales module

### Scenario 2: Complaint Resolution Workflow
1. Find a Complaint in "New" or "In Progress"
2. Add response via complaint detail page
3. Update status through lifecycle
4. Verify timeline entries

### Scenario 3: Key Account Review
1. Navigate to `/crm/key-accounts/`
2. Select an account and review objectives
3. Check account revenue vs targets
4. Review relationship map

### Scenario 4: Pipeline Analysis
1. Go to `/crm/opportunities/pipeline/`
2. See Kanban view of all opportunities
3. Check stage distribution
4. Run `/crm/reports/pipeline/` for detailed analysis

### Scenario 5: Lead Conversion Analysis
1. Run `/crm/reports/lead-conversion/`
2. See conversion rates by source
3. Analyze monthly trends
4. Identify best/worst performing sources
