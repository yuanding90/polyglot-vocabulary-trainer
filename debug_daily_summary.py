#!/usr/bin/env python3
"""
Debug daily_summary table to see what's happening with the stats
"""

from supabase import create_client
from datetime import datetime, timedelta

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def debug_daily_summary():
    """Debug daily_summary table and recent activity"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Debugging daily_summary table...")
    print("=" * 60)
    
    try:
        # Check if table exists and has data
        print("1. Checking daily_summary table...")
        result = supabase.table('daily_summary').select('*').execute()
        
        if result.data:
            print(f"📊 Found {len(result.data)} records in daily_summary:")
            for record in result.data:
                print(f"   - User: {record['user_id'][:8]}... | Date: {record['date']} | Reviews: {record['reviews_done']} | New Words: {record['new_words_learned']}")
        else:
            print("📊 No records found in daily_summary table")
        
        # Check rating_history for recent activity
        print("\n2. Checking rating_history for recent activity...")
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        
        rating_result = supabase.table('rating_history').select('*').gte('created_at', seven_days_ago.isoformat()).execute()
        
        if rating_result.data:
            print(f"📊 Found {len(rating_result.data)} recent ratings:")
            for rating in rating_result.data[:5]:  # Show first 5
                print(f"   - User: {rating['user_id'][:8]}... | Rating: {rating['rating']} | Date: {rating['created_at']}")
        else:
            print("📊 No recent ratings found in rating_history")
        
        # Check study_sessions for recent activity
        print("\n3. Checking study_sessions for recent activity...")
        session_result = supabase.table('study_sessions').select('*').gte('completed_at', seven_days_ago.isoformat()).execute()
        
        if session_result.data:
            print(f"📊 Found {len(session_result.data)} recent study sessions:")
            for session in session_result.data[:5]:  # Show first 5
                print(f"   - User: {session['user_id'][:8]}... | Type: {session['session_type']} | Words: {session['words_studied']} | Date: {session['completed_at']}")
        else:
            print("📊 No recent study sessions found")
        
        # Check if there are any users
        print("\n4. Checking for users...")
        user_result = supabase.table('user_progress').select('user_id').limit(5).execute()
        
        if user_result.data:
            print(f"📊 Found {len(user_result.data)} users with progress:")
            user_ids = list(set([record['user_id'] for record in user_result.data]))
            for user_id in user_ids[:3]:  # Show first 3
                print(f"   - User: {user_id[:8]}...")
        else:
            print("📊 No users found with progress")
        
    except Exception as e:
        print(f"❌ Error debugging: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Debug completed!")
    print("\n💡 Possible issues:")
    print("   1. Daily summary logging might not be called")
    print("   2. Session activity tracking might not be working")
    print("   3. RLS policies might be blocking inserts")
    print("   4. User authentication might be missing")

if __name__ == "__main__":
    debug_daily_summary()
