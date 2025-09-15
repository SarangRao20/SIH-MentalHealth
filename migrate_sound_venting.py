#!/usr/bin/env python3
"""
Database migration script to add SoundVentingSession table
"""

from app import app, db
from models import SoundVentingSession

def migrate_database():
    """Add SoundVentingSession table to existing database"""
    with app.app_context():
        try:
            # Create the new table
            db.create_all()
            print("✅ Database migration completed successfully!")
            print("✅ SoundVentingSession table added")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            return False
        
        return True

if __name__ == '__main__':
    migrate_database()