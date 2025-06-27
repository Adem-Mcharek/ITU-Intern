#!/usr/bin/env python3
"""
Manual migration script to upgrade the database for the queue system
Run this once to migrate your existing system to use the new queue
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models import Meeting, ProcessingQueue

def create_processing_queue_table():
    """Create the ProcessingQueue table and add new columns to Meeting"""
    
    # SQL for creating ProcessingQueue table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS processing_queue (
        id INTEGER NOT NULL PRIMARY KEY,
        meeting_id INTEGER NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        queued_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        started_at DATETIME,
        completed_at DATETIME,
        status VARCHAR(32) NOT NULL DEFAULT 'queued',
        FOREIGN KEY(meeting_id) REFERENCES meeting (id)
    );
    """
    
    # SQL for adding new columns to Meeting table
    add_columns_sql = [
        "ALTER TABLE meeting ADD COLUMN processing_started_at DATETIME;",
        "ALTER TABLE meeting ADD COLUMN processing_completed_at DATETIME;"
    ]
    
    # Execute the SQL
    try:
        # Create the ProcessingQueue table
        db.session.execute(db.text(create_table_sql))
        print("✓ Created processing_queue table")
        
        # Add new columns to Meeting table (ignore errors if columns already exist)
        for sql in add_columns_sql:
            try:
                db.session.execute(db.text(sql))
                print(f"✓ Added column: {sql.split('ADD COLUMN')[1].split()[0]}")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"- Column already exists: {sql.split('ADD COLUMN')[1].split()[0]}")
                else:
                    print(f"⚠ Error adding column: {e}")
        
        db.session.commit()
        print("✓ Database upgrade completed successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error during migration: {e}")
        return False
    
    return True

def migrate_existing_meetings():
    """Add any existing 'queued' meetings to the processing queue"""
    
    try:
        # Find meetings that are queued but not in the processing queue
        queued_meetings = Meeting.query.filter_by(status='queued').all()
        
        for meeting in queued_meetings:
            # Check if already in queue
            existing_queue_item = ProcessingQueue.query.filter_by(meeting_id=meeting.id).first()
            if not existing_queue_item:
                # Add to queue
                queue_item = ProcessingQueue(
                    meeting_id=meeting.id,
                    status='queued',
                    priority=0
                )
                db.session.add(queue_item)
                print(f"✓ Added meeting {meeting.id} to processing queue")
        
        db.session.commit()
        print(f"✓ Migrated {len(queued_meetings)} existing queued meetings")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error migrating existing meetings: {e}")
        return False
    
    return True

def verify_migration():
    """Verify that the migration was successful"""
    
    try:
        # Test that we can query the new table
        queue_count = ProcessingQueue.query.count()
        print(f"✓ ProcessingQueue table working - {queue_count} items in queue")
        
        # Test that new columns exist
        test_meeting = Meeting.query.first()
        if test_meeting:
            # Try to access new columns
            _ = test_meeting.processing_started_at
            _ = test_meeting.processing_completed_at
            print("✓ New Meeting columns accessible")
        
        return True
        
    except Exception as e:
        print(f"✗ Migration verification failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting queue system migration...")
    print("=" * 50)
    
    # Create Flask app context without queue worker
    import os
    os.environ['SKIP_QUEUE_WORKER'] = 'true'
    app = create_app()
    
    with app.app_context():
        print("📊 Current database status:")
        try:
            meeting_count = Meeting.query.count()
            queued_count = Meeting.query.filter_by(status='queued').count()
            print(f"   - Total meetings: {meeting_count}")
            print(f"   - Queued meetings: {queued_count}")
        except Exception as e:
            print(f"   - Could not query meetings (expected during migration): {e}")
        print()
        
        # Step 1: Create new table and columns
        print("🔧 Step 1: Creating new database structures...")
        if not create_processing_queue_table():
            print("✗ Migration failed at step 1")
            return False
        print()
        
        # Step 2: Migrate existing data
        print("📋 Step 2: Migrating existing queued meetings...")
        if not migrate_existing_meetings():
            print("✗ Migration failed at step 2")
            return False
        print()
        
        # Step 3: Verify migration
        print("✅ Step 3: Verifying migration...")
        if not verify_migration():
            print("✗ Migration verification failed")
            return False
        print()
        
        print("🎉 Migration completed successfully!")
        print("=" * 50)
        print("Next steps:")
        print("1. Restart your Flask application")
        print("2. The queue worker will start automatically")
        print("3. New meetings will be processed sequentially")
        print("4. Check the admin panel for queue status")
        
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 