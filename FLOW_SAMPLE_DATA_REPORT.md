# FLOW Sample Data Report

## Overview

This report documents the sample/demo data created for the FLOW module to ensure the UI is never empty and showcases all features.

## Sample Data Created

### Flow Posts (Global Feed)

**Count**: 8 posts

| Post Type | Content Summary | Pinned |
|----------|---------------|--------|
| Announcement | Welcome to Flow introduction | Yes |
| Update | Q1 2026 Performance Report highlights | No |
| Celebration | Sales Team achievement recognition | No |
| Announcement | New HR Policy Update | No |
| Update | Engineering WMS upgrade completion | No |
| Announcement | Office Holiday Schedule | No |
| Discussion | AI-based demand forecasting idea | No |
| Announcement | Security reminder - 2FA audit | No |

**Reactions**: Random mix of 👍, ❤️, 🎉, 🚀 (50% chance per emoji)
**Comments**: 40% chance of 1-3 comments per post

### Streams

**Count**: 10 streams

| Stream Name | Category | Type | Description |
|------------|----------|------|-------------|
| general | Company | Public | General discussions and announcements |
| announcements | Company | Public | Official company announcements |
| engineering | Departments | Public | Engineering team discussions |
| sales | Departments | Public | Sales team updates and leads |
| marketing | Departments | Public | Marketing campaigns and social media |
| hr | Departments | Public | HR policies and employee resources |
| warehouse | Operations | Public | Warehouse operations and logistics |
| logistics | Operations | Public | Shipping and delivery updates |
| random | Social | Public | Random conversations and water cooler chat |
| introductions | Social | Public | Introduce yourself to the team |

**Membership**: All users added to all streams

### Groups

**Count**: 5 groups

| Group Name | Type | Description |
|------------|------|-------------|
| Project Alpha Team | Private | Core team for Project Alpha |
| Q4 Marketing Campaign | Private | Marketing push for Q4 |
| New Employee Onboarding | Private | Onboarding committee |
| Friday Social Club | Public | Friday activities and events |
| Book Club | Public | Monthly book discussions |

### Messages

**In Streams**: 5-15 messages per stream (5 streams with messages)
**In Groups**: 3-10 messages per group (3 groups with messages)
**In Private Chats**: 3-8 messages per conversation (5 conversations)

**Sample Message Content**:
- "Good morning everyone! 👋"
- "Has anyone seen the latest quarterly report?"
- "The new server deployment is scheduled for tonight."
- "Great job team on closing that deal! 🎉"
- "Reminder: All hands meeting at 3 PM today."
- "Can someone review my pull request?"
- "The warehouse inventory has been updated."
- "Welcome to the team, @username!"
- "Lunch is on me today! 🍕"
- "Please remember to update your status."

### User Profiles

**Created For**: All existing users in the system

| Field | Sample Data |
|-------|------------|
| display_name | Username.title() |
| department | Random: Engineering, Sales, Marketing, HR, Operations, Warehouse |
| job_title | Random: Manager, Specialist, Coordinator, Director, Associate |
| avatar_url | null (uses default avatar) |

### User Statuses

**70% of users** have a status set

| Status | Status Text Examples |
|--------|---------------------|
| online | - |
| away | "Away from desk", "Back soon", "BRB" |
| busy | "In a call", "Focus mode", "Do not disturb" |
| in_meeting | - |
| offline | - |

### User Settings

**Created For**: All users

| Setting | Default Value |
|---------|--------------|
| language | 'en' |
| theme | 'light' |
| notification_sound | 1 |
| notification_desktop | 1 |
| message_preview | 1 |
| show_online_status | 1 |

## Sample Post Details

### Welcome Post (Pinned)
```
🎉 Welcome to Flow! This is your company-wide communication platform.
Share updates, announcements, and highlights with the entire organization.
```

### Q1 Performance Post
```
📊 Q1 2026 Performance Report is now available.
Key highlights: 23% increase in operational efficiency,
15% reduction in delivery times.
Full report on the dashboard.
```

### Sales Achievement Post
```
🏆 Congratulations to the Sales Team for achieving 120% of quarterly targets!
Special recognition to @sarah and @michael for exceptional performance.
```

### HR Policy Post
```
📢 New HR Policy Update: Flexible working hours policy is now in effect.
Please review the updated guidelines in the HR section.
```

### Engineering Update
```
🚀 Engineering Team: The new warehouse management system upgrade is complete.
Report any issues to #engineering.
```

## Data Generation Timestamp

All sample data is generated with timestamps within the past:
- Posts: 30 minutes to 1 week ago
- Messages: 1 minute to 48 hours ago
- Status updates: Recent

## Sample Images

### Avatars Used
The system uses default avatar placeholders:
- `avatar_private_blue.png` - Private chats
- `avatar_group_purple.png` - Groups
- `avatar_channel_green.png` - Streams/Channels

### Media Handling
- Images can be uploaded to posts
- File attachments supported
- Media gallery shows shared files

## Seed Function

The `seed_flow_data()` function in `flow_models.py` handles all sample data creation.

To re-seed data:
```python
from flow_models import seed_flow_data, initialize_flow_tables
initialize_flow_tables()
seed_flow_data()
```

## Demo Accounts

The system should have multiple demo users for testing:
- admin user (id=1)
- Additional users from existing user table

## Empty State Prevention

All major views have proper empty states:
- No conversations → "Start a new chat" CTA
- No streams → "Browse or create streams" CTA
- No groups → "Create or join groups" CTA
- No Flow posts → "Posts from streams will appear here" message

## RTL Sample Data

For RTL languages (Persian, Arabic), sample content with RTL characters:
- Persian: "سلام! این یک پیام تستی است"
- Arabic: "مرحبا! هذه رسالة تجريبية"

Note: These should be added in future translation passes.
