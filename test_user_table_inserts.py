#!/usr/bin/env python3
"""
Test if we can insert data into user tables (RLS test)
"""

from supabase import create_client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def test_user_table_inserts():
    """Test inserting data into user tables"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("🧪 Testing user table inserts...")
    print("=" * 60)
    
    # Test data
    test_user_id = "123e4567-e89b-12d3-a456-426614174000"
    test_deck_id = "5930768f-39d0-4dd0-a3be-8e4ffa7685b5"  # From the decks we found
    test_word_id = 1  # From the vocabulary we found
    
    # Test 1: Try to insert into rating_history
    print("1. Testing rating_history insert...")
    try:
        rating_data = {
            'user_id': test_user_id,
            'word_id': test_word_id,
            'deck_id': test_deck_id,
            'rating': 'good',
            'timestamp': datetime.now().isoformat()
        }
        result = supabase.table('rating_history').insert(rating_data).execute()
        print("   ✅ rating_history insert successful")
        
        # Clean up
        if result.data:
            record_id = result.data[0]['id']
            supabase.table('rating_history').delete().eq('id', record_id).execute()
            print("   🧹 Cleaned up test record")
            
    except Exception as e:
        print(f"   ❌ rating_history insert failed: {e}")
    
    # Test 2: Try to insert into user_progress
    print("\n2. Testing user_progress insert...")
    try:
        progress_data = {
            'user_id': test_user_id,
            'word_id': test_word_id,
            'deck_id': test_deck_id,
            'repetitions': 1,
            'interval': 1,
            'ease_factor': 2.5,
            'next_review_date': datetime.now().isoformat(),
            'again_count': 0
        }
        result = supabase.table('user_progress').insert(progress_data).execute()
        print("   ✅ user_progress insert successful")
        
        # Clean up
        if result.data:
            record_id = result.data[0]['id']
            supabase.table('user_progress').delete().eq('id', record_id).execute()
            print("   🧹 Cleaned up test record")
            
    except Exception as e:
        print(f"   ❌ user_progress insert failed: {e}")
    
    # Test 3: Try to insert into study_sessions
    print("\n3. Testing study_sessions insert...")
    try:
        session_data = {
            'user_id': test_user_id,
            'deck_id': test_deck_id,
            'session_type': 'review',
            'words_studied': 5,
            'correct_answers': 4,
            'session_duration': 300,
            'completed_at': datetime.now().isoformat()
        }
        result = supabase.table('study_sessions').insert(session_data).execute()
        print("   ✅ study_sessions insert successful")
        
        # Clean up
        if result.data:
            record_id = result.data[0]['id']
            supabase.table('study_sessions').delete().eq('id', record_id).execute()
            print("   🧹 Cleaned up test record")
            
    except Exception as e:
        print(f"   ❌ study_sessions insert failed: {e}")
    
    # Test 4: Try to insert into daily_summary
    print("\n4. Testing daily_summary insert...")
    try:
        summary_data = {
            'user_id': test_user_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'reviews_done': 5,
            'new_words_learned': 3
        }
        result = supabase.table('daily_summary').insert(summary_data).execute()
        print("   ✅ daily_summary insert successful")
        
        # Clean up
        if result.data:
            record_id = result.data[0]['id']
            supabase.table('daily_summary').delete().eq('id', record_id).execute()
            print("   🧹 Cleaned up test record")
            
    except Exception as e:
        print(f"   ❌ daily_summary insert failed: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 Insert tests completed!")
    print("\n💡 If all inserts failed, the issue is likely:")
    print("   1. RLS policies are blocking inserts")
    print("   2. User authentication is required")
    print("   3. The app needs to be authenticated to save data")

if __name__ == "__main__":
    test_user_table_inserts()
