# Talent Management Sample Data Guide

## Overview

This document describes the sample/demo data available for the Talent Management module.

---

## Sample Data Structure

### Employees with Talent Profiles

| Employee Code | Name | Department | Position | Potential | Performance | Readiness |
|--------------|------|------------|----------|-----------|-------------|-----------|
| EMP001 | Sarah Johnson | Engineering | VP of Engineering | Very High | Exceeds | Ready Now |
| EMP002 | Michael Chen | Engineering | Senior Architect | High | Exceeds | 1 Year |
| EMP003 | Ahmed Al-Rashid | Engineering | Tech Lead | High | Meets | 1 Year |
| EMP004 | Priya Sharma | Product | Senior Product Manager | High | Exceeds | 6 Months |
| EMP005 | James Wilson | Sales | Sales Director | Medium | Exceeds | 2 Years |
| EMP006 | Maria Garcia | Marketing | Marketing Manager | High | Meets | 1 Year |
| EMP007 | David Kim | Engineering | Software Engineer | Medium | Meets | 2 Years |
| EMP008 | Lisa Thompson | HR | HR Director | Very High | Exceeds | Ready Now |
| EMP009 | Robert Brown | Finance | CFO | Very High | Exceeds | Ready Now |
| EMP010 | Jennifer Lee | Operations | COO | Very High | Exceeds | Ready Now |

---

## Talent Profiles Sample Data

### Profile Fields
- Potential Rating: Very High, High, Medium, Low
- Performance Rating: Exceeds, Meets, Below
- Readiness Level: Ready Now, 6 Months, 1 Year, 2 Years, 3+ Years
- Flight Risk: 0 or 1
- Hi-Po Flag: 0 or 1
- Succession Candidate: 0 or 1

### Sample Talent Ratings

| Employee | Potential | Performance | Readiness | Hi-Po | Succession | Flight Risk |
|----------|-----------|-------------|-----------|-------|------------|-------------|
| Sarah Johnson | Very High | Exceeds | Ready Now | Yes | Yes | No |
| Michael Chen | High | Exceeds | 1 Year | Yes | Yes | No |
| Ahmed Al-Rashid | High | Meets | 1 Year | Yes | Yes | No |
| Priya Sharma | High | Exceeds | 6 Months | Yes | Yes | No |
| James Wilson | Medium | Exceeds | 2 Years | No | Yes | No |
| Maria Garcia | High | Meets | 1 Year | Yes | Yes | No |
| David Kim | Medium | Meets | 2 Years | No | No | No |
| Lisa Thompson | Very High | Exceeds | Ready Now | Yes | Yes | No |
| Robert Brown | Very High | Exceeds | Ready Now | Yes | Yes | No |
| Jennifer Lee | Very High | Exceeds | Ready Now | Yes | Yes | No |

---

## Competency Sample Data

### Competency Categories
1. Leadership
2. Technical Skills
3. Business Acumen
4. Communication
5. Problem Solving
6. Teamwork
7. Innovation
8. Customer Focus

### Sample Competencies

| Category | Competency | Type | Weight |
|----------|------------|------|--------|
| Leadership | Strategic Thinking | Core | 1.5 |
| Leadership | Team Leadership | Core | 1.3 |
| Leadership | Decision Making | Core | 1.2 |
| Leadership | Change Management | Core | 1.1 |
| Leadership | Coaching & Mentoring | Leadership | 1.0 |
| Technical | Data Analysis | Technical | 1.4 |
| Technical | Technical Expertise | Technical | 1.6 |
| Technical | Digital Literacy | Technical | 1.1 |
| Business | Financial Literacy | Core | 1.3 |
| Business | Market Awareness | Core | 1.2 |
| Business | Business Strategy | Core | 1.5 |
| Communication | Verbal Communication | Core | 1.0 |
| Communication | Written Communication | Core | 1.0 |
| Communication | Presentation Skills | Core | 1.1 |
| Communication | Negotiation | Core | 1.2 |
| Problem Solving | Analytical Thinking | Core | 1.3 |
| Problem Solving | Critical Thinking | Core | 1.2 |
| Problem Solving | Creativity | Core | 1.1 |
| Teamwork | Collaboration | Core | 1.0 |
| Teamwork | Cross-Functional Cooperation | Core | 1.1 |
| Teamwork | Conflict Resolution | Core | 1.0 |
| Innovation | Innovation Mindset | Core | 1.1 |
| Innovation | Risk Taking | Core | 1.0 |
| Customer Focus | Customer Orientation | Core | 1.2 |
| Customer Focus | Relationship Building | Core | 1.0 |

### Sample Employee Competency Assessments

| Employee | Competency | Current Level | Required Level | Gap |
|----------|-----------|---------------|-----------------|-----|
| Sarah Johnson | Strategic Thinking | 5 | 4 | +1 |
| Sarah Johnson | Team Leadership | 5 | 4 | +1 |
| Sarah Johnson | Decision Making | 4 | 4 | 0 |
| Sarah Johnson | Data Analysis | 3 | 4 | -1 |
| Michael Chen | Technical Expertise | 5 | 4 | +1 |
| Michael Chen | Data Analysis | 4 | 3 | +1 |
| Michael Chen | Analytical Thinking | 4 | 4 | 0 |
| Ahmed Al-Rashid | Team Leadership | 4 | 3 | +1 |
| Ahmed Al-Rashid | Coaching & Mentoring | 3 | 3 | 0 |
| Ahmed Al-Rashid | Technical Expertise | 4 | 4 | 0 |
| Priya Sharma | Business Strategy | 4 | 4 | 0 |
| Priya Sharma | Communication | 5 | 4 | +1 |
| Priya Sharma | Customer Orientation | 4 | 4 | 0 |

---

## Talent Pools Sample Data

### Pool Definitions

| Pool Name | Type | Color | Members |
|-----------|------|--------|--------|
| High Potential Pool | HiPo | #8b5cf6 | 6 |
| Successor Pool | Succession | #10b981 | 5 |
| Critical Role Backup | Critical | #f59e0b | 3 |
| Future Leaders | Leadership | #6366f1 | 4 |
| Specialist Talent | Specialist | #ec4899 | 2 |
| Retention Risk | Retention | #ef4444 | 1 |

### Sample Pool Memberships

| Pool | Employee | Joined Date | Status |
|------|----------|-------------|--------|
| High Potential Pool | Sarah Johnson | 2024-01-15 | Active |
| High Potential Pool | Michael Chen | 2024-02-20 | Active |
| High Potential Pool | Priya Sharma | 2024-03-10 | Active |
| High Potential Pool | Maria Garcia | 2024-04-05 | Active |
| High Potential Pool | Lisa Thompson | 2024-01-10 | Active |
| High Potential Pool | Robert Brown | 2024-02-01 | Active |
| High Potential Pool | Jennifer Lee | 2024-01-05 | Active |
| Successor Pool | Michael Chen | 2024-03-01 | Active |
| Successor Pool | Ahmed Al-Rashid | 2024-03-15 | Active |
| Successor Pool | Priya Sharma | 2024-04-01 | Active |
| Future Leaders | Jennifer Lee | 2024-01-20 | Active |
| Future Leaders | Lisa Thompson | 2024-02-15 | Active |
| Future Leaders | Sarah Johnson | 2024-03-01 | Active |

---

## Succession Planning Sample Data

### Critical Roles

| Position | Department | Incumbent | Criticality |
|----------|-----------|-----------|-------------|
| VP of Engineering | Engineering | Sarah Johnson | Critical |
| Sales Director | Sales | James Wilson | Critical |
| HR Director | HR | Lisa Thompson | Critical |
| CFO | Finance | Robert Brown | Critical |
| COO | Operations | Jennifer Lee | Critical |
| Tech Lead | Engineering | Ahmed Al-Rashid | High |

### Succession Plans

| Critical Role | Successor | Readiness | Status |
|--------------|----------|-----------|--------|
| VP of Engineering | Michael Chen | 1 Year | Approved |
| VP of Engineering | Ahmed Al-Rashid | 2 Years | Draft |
| Sales Director | Priya Sharma | 2 Years | Draft |
| HR Director | Maria Garcia | 1 Year | Approved |
| CFO | [Unidentified] | - | - |
| COO | [Unidentified] | - | - |
| Tech Lead | David Kim | 6 Months | Approved |

---

## Development Plans Sample Data

### Sample IDP Structure

| Employee | Year | Status | Completion | Goals |
|---------|------|--------|------------|-------|
| Michael Chen | 2026 | In Progress | 65% | 4 (3 completed) |
| Ahmed Al-Rashid | 2026 | In Progress | 40% | 3 (1 completed) |
| Priya Sharma | 2026 | In Progress | 80% | 5 (4 completed) |
| Maria Garcia | 2026 | Draft | 0% | 3 (0 started) |
| David Kim | 2026 | Completed | 100% | 4 (4 completed) |

### Sample Development Goals

| Plan | Goal Title | Status | Priority |
|------|-----------|--------|----------|
| Michael Chen - IDP | Executive Leadership Program | In Progress | High |
| Michael Chen - IDP | Strategic Planning Certification | Completed | Medium |
| Michael Chen - IDP | Board Presentation Skills | Not Started | Medium |
| Michael Chen - IDP | Cross-Functional Project Leadership | In Progress | High |
| Ahmed Al-Rashid - IDP | Advanced Architecture Design | In Progress | High |
| Ahmed Al-Rashid - IDP | Team Management Training | Completed | Medium |
| Ahmed Al-Rashid - IDP | Innovation Workshop | Not Started | Low |
| Priya Sharma - IDP | Executive MBA | In Progress | High |
| Priya Sharma - IDP | Negotiation Mastery | Completed | High |
| Priya Sharma - IDP | Strategic Vision Workshop | Completed | Medium |
| Priya Sharma - IDP | Industry Conference Speaking | Completed | Medium |
| Priya Sharma - IDP | Cross-Functional Leadership | In Progress | High |

---

## Talent Review Cycles Sample Data

### 2026 Annual Review Cycle

| Field | Value |
|-------|-------|
| Cycle Name | 2026 Annual Talent Review |
| Period | 2025-01-01 to 2025-12-31 |
| Status | In Progress |
| Participants | 10 |
| Completed | 7 |
| Calibration Date | 2026-03-15 |

### Sample Participant Ratings

| Employee | Manager Rating | Potential | Performance | Readiness | Final Rating |
|----------|---------------|-----------|-------------|-----------|--------------|
| Sarah Johnson | Lisa Thompson | Very High | Exceeds | Ready Now | A - Top Talent |
| Michael Chen | Sarah Johnson | High | Exceeds | 1 Year | A - Top Talent |
| Ahmed Al-Rashid | Sarah Johnson | High | Meets | 1 Year | B+ - Strong Performer |
| Priya Sharma | Jennifer Lee | High | Exceeds | 6 Months | A - Top Talent |
| James Wilson | Jennifer Lee | Medium | Exceeds | 2 Years | B - Solid Performer |
| Maria Garcia | Jennifer Lee | High | Meets | 1 Year | B+ - Strong Performer |
| David Kim | Ahmed Al-Rashid | Medium | Meets | 2 Years | B - Solid Performer |
| Lisa Thompson | Robert Brown | Very High | Exceeds | Ready Now | A - Top Talent |
| Robert Brown | External | Very High | Exceeds | Ready Now | A - Top Talent |
| Jennifer Lee | External | Very High | Exceeds | Ready Now | A - Top Talent |

---

## Career Path Sample Data

### Sample Career Paths

| From Position | To Position | Path Type | Avg Duration |
|---------------|-------------|-----------|--------------|
| Software Engineer | Senior Software Engineer | Promotion | 3 years |
| Senior Software Engineer | Tech Lead | Promotion | 3 years |
| Tech Lead | Engineering Manager | Promotion | 2 years |
| Engineering Manager | VP of Engineering | Promotion | 4 years |
| Product Manager | Senior Product Manager | Promotion | 2 years |
| Senior Product Manager | Director of Product | Promotion | 3 years |
| Sales Representative | Sales Manager | Promotion | 4 years |
| Sales Manager | Sales Director | Promotion | 3 years |
| Individual Contributor | Team Lead | Lateral | 1 year |
| Team Lead | Manager | Promotion | 2 years |

---

## Mentoring Assignments Sample Data

| Mentor | Mentee | Start Date | Status | Sessions |
|--------|--------|------------|--------|----------|
| Sarah Johnson | Michael Chen | 2025-01-01 | Active | 8 |
| Sarah Johnson | Ahmed Al-Rashid | 2025-03-01 | Active | 5 |
| Lisa Thompson | Maria Garcia | 2025-02-01 | Active | 6 |
| Jennifer Lee | Priya Sharma | 2025-01-15 | Active | 7 |

---

## Sample Dashboard Metrics

### Talent Dashboard (as of April 2026)

| Metric | Value |
|--------|-------|
| Total Talent Profiles | 150 |
| Active Employees with Profiles | 142 |
| Hi-Po Count | 23 |
| Succession Coverage | 75% |
| Critical Roles at Risk | 4 |
| IDPs In Progress | 67 |
| Active Review Cycles | 2 |
| Ready Now (Overall) | 18 |
| Development Ready (6mo-1yr) | 45 |
| Building (2+ years) | 79 |

### Hi-Po Distribution

| Readiness | Count |
|-----------|-------|
| Ready Now | 8 |
| 6 Months | 5 |
| 1 Year | 7 |
| 2 Years | 3 |

### Bench Strength Summary

| Department | Critical Roles | Covered | Coverage % |
|-----------|---------------|---------|------------|
| Engineering | 12 | 9 | 75% |
| Sales | 5 | 4 | 80% |
| Marketing | 3 | 2 | 67% |
| Operations | 4 | 3 | 75% |
| HR | 2 | 2 | 100% |
| Finance | 3 | 2 | 67% |
| Product | 4 | 3 | 75% |

---

## Generating Sample Data

To populate the system with sample data, run:

```bash
python seed_talent_data.py
```

This will create:
- 25 employees with talent profiles
- 8 competency categories with 25 competencies
- 3 talent pools with sample memberships
- 6 critical roles with succession plans
- 10 development plans with goals
- 1 talent review cycle with participants
- 4 mentoring assignments
- 5 career paths
