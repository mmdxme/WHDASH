# FLOW Product Architecture

## Overview

FLOW is the enterprise internal communication platform designed as a layered communication system with clear separation between private/conversational content and public/global content.

## Core Product Vision

### FLOW = Global Company-Wide Communication Layer
- **Purpose**: Organization-wide visibility and discoverable content
- **Content Types**:
  - Public announcements
  - Company-wide updates
  - Published posts from Streams
  - Featured/discoverable content

### STREAMS = Scoped Communication Spaces
- **Purpose**: Team/department/project-specific conversations
- **Content Types**:
  - Private team discussions
  - Project-specific messages
  - Department communications
- **Default Visibility**: Private (only visible to members)
- **Publishing**: Optional, requires explicit action to share to FLOW

### CHATS = Direct/Private Conversations
- **Purpose**: 1-to-1 or small group direct messages
- **Visibility**: Private (only participants can see)

### GROUPS = Community Spaces
- **Purpose**: Group conversations with optional membership rules
- **Visibility**: Can be public or private

## Data Model

### New Tables Added

#### flow_posts
Global Flow feed posts created natively or published from streams.

```sql
CREATE TABLE flow_posts (
    id TEXT PRIMARY KEY,
    author_id INTEGER NOT NULL,
    author_name TEXT,
    author_avatar TEXT,
    content TEXT NOT NULL,
    content_html TEXT,
    post_type TEXT DEFAULT 'text',
    source_type TEXT,  -- 'stream', 'group', or NULL for native
    source_id TEXT,
    source_name TEXT,
    source_url TEXT,
    media_url TEXT,
    media_type TEXT,
    is_pinned INTEGER DEFAULT 0,
    is_featured INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    edited_at DATETIME
);
```

#### flow_post_reactions
Emoji reactions on Flow posts.

```sql
CREATE TABLE flow_post_reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    emoji TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id, emoji)
);
```

#### flow_post_comments
Comments on Flow posts.

```sql
CREATE TABLE flow_post_comments (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    author_name TEXT,
    author_avatar TEXT,
    content TEXT NOT NULL,
    is_deleted INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    edited_at DATETIME
);
```

#### flow_post_shares
Audit trail for posts published from streams.

```sql
CREATE TABLE flow_post_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT NOT NULL,
    from_stream_id TEXT,
    from_stream_name TEXT,
    original_message_id TEXT,
    shared_by INTEGER NOT NULL,
    shared_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### flow_global_settings
Global Flow governance settings.

```sql
CREATE TABLE flow_global_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Existing Tables (Enhanced)

#### flow_channels (Streams)
Enhanced with:
- `settings` TEXT - JSON blob with Flow publishing settings
- `allow_publish_to_flow` boolean in settings

## Key Product Rules

### 1. FLOW as Global Layer
- Content appears in Flow only if:
  - Created natively as a Flow post
  - Explicitly published from a Stream (where Stream allows it)
  - From a public Group (automatic)
- Private Stream content NEVER appears in Flow unless published

### 2. STREAM as Scoped Space
- All messages in a Stream are private to members by default
- Stream admins can enable "allow_publish_to_flow" setting
- Only when enabled, members can publish individual messages to Flow

### 3. Publication Flow
```
Stream Message → Right-click → "Share to Flow" → Flow Post Created
                                          ↓
                              Source tracked (from_stream_id)
                              Original message reference kept
```

### 4. Privacy Rules
- Private content stays private
- Publishing is always explicit (never automatic)
- Audit trail maintained for publications

## Navigation Structure

```
Flow (Global Communication Hub)
├── Chats (Private 1-to-1 conversations)
├── Streams (Team/department scoped spaces)
│   ├── Browse Streams
│   ├── Create Stream
│   └── Individual Stream view with "Share to Flow"
├── Groups (Community spaces)
└── Flow Feed (Global/public content)
    ├── Create Post
    ├── View Posts
    ├── React
    └── Comment
```

## API Endpoints

### Flow Feed
- `GET /flow/api/flow/feed` - Get Flow feed posts
- `POST /flow/api/flow/posts` - Create native Flow post
- `GET /flow/api/flow/posts/<id>` - Get post with comments
- `POST /flow/api/flow/posts/<id>/react` - Add/remove reaction
- `POST /flow/api/flow/posts/<id>/comment` - Add comment
- `DELETE /flow/api/flow/posts/<id>` - Delete post

### Stream Publishing
- `POST /flow/api/flow/publish` - Publish message to Flow
- `GET /flow/api/flow/streams/<id>/publish-allowed` - Check if can publish

## UI/UX Principles

### Visual Distinction
- **Flow Feed**: Blue/Purple gradient branding, globe icon
- **Streams**: Green branding, # channel icon
- **Chats**: Blue branding, chat bubble icon
- **Groups**: Purple branding, users icon

### Card Design
- Flow post cards show:
  - Author avatar and name
  - Timestamp
  - Source badge (if from Stream/Group)
  - Post type badge (Announcement, Update, etc.)
  - Content preview
  - Media (if any)
  - Reactions and comments count
  - Action buttons

### RTL/LTR Support
- All text uses `dir="auto"` for proper bidirectional rendering
- UI components maintain correct alignment
- Persian/Arabic text displays correctly

## Future Enhancements

1. **Moderation Queue**: Admin approval for Flow posts
2. **Scheduling**: Schedule posts for future publication
3. **Analytics**: Track post engagement metrics
4. **Following**: Follow specific streams for notifications
5. **Digest**: Email digest of Flow updates
