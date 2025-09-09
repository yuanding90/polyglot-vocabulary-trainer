#!/usr/bin/env python3
"""
Check all tables to see what data exists
"""

from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_all_tables():
    """Check all relevant tables"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Checking all tables...")
    print("=" * 60)
    
    tables_to_check = [
        'daily_summary',
        'rating_history', 
        'study_sessions',
        'user_progress',
        'vocabulary_decks',
        'vocabulary'
    ]
    
    for table in tables_to_check:
        try:
            print(f"\n📊 Checking {table}...")
            result = supabase.table(table).select('*', count='exact').limit(5).execute()
            
            if result.count is not None:
                print(f"   Total records: {result.count}")
                if result.data:
                    print(f"   Sample records:")
                    for i, record in enumerate(result.data[:3]):
                        print(f"     {i+1}. {str(record)[:100]}...")
                else:
                    print("   No records found")
            else:
                print("   Could not get count")
                
        except Exception as e:
            print(f"   ❌ Error accessing {table}: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Table check completed!")

if __name__ == "__main__":
    check_all_tables()
