#!/usr/bin/env python3
"""
Check Chinese Deck Sizes
Query the database to get the exact word count for each Chinese deck
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

def check_chinese_deck_sizes():
    """Check the size of each Chinese deck"""
    print("🔍 Checking Chinese Deck Sizes")
    print("=" * 50)
    
    try:
        # Get all Chinese decks
        result = supabase.table('vocabulary_decks')\
            .select('id, name, total_words')\
            .like('name', 'Chinese Finance%')\
            .order('name')\
            .execute()
        
        if not result.data:
            print("❌ No Chinese decks found")
            return
        
        print(f"📚 Found {len(result.data)} Chinese decks:\n")
        
        total_words = 0
        for deck in result.data:
            deck_id = deck['id']
            deck_name = deck['name']
            total_words_field = deck['total_words']
            
            # Get actual word count from deck_vocabulary table
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
        
        print("=" * 50)
        print(f"📈 Total Chinese vocabulary: {total_words} words")
        print(f"📚 Average per deck: {total_words // len(result.data)} words")
        
    except Exception as e:
        print(f"❌ Error checking deck sizes: {e}")

if __name__ == "__main__":
    check_chinese_deck_sizes()

