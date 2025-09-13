#!/usr/bin/env python3
"""
Database Migration Script
Adds missing created_at column to assessment table
"""

import sqlite3
from datetime import datetime
import os

def migrate_database():
    """Add created_at column to assessment table"""
    
    db_path = "instance/mental_health.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if created_at column already exists
        cursor.execute("PRAGMA table_info(assessment)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' in columns:
            print("✅ created_at column already exists!")
            return True
        
        print("🔄 Adding created_at column to assessment table...")
        
        # Add the created_at column (SQLite doesn't support CURRENT_TIMESTAMP in ALTER)
        cursor.execute("""
            ALTER TABLE assessment 
            ADD COLUMN created_at TIMESTAMP
        """)
        
        # Update existing records to have same created_at as completed_at
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            UPDATE assessment 
            SET created_at = completed_at 
            WHERE created_at IS NULL
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Show updated table structure
        cursor.execute("PRAGMA table_info(assessment)")
        columns = cursor.fetchall()
        print("\n📋 Updated Assessment Table Structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🗃️  Database Migration Tool")
    print("=" * 30)
    
    success = migrate_database()
    
    if success:
        print("\n🎉 Migration completed! You can now run the application.")
    else:
        print("\n💡 If migration failed, you can:")
        print("   1. Delete the database file: instance/mental_health.db")
        print("   2. Restart the application to recreate tables")