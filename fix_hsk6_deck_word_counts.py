#!/usr/bin/env python3
"""
Fix HSK6 Deck Word Counts Script
Updates the total_words field to match the actual word count
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

def fix_hsk6_deck_word_counts():
    """Fix the total_words field for HSK6 decks"""
    print("🔧 Fixing HSK6 Deck Word Counts")
    print("=" * 60)
    
    # Fetch all HSK6 decks
    result = supabase.table('vocabulary_decks')\
        .select('*')\
        .like('name', 'HSK6%')\
        .order('name')\
        .execute()
    
    if not result.data:
        print("❌ No HSK6 decks found")
        return
    
    for deck in result.data:
        deck_id = deck['id']
        deck_name = deck['name']
        old_total_words = deck['total_words']
        
        # Count actual vocabulary linked to this deck
        vocab_result = supabase.table('deck_vocabulary')\
            .select('vocabulary_id', count='exact')\
            .eq('deck_id', deck_id)\
            .execute()
        
        actual_count = vocab_result.count if vocab_result.count is not None else 0
        
        print(f"🎯 {deck_name}:")
        print(f"   📊 Old Total Words: {old_total_words}")
        print(f"   📊 Actual Words: {actual_count}")
        
        # Update the total_words field
        if old_total_words != actual_count:
            update_result = supabase.table('vocabulary_decks')\
                .update({'total_words': actual_count})\
                .eq('id', deck_id)\
                .execute()
            
            if update_result.data:
                print(f"   ✅ Updated to: {actual_count}")
            else:
                print(f"   ❌ Failed to update")
        else:
            print(f"   ✅ Already correct")
        
        print()
    
    print("=" * 60)
    print("🎉 HSK6 Deck Word Counts Fixed!")
    
    # Verify the fix
    print("\n🔍 Verification:")
    verify_result = supabase.table('vocabulary_decks')\
        .select('name, total_words')\
        .like('name', 'HSK6%')\
        .order('name')\
        .execute()
    
    for deck in verify_result.data:
        print(f"   {deck['name']}: {deck['total_words']} words")

if __name__ == "__main__":
    try:
        fix_hsk6_deck_word_counts()
    except Exception as e:
        print(f"❌ Error fixing deck word counts: {e}")
        raise

