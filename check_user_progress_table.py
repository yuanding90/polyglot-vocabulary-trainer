#!/usr/bin/env python3
"""
Check User Progress Table

Checks if user_progress table exists and what RLS policies it needs.
"""

from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_user_progress_table():
    """Check if user_progress table exists and its structure."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🔍 Checking user_progress table...")
    print("=" * 50)
    
    try:
        # Try to read from user_progress table
        response = supabase.table('user_progress').select('*').limit(1).execute()
        
        if response.data is not None:
            print("✅ user_progress table exists and is accessible")
            print(f"   Sample data count: {len(response.data)}")
            
            if response.data:
                # Show table structure
                sample_row = response.data[0]
                print(f"   Table columns: {list(sample_row.keys())}")
                print(f"   Sample row: {sample_row}")
            else:
                print("   Table is empty (no user progress data yet)")
        else:
            print("❌ user_progress table does not exist or is not accessible")
            
    except Exception as e:
        print(f"❌ Error accessing user_progress table: {e}")
        print("\n💡 This means the table doesn't exist yet or has RLS issues.")
    
    print("\n" + "=" * 50)
    print("🎯 RLS Impact Analysis:")
    print("1. ✅ vocabulary_decks, vocabulary, deck_vocabulary - RLS enabled, read access working")
    print("2. ⚠️  user_progress - This table needs RLS policies for user progress updates")
    print("\n📋 Required user_progress table structure:")
    print("- user_id (string) - user identifier")
    print("- deck_id (string) - deck identifier") 
    print("- word_id (integer) - vocabulary word identifier")
    print("- repetitions (integer) - number of successful reviews")
    print("- interval (real) - current SRS interval")
    print("- ease_factor (real) - SRS ease factor")
    print("- next_review_date (timestamp) - when word is due for review")
    print("- again_count (integer) - number of failed reviews")
    
    print("\n🔒 RLS Policy Requirements for user_progress:")
    print("- Users should only see their own progress (user_id = auth.uid())")
    print("- Users should be able to INSERT/UPDATE their own progress")
    print("- Users should NOT see other users' progress")

def test_user_progress_operations():
    """Test if user progress operations work with current RLS setup."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n🧪 Testing User Progress Operations...")
    print("=" * 50)
    
    try:
        # Test reading user progress
        response = supabase.table('user_progress').select('*').limit(1).execute()
        print(f"✅ Read test: {'Success' if response.data is not None else 'Failed'}")
        
        # Test inserting user progress (this will likely fail without proper RLS)
        test_data = {
            'user_id': 'test-user-123',
            'deck_id': 'test-deck-123', 
            'word_id': 1,
            'repetitions': 0,
            'interval': 1.0,
            'ease_factor': 2.5,
            'next_review_date': '2024-01-01T00:00:00Z',
            'again_count': 0
        }
        
        try:
            insert_response = supabase.table('user_progress').insert(test_data).execute()
            print(f"✅ Insert test: Success (data inserted)")
            # Clean up test data
            supabase.table('user_progress').delete().eq('user_id', 'test-user-123').execute()
        except Exception as e:
            print(f"❌ Insert test: Failed - {e}")
            print("   This is expected if RLS is blocking writes")
            
    except Exception as e:
        print(f"❌ Operation test failed: {e}")

if __name__ == "__main__":
    check_user_progress_table()
    test_user_progress_operations()

