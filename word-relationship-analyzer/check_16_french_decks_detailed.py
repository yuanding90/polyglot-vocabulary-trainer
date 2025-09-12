#!/usr/bin/env python3
"""
Detailed check of the 16 French decks with accurate word counts.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_16_french_decks_detailed():
    """Check the 16 French decks with detailed word counts"""
    print("🔍 Detailed check of 16 French decks...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get all vocabulary decks
        decks_result = supabase.table('vocabulary_decks').select('*').execute()
        
        if not decks_result.data:
            print("❌ No vocabulary decks found!")
            return
        
        # Filter for the 16 main French decks (French 01 through French 16)
        french_deck_names = [
            "12. French 01", "13. French 02", "14. French 03", "15. French 04",
            "16. French 05", "17. French 06", "18. French 07", "19. French 08",
            "20. French 09", "21. French 10", "22. French 11", "23. French 12",
            "24. French 13", "25. French 14", "26. French 15", "27. French 16"
        ]
        
        french_decks = []
        for deck in decks_result.data:
            if deck['name'] in french_deck_names:
                french_decks.append(deck)
        
        print(f"🇫🇷 Found {len(french_decks)} French decks:")
        print("-" * 60)
        
        total_words = 0
        all_deck_ids = []
        
        for i, deck in enumerate(french_decks, 1):
            deck_id = deck['id']
            deck_name = deck['name']
            deck_total = deck.get('total_words', 0)
            
            # Get actual word count from deck_vocabulary table
            vocab_count_result = supabase.table('deck_vocabulary').select('*', count='exact').eq('deck_id', deck_id).execute()
            actual_count = vocab_count_result.count if vocab_count_result.count else 0
            
            print(f"{i:2d}. {deck_name}")
            print(f"    Deck ID: {deck_id}")
            print(f"    Listed total: {deck_total}")
            print(f"    Actual count: {actual_count}")
            
            total_words += actual_count
            all_deck_ids.append(deck_id)
            
            # Show sample words from this deck
            sample_result = supabase.table('deck_vocabulary').select(
                'vocabulary(id, language_a_word, language_b_translation)'
            ).eq('deck_id', deck_id).limit(3).execute()
            
            if sample_result.data:
                print(f"    Sample words:")
                for item in sample_result.data:
                    vocab = item['vocabulary']
                    print(f"      - {vocab['language_a_word']} → {vocab['language_b_translation']}")
            print()
        
        print("=" * 60)
        print(f"📊 SUMMARY:")
        print(f"   • Total French decks: {len(french_decks)}")
        print(f"   • Total vocabulary words: {total_words}")
        print(f"   • Average words per deck: {total_words // len(french_decks) if french_decks else 0}")
        
        # Get all unique vocabulary IDs from French decks
        print(f"\n🔍 Getting all unique vocabulary IDs from French decks...")
        all_vocab_result = supabase.table('deck_vocabulary').select('vocabulary_id').in_('deck_id', all_deck_ids).execute()
        
        if all_vocab_result.data:
            unique_vocab_ids = set(item['vocabulary_id'] for item in all_vocab_result.data)
            print(f"   • Unique vocabulary IDs: {len(unique_vocab_ids)}")
            
            # Check if any of our CSV sample words exist in these IDs
            print(f"\n🔍 Checking CSV sample words in French deck vocabulary...")
            
            csv_sample_words = ['abaissement', 'abaisser', 'abandon', 'abandonner', 'abcès', 'abnégation', 'aboi']
            
            found_count = 0
            for word in csv_sample_words:
                # Check if this word exists in the French deck vocabulary
                vocab_result = supabase.table('vocabulary').select('id').eq('language_a_word', word.lower()).execute()
                if vocab_result.data:
                    vocab_id = vocab_result.data[0]['id']
                    if vocab_id in unique_vocab_ids:
                        found_count += 1
                        print(f"   ✅ Found: {word} (ID: {vocab_id})")
                    else:
                        print(f"   ⚠️  Exists but not in French decks: {word} (ID: {vocab_id})")
                else:
                    print(f"   ❌ Not found in vocabulary: {word}")
            
            print(f"\n📊 CSV Sample Results:")
            print(f"   • Found in French decks: {found_count}/{len(csv_sample_words)}")
            print(f"   • Success rate: {(found_count/len(csv_sample_words)*100):.1f}%")
        
        return french_decks, total_words
        
    except Exception as e:
        print(f"❌ Error checking French decks: {e}")
        return [], 0

if __name__ == "__main__":
    decks, total_words = check_16_french_decks_detailed()
    if decks:
        print(f"\n🎯 Ready to proceed with {len(decks)} French decks containing {total_words} total words!")
    else:
        print(f"\n⚠️  No French decks found.")
