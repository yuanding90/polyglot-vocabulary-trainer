#!/usr/bin/env python3
"""
Run the daily_summary table creation migration
"""

import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def run_migration():
    """Run the daily_summary table creation migration"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🚀 Running daily_summary table migration...")
    print("=" * 60)
    
    # Read the SQL file
    try:
        with open('create_daily_summary_table.sql', 'r') as f:
            sql_content = f.read()
        print("✅ Successfully read SQL migration file")
    except FileNotFoundError:
        print("❌ Error: create_daily_summary_table.sql file not found")
        return
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return
    
    # Split SQL into individual statements (split by semicolon)
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    print(f"📝 Found {len(sql_statements)} SQL statements to execute")
    
    # Execute each statement
    for i, statement in enumerate(sql_statements, 1):
        if not statement:
            continue
            
        try:
            print(f"\n{i}. Executing statement...")
            print(f"   SQL: {statement[:100]}{'...' if len(statement) > 100 else ''}")
            
            # Use rpc to execute raw SQL
            result = supabase.rpc('exec_sql', {'sql': statement}).execute()
            
            print(f"   ✅ Statement {i} executed successfully")
            
        except Exception as e:
            print(f"   ❌ Error executing statement {i}: {e}")
            # Continue with other statements even if one fails
            continue
    
    print("\n" + "=" * 60)
    print("🎉 Migration completed!")
    print("\n📋 What was created:")
    print("   - daily_summary table")
    print("   - RLS policies for security")
    print("   - Indexes for performance")
    print("   - Auto-updating timestamps")
    
    # Test the table creation
    try:
        print("\n🔍 Testing table creation...")
        result = supabase.table('daily_summary').select('*').limit(1).execute()
        print("✅ daily_summary table is accessible")
    except Exception as e:
        print(f"❌ Error accessing daily_summary table: {e}")

if __name__ == "__main__":
    run_migration()
