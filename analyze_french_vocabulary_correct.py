#!/usr/bin/env python3
"""
Corrected Analysis of French Vocabulary - Investigating Language Fields
"""

from supabase import create_client, Client
from collections import defaultdict

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

def investigate_vocabulary_structure():
    """Investigate the vocabulary table structure and language fields."""
    
    print("🔍 INVESTIGATING VOCABULARY TABLE STRUCTURE")
    print("="*60)
    
    try:
        # First, let's understand the vocabulary table structure
        print("📋 Sample vocabulary entries to understand structure:")
        sample_response = supabase.table('vocabulary').select('*').limit(5).execute()
        
        if sample_response.data:
            for i, item in enumerate(sample_response.data, 1):
                print(f"   Entry {i}:")
                for key, value in item.items():
                    print(f"     {key}: {value}")
                print()
        
        # Now let's look at French deck language configuration
        print("📚 French deck language configuration:")
        french_deck_response = supabase.table('vocabulary_decks').select('id, name, language_a_name, language_b_name, language_a_code, language_b_code').like('name', '%. French %').execute()
        
        if french_deck_response.data:
            for deck in french_deck_response.data:
                print(f"   {deck['name']}:")
                print(f"     Language A: {deck['language_a_name']} ({deck['language_a_code']})")
                print(f"     Language B: {deck['language_b_name']} ({deck['language_b_code']})")
                print()
        
        # Let's check which language field contains French words
        print("🔍 Checking vocabulary entries from a French deck:")
        
        # Get one French deck
        french_deck = french_deck_response.data[0]
        deck_id = french_deck['id']
        
        # Get some vocabulary from this deck
        deck_vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id').eq('deck_id', deck_id).limit(10).execute()
        
        if deck_vocab_response.data:
            vocab_ids = [item['vocabulary_id'] for item in deck_vocab_response.data]
            
            # Get vocabulary details
            vocab_details_response = supabase.table('vocabulary').select('*').in_('id', vocab_ids).execute()
            
            if vocab_details_response.data:
                print(f"   Sample entries from {french_deck['name']}:")
                for item in vocab_details_response.data:
                    print(f"     ID {item['id']}:")
                    print(f"       language_a_word: '{item['language_a_word']}'")
                    print(f"       language_b_translation: '{item['language_b_translation']}'")
                    print(f"       language_a_sentence: '{item['language_a_sentence'][:50]}...'")
                    print(f"       language_b_sentence: '{item['language_b_sentence'][:50]}...'")
                    print()
        
        return french_deck_response.data
        
    except Exception as e:
        print(f"❌ Error during investigation: {e}")
        return None

def analyze_french_vocabulary_correct():
    """Analyze French vocabulary using the correct language field."""
    
    print("\n🚀 CORRECTED FRENCH VOCABULARY ANALYSIS")
    print("="*60)
    
    try:
        # Get French decks with their language configuration
        french_deck_response = supabase.table('vocabulary_decks').select('id, name, language_a_name, language_b_name').like('name', '%. French %').execute()
        
        if not french_deck_response.data:
            print("❌ No French decks found")
            return
        
        french_decks = french_deck_response.data
        print(f"✅ Found {len(french_decks)} French decks")
        
        # Determine which language field contains French
        # Based on the deck names, French should be the target language
        sample_deck = french_decks[0]
        print(f"\n📋 Language configuration for {sample_deck['name']}:")
        print(f"   Language A: {sample_deck['language_a_name']}")
        print(f"   Language B: {sample_deck['language_b_name']}")
        
        # French is likely in language_b_name (target language)
        # Let's verify by checking a few entries
        deck_id = sample_deck['id']
        deck_vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id').eq('deck_id', deck_id).limit(5).execute()
        
        if deck_vocab_response.data:
            vocab_ids = [item['vocabulary_id'] for item in deck_vocab_response.data]
            vocab_details_response = supabase.table('vocabulary').select('*').in_('id', vocab_ids).execute()
            
            if vocab_details_response.data:
                print(f"\n🔍 Sample entries to determine French field:")
                for item in vocab_details_response.data:
                    print(f"   language_a_word: '{item['language_a_word']}'")
                    print(f"   language_b_translation: '{item['language_b_translation']}'")
                    print()
        
        # Based on the investigation, French words are likely in language_b_translation
        # Let's proceed with this assumption and analyze all French vocabulary
        
        print(f"\n📊 ANALYZING ALL FRENCH VOCABULARY:")
        
        # Get all vocabulary IDs from all French decks
        all_vocab_ids = set()
        deck_stats = []
        
        for deck in french_decks:
            deck_vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id', count='exact').eq('deck_id', deck['id']).execute()
            vocab_count = deck_vocab_response.count or 0
            
            deck_stats.append({
                'name': deck['name'],
                'id': deck['id'],
                'vocab_count': vocab_count
            })
            
            if deck_vocab_response.data:
                for item in deck_vocab_response.data:
                    all_vocab_ids.add(item['vocabulary_id'])
        
        print(f"   Total unique vocabulary IDs: {len(all_vocab_ids)}")
        
        # Get French vocabulary (assuming it's in language_b_translation)
        print(f"   Fetching French vocabulary details in batches...")
        french_vocabulary = []
        batch_size = 1000
        all_vocab_ids_list = list(all_vocab_ids)
        
        for i in range(0, len(all_vocab_ids_list), batch_size):
            batch_ids = all_vocab_ids_list[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(all_vocab_ids_list) + batch_size - 1)//batch_size}")
            
            vocab_response = supabase.table('vocabulary').select('id, language_b_translation').in_('id', batch_ids).execute()
            if vocab_response.data:
                french_vocabulary.extend(vocab_response.data)
        
        print(f"   Retrieved {len(french_vocabulary)} French vocabulary entries")
        
        # Analyze French vocabulary characteristics
        print(f"\n📊 FRENCH VOCABULARY CHARACTERISTICS:")
        
        # Word length analysis
        word_lengths = [len(item['language_b_translation']) for item in french_vocabulary]
        avg_length = sum(word_lengths) / len(word_lengths)
        min_length = min(word_lengths)
        max_length = max(word_lengths)
        
        print(f"   Average word length: {avg_length:.1f} characters")
        print(f"   Shortest word: {min_length} characters")
        print(f"   Longest word: {max_length} characters")
        
        # Sample French vocabulary
        print(f"\n📝 SAMPLE FRENCH VOCABULARY WORDS:")
        sample_words = french_vocabulary[:20]
        for i, item in enumerate(sample_words, 1):
            print(f"   {i:2d}. '{item['language_b_translation']}' (ID: {item['id']})")
        
        if len(french_vocabulary) > 20:
            print(f"   ... and {len(french_vocabulary)-20} more words")
        
        # Check for duplicates
        word_counts = defaultdict(int)
        for item in french_vocabulary:
            word_counts[item['language_b_translation']] += 1
        
        duplicates = {word: count for word, count in word_counts.items() if count > 1}
        if duplicates:
            print(f"\n⚠️  DUPLICATE FRENCH WORDS FOUND:")
            for word, count in list(duplicates.items())[:10]:
                print(f"   '{word}': appears {count} times")
            if len(duplicates) > 10:
                print(f"   ... and {len(duplicates)-10} more duplicates")
        else:
            print(f"\n✅ NO DUPLICATE FRENCH WORDS FOUND")
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 SUMMARY:")
        print(f"   French decks: {len(french_decks)}")
        print(f"   Total vocabulary entries: {sum(deck['vocab_count'] for deck in deck_stats)}")
        print(f"   Unique French vocabulary words: {len(french_vocabulary)}")
        print(f"   Duplicate entries: {sum(deck['vocab_count'] for deck in deck_stats) - len(french_vocabulary)}")
        
        return {
            'total_decks': len(french_decks),
            'total_vocabulary_entries': sum(deck['vocab_count'] for deck in deck_stats),
            'unique_french_vocabulary': len(french_vocabulary),
            'duplicate_entries': sum(deck['vocab_count'] for deck in deck_stats) - len(french_vocabulary),
            'deck_stats': deck_stats,
            'french_vocabulary': french_vocabulary
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

if __name__ == "__main__":
    # First investigate the structure
    decks = investigate_vocabulary_structure()
    
    if decks:
        # Then do the corrected analysis
        results = analyze_french_vocabulary_correct()
        if results:
            print(f"\n✅ Analysis complete!")
        else:
            print(f"\n❌ Analysis failed!")
    else:
        print(f"\n❌ Investigation failed!")
