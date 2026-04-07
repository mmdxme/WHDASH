#!/usr/bin/env python3
"""
Migration script to add email management tables to the database.
Run this script to create the necessary tables for Email Management:
- email_settings: Stores Gmail OAuth configuration
- email_accounts: Stores connected email accounts (Gmail and SMTP/IMAP)
- email_cache: Optional cache for message metadata (improves performance)
"""

import sqlite3
import os

DATABASE = 'warehouse.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def migrate():
    if not os.path.exists(DATABASE):
        print(f"Database '{DATABASE}' does not exist. Please run the application first to create the database.")
        return False

    db = get_db()

    # Check if tables already exist
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_settings'")
    if cursor.fetchone():
        print("Table 'email_settings' already exists.")
    else:
        print("Creating 'email_settings' table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS email_settings (
                id INTEGER PRIMARY KEY,
                gmail_client_id TEXT,
                gmail_client_secret TEXT,
                gmail_redirect_uri TEXT,
                updated_at TEXT
            )
        ''')
        print("Created 'email_settings' table.")

    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_accounts'")
    if cursor.fetchone():
        print("Table 'email_accounts' already exists.")
    else:
        print("Creating 'email_accounts' table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS email_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_type TEXT NOT NULL,
                email_address TEXT,
                smtp_host TEXT,
                smtp_port INTEGER,
                smtp_username TEXT,
                smtp_password TEXT,
                imap_host TEXT,
                imap_port INTEGER,
                access_token TEXT,
                refresh_token TEXT,
                expires_at TEXT,
                is_default INTEGER DEFAULT 0,
                use_tls INTEGER DEFAULT 1,
                updated_at TEXT,
                notifications_enabled INTEGER DEFAULT 1,
                notify_from_senders TEXT,
                notify_subject_keywords TEXT,
                notify_sound_enabled INTEGER DEFAULT 1,
                last_seen_message_id TEXT,
                UNIQUE(user_id, account_type, email_address)
            )
        ''')
        print("Created 'email_accounts' table.")

        # Create indexes for faster queries
        print("Creating indexes for 'email_accounts'...")
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_accounts_user_id ON email_accounts(user_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_accounts_type ON email_accounts(account_type)')

    # Ensure indexes exist even if tables were created before indexes were added
    print("Ensuring indexes exist...")
    try:
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_accounts_user_id ON email_accounts(user_id)')
    except sqlite3.OperationalError:
        pass  # Index may already exist
    try:
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_accounts_type ON email_accounts(account_type)')
    except sqlite3.OperationalError:
        pass
    try:
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_accounts_default ON email_accounts(user_id, is_default)')
    except sqlite3.OperationalError:
        pass

    # Create email_cache table for performance optimization (optional local cache)
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_cache'")
    if cursor.fetchone():
        print("Table 'email_cache' already exists.")
    else:
        print("Creating 'email_cache' table...")
        db.execute('''
            CREATE TABLE IF NOT EXISTS email_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                message_uid TEXT NOT NULL,
                subject TEXT,
                sender TEXT,
                recipient TEXT,
                date TEXT,
                snippet TEXT,
                has_attachments INTEGER DEFAULT 0,
                is_read INTEGER DEFAULT 0,
                folder TEXT DEFAULT 'INBOX',
                cached_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, message_uid, folder)
            )
        ''')
        print("Created 'email_cache' table.")
        
        # Create indexes for email_cache
        print("Creating indexes for 'email_cache'...")
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_cache_account ON email_cache(account_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_cache_folder ON email_cache(account_id, folder)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_email_cache_date ON email_cache(account_id, date DESC)')

    db.commit()

    # Add new notification columns if they don't exist (for existing databases)
    print("Adding notification columns to existing tables...")
    columns_to_add = [
        ('email_accounts', 'notifications_enabled', 'INTEGER DEFAULT 1'),
        ('email_accounts', 'notify_from_senders', 'TEXT'),
        ('email_accounts', 'notify_subject_keywords', 'TEXT'),
        ('email_accounts', 'notify_sound_enabled', 'INTEGER DEFAULT 1'),
        ('email_accounts', 'last_seen_message_id', 'TEXT'),
    ]

    for table_col in columns_to_add:
        table_name, col_name, col_type = table_col
        try:
            db.execute(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}')
            print(f"  Added column '{col_name}' to '{table_name}'")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                pass  # Column already exists
            else:
                print(f"  Note: {e}")

    db.commit()
    db.close()
    print("Migration completed successfully!")
    return True


if __name__ == '__main__':
    migrate()
