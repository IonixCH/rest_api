#!/usr/bin/env python3
"""
Script to add working_hours column to hr_attendance table if it doesn't exist
"""

import psycopg2
import os
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'hris_db'),
    'user': os.getenv('DB_USER', 'odoo'),
    'password': os.getenv('DB_PASSWORD', 'odoo'),
}

def add_working_hours_column():
    """Add working_hours column to hr_attendance table if it doesn't exist"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='hr_attendance' AND column_name='working_hours'
        """)
        
        if cursor.fetchone() is None:
            print("Adding working_hours column to hr_attendance table...")
            
            # Add the column
            cursor.execute("""
                ALTER TABLE hr_attendance 
                ADD COLUMN working_hours VARCHAR(20) DEFAULT '00:00:00'
            """)
            
            # Update existing records to calculate working_hours
            cursor.execute("""
                UPDATE hr_attendance 
                SET working_hours = CASE 
                    WHEN check_in IS NOT NULL AND check_out IS NOT NULL THEN
                        LPAD(EXTRACT(HOUR FROM (check_out - check_in))::text, 2, '0') || ':' ||
                        LPAD(EXTRACT(MINUTE FROM (check_out - check_in))::text, 2, '0') || ':' ||
                        LPAD(EXTRACT(SECOND FROM (check_out - check_in))::int::text, 2, '0')
                    ELSE '00:00:00'
                END
                WHERE working_hours IS NULL OR working_hours = '00:00:00'
            """)
            
            conn.commit()
            print("✅ working_hours column added successfully!")
            print(f"✅ Updated {cursor.rowcount} existing records")
            
        else:
            print("ℹ️  working_hours column already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🔧 Adding working_hours column to hr_attendance table...")
    success = add_working_hours_column()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
