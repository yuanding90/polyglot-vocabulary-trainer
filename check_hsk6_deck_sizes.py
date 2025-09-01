#!/usr/bin/env python3
"""
HSK6 Deck Size Verification Script
Verifies the actual word count for each HSK6 deck
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

def check_hsk6_deck_sizes():
    """Check the actual word count for each HSK6 deck"""
    print("🔍 Checking HSK6 Deck Sizes")
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
    
    total_words = 0
    
    for deck in result.data:
        deck_id = deck['id']
        deck_name = deck['name']
        total_words_field = deck['total_words']
        
        # Count actual vocabulary linked to this deck
        vocab_result = supabase.table('deck_vocabulary')\
            .select('vocabulary_id', count='exact')\
            .eq('deck_id', deck_id)\
            .execute()
        
        actual_count = vocab_result.count if vocab_result.count is not None else 0
        
        print(f"🎯 {deck_name}:")
        print(f"   📊 Total Words (field): {total_words_field}")
        print(f"   📊 Actual Words (linked): {actual_count}")
        print(f"   🆔 Deck ID: {deck_id}")
        print()
        
        total_words += actual_count
    
    print("=" * 60)
    print(f"📈 Total HSK6 vocabulary: {total_words} words")
    print(f"📚 Number of HSK6 decks: {len(result.data)}")
    
    # Show sample vocabulary from first deck
    if result.data:
        first_deck_id = result.data[0]['id']
        print(f"\n🔍 Sample vocabulary from {result.data[0]['name']}:")
        print("-" * 40)
        
        # Get sample vocabulary
        sample_result = supabase.table('deck_vocabulary')\
            .select('vocabulary_id, word_order')\
            .eq('deck_id', first_deck_id)\
            .order('word_order')\
            .limit(5)\
            .execute()
        
        for item in sample_result.data:
            vocab_id = item['vocabulary_id']
            
            # Get vocabulary details
            vocab_result = supabase.table('vocabulary')\
                .select('language_a_word, language_b_translation, language_a_sentence')\
                .eq('id', vocab_id)\
                .execute()
            
            if vocab_result.data:
                vocab = vocab_result.data[0]
                print(f"   {item['word_order']}. {vocab['language_a_word']} → {vocab['language_b_translation']}")
                print(f"      Example: {vocab['language_a_sentence'][:50]}...")
                print()

if __name__ == "__main__":
    try:
        check_hsk6_deck_sizes()
    except Exception as e:
        print(f"❌ Error checking deck sizes: {e}")
        raise
