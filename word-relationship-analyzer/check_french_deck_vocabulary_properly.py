#!/usr/bin/env python3
"""
Check French deck vocabulary properly - understand the ID system.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_french_deck_vocabulary_properly():
    """Check French deck vocabulary properly - understand the ID system"""
    print("🔍 Checking French deck vocabulary properly...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get the 16 French deck IDs
        french_deck_names = [
            "12. French 01", "13. French 02", "14. French 03", "15. French 04",
            "16. French 05", "17. French 06", "18. French 07", "19. French 08",
            "20. French 09", "21. French 10", "22. French 11", "23. French 12",
            "24. French 13", "25. French 14", "26. French 15", "27. French 16"
        ]
        
        decks_result = supabase.table('vocabulary_decks').select('id, name').in_('name', french_deck_names).execute()
        
        if not decks_result.data:
            print("❌ No French decks found!")
            return
        
        french_deck_ids = [deck['id'] for deck in decks_result.data]
        print(f"🇫🇷 Found {len(french_deck_ids)} French decks")
        
        # Get ALL deck_vocabulary entries for French decks (not unique IDs)
        print(f"\n📊 Getting ALL vocabulary entries from French decks...")
        all_vocab_result = supabase.table('deck_vocabulary').select('*').in_('deck_id', french_deck_ids).execute()
        
        if not all_vocab_result.data:
            print("❌ No vocabulary entries found!")
            return
        
        total_entries = len(all_vocab_result.data)
        print(f"   • Total deck_vocabulary entries: {total_entries}")
        
        # Get unique vocabulary IDs
        unique_vocab_ids = set(item['vocabulary_id'] for item in all_vocab_result.data)
        print(f"   • Unique vocabulary IDs: {len(unique_vocab_ids)}")
        
        # Check if vocabulary IDs are global or per-deck
        print(f"\n🔍 Checking vocabulary ID system...")
        
        # Get some vocabulary entries with their actual words
        sample_entries = all_vocab_result.data[:10]
        print(f"📝 Sample deck_vocabulary entries:")
        for entry in sample_entries:
            deck_id = entry['deck_id']
            vocab_id = entry['vocabulary_id']
            
            # Get the actual vocabulary word
            vocab_result = supabase.table('vocabulary').select('language_a_word, language_b_translation').eq('id', vocab_id).execute()
            if vocab_result.data:
                word = vocab_result.data[0]
                print(f"   Deck {deck_id[:8]}... → Vocab ID {vocab_id} → '{word['language_a_word']}' → '{word['language_b_translation']}'")
        
        # Check if the same vocabulary ID appears in multiple decks
        print(f"\n🔍 Checking if vocabulary IDs are shared across decks...")
        
        # Count how many times each vocabulary ID appears
        vocab_id_counts = {}
        for entry in all_vocab_result.data:
            vocab_id = entry['vocabulary_id']
            vocab_id_counts[vocab_id] = vocab_id_counts.get(vocab_id, 0) + 1
        
        # Find vocabulary IDs that appear in multiple decks
        shared_ids = {vid: count for vid, count in vocab_id_counts.items() if count > 1}
        print(f"   • Vocabulary IDs appearing in multiple decks: {len(shared_ids)}")
        
        if shared_ids:
            print(f"   • Sample shared vocabulary IDs:")
            for i, (vocab_id, count) in enumerate(list(shared_ids.items())[:5]):
                # Get the word for this ID
                vocab_result = supabase.table('vocabulary').select('language_a_word').eq('id', vocab_id).execute()
                word = vocab_result.data[0]['language_a_word'] if vocab_result.data else 'Unknown'
                print(f"     - ID {vocab_id} ('{word}') appears in {count} decks")
        
        # Now let's check our CSV words properly
        print(f"\n🔍 Checking CSV sample words in French deck vocabulary...")
        
        csv_sample_words = ['abaissement', 'abaisser', 'abandon', 'abandonner', 'abcès', 'abnégation', 'aboi']
        
        found_count = 0
        for word in csv_sample_words:
            # Check if this word exists in vocabulary table
            vocab_result = supabase.table('vocabulary').select('id').eq('language_a_word', word.lower()).execute()
            if vocab_result.data:
                vocab_id = vocab_result.data[0]['id']
                
                # Check if this vocabulary ID is in any French deck
                if vocab_id in unique_vocab_ids:
                    found_count += 1
                    print(f"   ✅ Found: {word} (ID: {vocab_id})")
                else:
                    print(f"   ⚠️  Exists in vocabulary but not in French decks: {word} (ID: {vocab_id})")
            else:
                print(f"   ❌ Not found in vocabulary: {word}")
        
        print(f"\n📊 Summary:")
        print(f"   • Total deck_vocabulary entries: {total_entries}")
        print(f"   • Unique vocabulary IDs: {len(unique_vocab_ids)}")
        print(f"   • Vocabulary IDs shared across decks: {len(shared_ids)}")
        print(f"   • CSV sample success rate: {found_count}/{len(csv_sample_words)} ({(found_count/len(csv_sample_words)*100):.1f}%)")
        
        return total_entries, len(unique_vocab_ids), found_count
        
    except Exception as e:
        print(f"❌ Error checking French deck vocabulary: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    total_entries, unique_ids, found_count = check_french_deck_vocabulary_properly()
    print(f"\n🎯 Total entries: {total_entries}, Unique IDs: {unique_ids}, CSV matches: {found_count}")
