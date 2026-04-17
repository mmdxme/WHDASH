# Flow Sample Data Report

## Overview

This document details the sample data populated in the Flow module for internal enterprise communication and collaboration.

## Flow Module Coverage

### Channels & Conversations
| Table | Sample Data |
|-------|-------------|
| flow_channels | 20 channels |
| flow_conversations | 64 conversations |
| flow_conversation_members | 306 members |
| flow_channel_members | 177 members |

### Messages & Posts
| Table | Sample Data |
|-------|-------------|
| flow_messages | 434 messages |
| flow_posts | 15 posts |
| flow_post_comments | 8 comments |
| flow_post_reactions | 23 reactions |

### Voice & Meetings
| Table | Sample Data |
|-------|-------------|
| flow_call_sessions | 16 call sessions |
| flow_call_participants | 32 participants |

### User Activity
| Table | Sample Data |
|-------|-------------|
| flow_user_profiles | 13 user profiles |
| flow_user_settings | 13 user settings |
| flow_user_status | 39 status updates |
| flow_notifications | 60 notifications |

### Groups
| Table | Sample Data |
|-------|-------------|
| flow_groups | 10 groups |
| flow_group_members | 61 group members |

## Channel Categories

The system includes pre-configured channels for various business functions:
- `#general` - Company-wide announcements
- `#sales-team` - Sales department discussions
- `#operations` - Operations updates
- `#hr-announcements` - HR notices
- `#finance-updates` - Finance team
- `#warehouse-alerts` - WMS alerts
- `#quality-news` - Quality notifications
- `#it-support` - IT helpdesk

## Message Content Samples

Messages contain realistic content for an auto spare parts trading company:
- Sales quotes and order discussions
- Warehouse receiving notifications
- HR policy announcements
- Finance deadline reminders
- Quality inspection alerts
- Supplier performance feedback
- Customer complaint escalations

## Integration with Other Modules

Flow notifications are linked to:
- `platform_notifications` - 48 notifications
- `workflow_instances` - Approval alerts
- `quality_alerts` - NCR notifications
- `maintenance_alerts` - Work order updates

## User Status Distribution

| Status | Count |
|--------|-------|
| Online | ~10 users |
| Away | ~5 users |
| Offline | ~20 users |

## Validation

| Flow Component | Status | Count |
|----------------|--------|-------|
| Channels | OK | 20 |
| Conversations | OK | 64 |
| Messages | OK | 434 |
| Posts | OK | 15 |
| Groups | OK | 10 |
| Notifications | OK | 60 |

## Usage Notes

Flow data makes the platform feel "alive" with:
- Real-time-like messaging history
- Cross-department communication patterns
- Approval workflow notifications
- @mentions and reactions
- Pinned announcements