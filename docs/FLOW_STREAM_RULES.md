# FLOW vs Streams Rules

## Core Product Definitions

### FLOW (Global Feed)
**Definition**: FLOW is the organization-wide, public communication layer.

**Characteristics**:
- Content is visible across the organization
- Discoverable by all users (subject to permissions)
- Posts can be created natively in Flow
- Posts can be published from Streams (where allowed)

**Use Cases**:
- Company announcements
- Org-wide updates
- Public team achievements
- Organizational news

### STREAMS (Scoped Spaces)
**Definition**: STREAMS are team/department/project-specific communication spaces.

**Characteristics**:
- Content is private by default (only visible to members)
- Requires explicit membership
- Messages stay within the stream context
- Can optionally publish to Flow

**Use Cases**:
- Department discussions
- Project team communications
- Team-specific announcements
- Private working groups

### CHATS (Direct Messages)
**Definition**: Private 1-to-1 or small group conversations.

**Characteristics**:
- Completely private
- No publishing to Flow
- No visibility outside participants

### GROUPS (Community Spaces)
**Definition**: Community spaces with optional membership.

**Characteristics**:
- Can be public or private
- Public groups automatically appear in Flow
- Private groups behave like streams

## Publication Rules

### Stream → Flow Publishing

**Rule 1: Stream Must Allow Publishing**
```
Stream Settings → allow_publish_to_flow = true
```

**Rule 2: User Must Be Member**
```
User must be a member of the stream to publish
```

**Rule 3: Explicit Action Required**
```
User right-click → "Share to Flow" → Creates Flow post
```
No automatic publishing!

**Rule 4: Source Tracking**
```
Flow post contains:
- source_type = 'stream'
- source_id = stream_id
- source_name = stream_name
- source_url = link to original stream message
```

### Public Groups → Flow (Automatic)

Public groups have their messages automatically appear in Flow:
```
Group Settings → group_type = 'public'
```

Private groups do NOT automatically appear in Flow.

## Privacy Matrix

| Content Type | Visible to Non-Members | Publishable to Flow |
|--------------|------------------------|-------------------|
| Private Stream Message | No | Only if allowed by Stream |
| Public Stream Message | No (Stream is public, but message is in Stream) | Only if allowed by Stream |
| Private Group Message | No | No |
| Public Group Message | Yes (in Flow) | Automatic |
| Direct Chat | No | No |
| Flow Native Post | Yes | Direct creation |

## Stream Settings

### Key Settings

1. **Stream Visibility**
   - Public: Anyone can see stream exists, but content requires membership
   - Private: Only members know the stream exists

2. **Allow Publish to Flow**
   - When enabled: Members can share individual messages to Flow
   - When disabled: No publishing allowed (default)

3. **Moderation Required**
   - Future: Require admin approval before Flow publication

4. **Invite Code**
   - Generated for private streams
   - Required for joining

## Access Control

### Who Can View Flow?
- All authenticated users (by default)
- Admins can restrict to specific roles

### Who Can Create Native Flow Posts?
- All authenticated users (default)
- Configurable via flow_feed permissions

### Who Can Publish from Stream to Flow?
- Stream members only
- Stream must have allow_publish_to_flow = true

### Who Can Manage Stream Settings?
- Stream admins only
- Stream owner

## UI Implementation

### Flow Feed Tab
- Blue/Purple gradient branding
- "Create Post" composer
- Posts with source badges
- Reaction and comment counts

### Stream View
- Green branding
- Message list
- Right-click context menu with "Share to Flow"
- Member list

### Context Menu Options
```
Message in Stream:
├── Reply
├── Forward
├── Copy Text
├── Pin
├── Save Media (if applicable)
├── Share to Flow  ← New
├── Edit (if own message)
└── Delete (if own message)
```

## Violations and Prevention

### Violation 1: Auto-publishing Private Content
**Prevention**:
- No automatic code path from Stream to Flow
- require explicit user action
- audit logging of all publications

### Violation 2: Unauthorized Publication
**Prevention**:
- Check membership before allowing publish
- Check stream settings before allowing publish
- Return 403 if not allowed

### Violation 3: Private Content Leak
**Prevention**:
- Flow feed queries only explicitly published content
- Public group posts are inherently public
- No JOINs that could expose private content

## Audit Trail

All publications are logged:
```python
log_audit(user_id, 'flow_publish', {
    'message_id': message_id,
    'stream_id': stream_id,
    'stream_name': stream_name
}, 'flow')
```

And tracked in `flow_post_shares` table.

## Migration Notes

Existing channels now support:
```sql
ALTER TABLE flow_channels ADD COLUMN settings TEXT;
```

Default settings:
```json
{
    "allow_publish_to_flow": false,
    "moderation_required": false
}
```
