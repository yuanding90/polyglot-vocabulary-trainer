#!/usr/bin/env python3
"""
Comprehensive Analysis of All French Vocabulary Across All 16 Decks
"""

from supabase import create_client, Client
from collections import defaultdict

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

def analyze_all_french_vocabulary():
    """Analyze all French vocabulary across all 16 French decks."""
    
    print("🚀 COMPREHENSIVE FRENCH VOCABULARY ANALYSIS")
    print("="*60)
    
    try:
        # Get all French decks
        print("📚 Fetching French deck information...")
        french_deck_response = supabase.table('vocabulary_decks').select('*').like('name', '%. French %').execute()
        
        if not french_deck_response.data:
            print("❌ No French decks found")
            return
        
        french_decks = french_deck_response.data
        print(f"✅ Found {len(french_decks)} French decks")
        
        # Display deck information
        print(f"\n📋 FRENCH DECKS OVERVIEW:")
        for deck in french_decks:
            print(f"   {deck['name']} (ID: {deck['id'][:8]}...)")
        
        # Get vocabulary counts per deck
        print(f"\n📊 VOCABULARY COUNTS PER DECK:")
        total_vocabulary = 0
        deck_stats = []
        
        for deck in french_decks:
            # Get vocabulary count for this deck
            vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id', count='exact').eq('deck_id', deck['id']).execute()
            vocab_count = vocab_response.count or 0
            
            deck_stats.append({
                'name': deck['name'],
                'id': deck['id'],
                'vocab_count': vocab_count
            })
            
            total_vocabulary += vocab_count
            print(f"   {deck['name']}: {vocab_count} words")
        
        print(f"\n📈 TOTAL VOCABULARY ACROSS ALL DECKS: {total_vocabulary} words")
        
        # Get unique vocabulary across all decks
        print(f"\n🔍 ANALYZING UNIQUE VOCABULARY...")
        
        # Get all vocabulary IDs from all French decks
        all_vocab_ids = set()
        for deck in french_decks:
            deck_vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id').eq('deck_id', deck['id']).execute()
            if deck_vocab_response.data:
                for item in deck_vocab_response.data:
                    all_vocab_ids.add(item['vocabulary_id'])
        
        print(f"   Total unique vocabulary IDs: {len(all_vocab_ids)}")
        
        # Get vocabulary details for all unique IDs (in batches)
        print(f"   Fetching vocabulary details in batches...")
        vocabulary_details = []
        batch_size = 1000
        all_vocab_ids_list = list(all_vocab_ids)
        
        for i in range(0, len(all_vocab_ids_list), batch_size):
            batch_ids = all_vocab_ids_list[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(all_vocab_ids_list) + batch_size - 1)//batch_size}")
            
            vocab_response = supabase.table('vocabulary').select('id, language_a_word').in_('id', batch_ids).execute()
            if vocab_response.data:
                vocabulary_details.extend(vocab_response.data)
        
        if not vocabulary_details:
            print("❌ No vocabulary details found")
            return
        
        print(f"   Retrieved {len(vocabulary_details)} vocabulary entries")
        
        # Analyze vocabulary characteristics
        print(f"\n📊 VOCABULARY CHARACTERISTICS:")
        
        # Word length analysis
        word_lengths = [len(item['language_a_word']) for item in vocabulary_details]
        avg_length = sum(word_lengths) / len(word_lengths)
        min_length = min(word_lengths)
        max_length = max(word_lengths)
        
        print(f"   Average word length: {avg_length:.1f} characters")
        print(f"   Shortest word: {min_length} characters")
        print(f"   Longest word: {max_length} characters")
        
        # Length distribution
        length_dist = defaultdict(int)
        for length in word_lengths:
            length_dist[length] += 1
        
        print(f"   Length distribution:")
        for length in sorted(length_dist.keys()):
            count = length_dist[length]
            percentage = count / len(word_lengths) * 100
            print(f"     {length} chars: {count} words ({percentage:.1f}%)")
        
        # Sample vocabulary
        print(f"\n📝 SAMPLE VOCABULARY WORDS:")
        sample_words = vocabulary_details[:20]
        for i, item in enumerate(sample_words, 1):
            print(f"   {i:2d}. '{item['language_a_word']}' (ID: {item['id']})")
        
        if len(vocabulary_details) > 20:
            print(f"   ... and {len(vocabulary_details)-20} more words")
        
        # Check for duplicates
        word_counts = defaultdict(int)
        for item in vocabulary_details:
            word_counts[item['language_a_word']] += 1
        
        duplicates = {word: count for word, count in word_counts.items() if count > 1}
        if duplicates:
            print(f"\n⚠️  DUPLICATE WORDS FOUND:")
            for word, count in list(duplicates.items())[:10]:
                print(f"   '{word}': appears {count} times")
            if len(duplicates) > 10:
                print(f"   ... and {len(duplicates)-10} more duplicates")
        else:
            print(f"\n✅ NO DUPLICATE WORDS FOUND")
        
        # Summary
        print(f"\n" + "="*60)
        print(f"📊 SUMMARY:")
        print(f"   French decks: {len(french_decks)}")
        print(f"   Total vocabulary entries: {total_vocabulary}")
        print(f"   Unique vocabulary words: {len(vocabulary_details)}")
        print(f"   Duplicate entries: {total_vocabulary - len(vocabulary_details)}")
        print(f"   Average words per deck: {total_vocabulary / len(french_decks):.1f}")
        
        return {
            'total_decks': len(french_decks),
            'total_vocabulary_entries': total_vocabulary,
            'unique_vocabulary_words': len(vocabulary_details),
            'duplicate_entries': total_vocabulary - len(vocabulary_details),
            'deck_stats': deck_stats,
            'vocabulary_details': vocabulary_details
        }
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return None

if __name__ == "__main__":
    results = analyze_all_french_vocabulary()
    if results:
        print(f"\n✅ Analysis complete!")
    else:
        print(f"\n❌ Analysis failed!")
