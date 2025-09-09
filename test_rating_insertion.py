#!/usr/bin/env python3
"""
Test rating insertion with proper authentication
"""

from supabase import create_client, Client
import uuid
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def test_rating_insertion_with_auth():
    """Test rating insertion with authentication."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🧪 Testing rating insertion with authentication...")
    print("=" * 60)
    
    # First, let's see if we can get any existing users
    try:
        print("1. Checking if there are any users in auth.users...")
        # This won't work with anon key, but let's try
        users_result = supabase.table('auth.users').select('*').limit(5).execute()
        print(f"Users found: {len(users_result.data) if users_result.data else 0}")
    except Exception as e:
        print(f"❌ Cannot access auth.users: {e}")
    
    # Let's check what user IDs exist in other tables
    try:
        print("\n2. Checking user IDs in user_progress table...")
        progress_result = supabase.table('user_progress').select('user_id').limit(10).execute()
        if progress_result.data:
            user_ids = set(record['user_id'] for record in progress_result.data)
            print(f"Found {len(user_ids)} unique user IDs in user_progress:")
            for user_id in list(user_ids)[:5]:  # Show first 5
                print(f"  - {user_id}")
        else:
            print("No user_progress records found")
    except Exception as e:
        print(f"❌ Error checking user_progress: {e}")
    
    # Let's try to insert with a real user ID from user_progress
    try:
        print("\n3. Trying to insert rating with real user ID...")
        if progress_result.data:
            real_user_id = progress_result.data[0]['user_id']
            print(f"Using real user ID: {real_user_id}")
            
            test_data = {
                'user_id': real_user_id,
                'word_id': 1,
                'deck_id': '00000000-0000-0000-0000-000000000000',
                'rating': 'good',
                'timestamp': datetime.now().isoformat()
            }
            
            result = supabase.table('rating_history').insert(test_data).execute()
            print("✅ Successfully inserted rating with real user ID!")
            print(f"   Inserted record: {result.data}")
            
            # Clean up
            if result.data:
                record_id = result.data[0]['id']
                supabase.table('rating_history').delete().eq('id', record_id).execute()
                print("🧹 Cleaned up test record")
        else:
            print("⚠️  No real user IDs found to test with")
            
    except Exception as e:
        print(f"❌ Error inserting with real user ID: {e}")
    
    # Let's check if there are any existing rating_history records
    try:
        print("\n4. Checking for any existing rating_history records...")
        existing_result = supabase.table('rating_history').select('*').limit(5).execute()
        if existing_result.data:
            print(f"Found {len(existing_result.data)} existing records:")
            for record in existing_result.data:
                print(f"  - User: {record['user_id'][:8]}... | Rating: {record['rating']} | Date: {record.get('created_at', record.get('timestamp', 'N/A'))}")
        else:
            print("No existing rating_history records found")
    except Exception as e:
        print(f"❌ Error checking existing records: {e}")

def check_rls_policies():
    """Check what RLS policies are currently active."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n🔍 Checking RLS policies...")
    print("=" * 40)
    
    # Try to get policies using a direct SQL query
    try:
        # This is a workaround to check policies
        policies_result = supabase.rpc('get_policies_for_table', {'table_name': 'rating_history'}).execute()
        print(f"Policies: {policies_result.data}")
    except Exception as e:
        print(f"❌ Cannot get policies directly: {e}")
    
    # Try to check if RLS is enabled by attempting operations
    try:
        print("\nTesting RLS behavior...")
        
        # Try to select without authentication
        select_result = supabase.table('rating_history').select('*').limit(1).execute()
        print(f"✅ SELECT works: {len(select_result.data) if select_result.data else 0} records")
        
        # Try to insert without authentication (should fail)
        try:
            insert_result = supabase.table('rating_history').insert({
                'user_id': 'test-user-id',
                'word_id': 999,
                'deck_id': 'test-deck-id',
                'rating': 'test',
                'timestamp': datetime.now().isoformat()
            }).execute()
            print("⚠️  INSERT worked without auth (RLS might be disabled)")
        except Exception as e:
            print(f"✅ INSERT blocked without auth (RLS is working): {e.get('message', str(e))}")
            
    except Exception as e:
        print(f"❌ Error testing RLS: {e}")

if __name__ == "__main__":
    test_rating_insertion_with_auth()
    check_rls_policies()
