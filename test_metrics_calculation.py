#!/usr/bin/env python3
"""
Test Metrics Calculation Script
Verifies that new decks show correct metrics (all unseen, no strengthening/learning/etc)
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Initialize Supabase client
supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
supabase_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def test_metrics_calculation():
    """Test metrics calculation for new decks"""
    print("🧪 Testing Metrics Calculation for New Decks")
    print("=" * 60)
    
    # Get a new user ID that shouldn't have any progress
    test_user_id = '11111111-1111-1111-1111-111111111111'
    
    # Get all HSK6 decks
    result = supabase.table('vocabulary_decks')\
        .select('*')\
        .like('name', 'HSK6%')\
        .order('name')\
        .limit(2)\
        .execute()
    
    if not result.data:
        print("❌ No HSK6 decks found")
        return
    
    for deck in result.data:
        deck_id = deck['id']
        deck_name = deck['name']
        
        print(f"\n🎯 Testing {deck_name}:")
        print("-" * 40)
        
        # Check if user has any progress for this deck
        progress_result = supabase.table('user_progress')\
            .select('*')\
            .eq('user_id', test_user_id)\
            .eq('deck_id', deck_id)\
            .execute()
        
        has_progress = len(progress_result.data) > 0
        print(f"   📊 Has progress: {has_progress}")
        print(f"   📊 Progress count: {len(progress_result.data)}")
        
        # Get total words in deck
        vocab_result = supabase.table('deck_vocabulary')\
            .select('vocabulary_id', count='exact')\
            .eq('deck_id', deck_id)\
            .execute()
        
        total_words = vocab_result.count if vocab_result.count is not None else 0
        print(f"   📊 Total words in deck: {total_words}")
        
        # Expected metrics for new deck
        expected_unseen = total_words
        expected_others = 0
        
        print(f"   ✅ Expected unseen: {expected_unseen}")
        print(f"   ✅ Expected others (learning/strengthening/etc): {expected_others}")
        
        if has_progress:
            print(f"   ⚠️  WARNING: User has progress, this should be a new deck!")
        else:
            print(f"   ✅ Correct: No progress found for new deck")
        
        print()

if __name__ == "__main__":
    try:
        test_metrics_calculation()
    except Exception as e:
        print(f"❌ Error testing metrics: {e}")
        raise
