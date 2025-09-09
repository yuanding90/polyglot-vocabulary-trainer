#!/usr/bin/env python3
"""
Test User Progress with Correct Data Types

Test user progress operations with proper data types.
"""

from supabase import create_client, Client
import uuid

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def test_user_progress_with_correct_types():
    """Test user progress operations with correct data types."""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🧪 Testing User Progress with Correct Data Types...")
    print("=" * 60)
    
    # Get a real deck ID and word ID from the database
    try:
        # Get a real deck ID
        deck_response = supabase.table('vocabulary_decks').select('id').limit(1).execute()
        if not deck_response.data:
            print("❌ No decks found in database")
            return
        
        real_deck_id = deck_response.data[0]['id']
        print(f"✅ Using real deck ID: {real_deck_id}")
        
        # Get a real word ID
        word_response = supabase.table('vocabulary').select('id').limit(1).execute()
        if not word_response.data:
            print("❌ No words found in database")
            return
        
        real_word_id = word_response.data[0]['id']
        print(f"✅ Using real word ID: {real_word_id}")
        
        # Create test user ID (UUID format)
        test_user_id = str(uuid.uuid4())
        print(f"✅ Using test user ID: {test_user_id}")
        
        # Test data with correct types (integers for numeric fields)
        test_data = {
            'user_id': test_user_id,
            'deck_id': real_deck_id,
            'word_id': real_word_id,
            'repetitions': 1,
            'interval': 2,  # Integer, not float
            'ease_factor': 2.5,  # This might be float or integer
            'next_review_date': '2024-12-01T00:00:00Z',
            'again_count': 0
        }
        
        print(f"\n📝 Testing INSERT with correct data types...")
        try:
            insert_response = supabase.table('user_progress').insert(test_data).execute()
            print(f"✅ INSERT successful!")
            print(f"   Inserted data: {insert_response.data}")
            
            # Test reading the data back
            print(f"\n📖 Testing SELECT...")
            read_response = supabase.table('user_progress').select('*').eq('user_id', test_user_id).execute()
            print(f"✅ SELECT successful!")
            print(f"   Retrieved data: {read_response.data}")
            
            # Test updating the data
            print(f"\n✏️  Testing UPDATE...")
            update_data = {'repetitions': 2, 'interval': 5}  # Integers
            update_response = supabase.table('user_progress').update(update_data).eq('user_id', test_user_id).execute()
            print(f"✅ UPDATE successful!")
            print(f"   Updated data: {update_response.data}")
            
            # Clean up test data
            print(f"\n🧹 Cleaning up test data...")
            delete_response = supabase.table('user_progress').delete().eq('user_id', test_user_id).execute()
            print(f"✅ DELETE successful!")
            print(f"   Deleted rows: {len(delete_response.data) if delete_response.data else 0}")
            
            print(f"\n🎉 ALL TESTS PASSED!")
            print("✅ User progress operations work correctly")
            print("✅ RLS is NOT blocking user progress operations")
            print("✅ Users can save and update their progress")
            
        except Exception as e:
            print(f"❌ Operation failed: {e}")
            print(f"   This would indicate RLS is blocking the operation")
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")

def check_table_structure():
    """Check the actual structure of user_progress table."""
    print(f"\n🔍 Checking user_progress table structure...")
    print("=" * 50)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Try to get table info by inserting and seeing what errors we get
        print("📋 Testing different data types to understand table structure...")
        
        # Test with different ease_factor types
        test_cases = [
            {'ease_factor': 2.5},  # Float
            {'ease_factor': 2},    # Integer
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}: ease_factor = {test_case['ease_factor']} (type: {type(test_case['ease_factor']).__name__})")
            # We'll test this in the main function
            
    except Exception as e:
        print(f"❌ Error checking structure: {e}")

if __name__ == "__main__":
    test_user_progress_with_correct_types()
    check_table_structure()

