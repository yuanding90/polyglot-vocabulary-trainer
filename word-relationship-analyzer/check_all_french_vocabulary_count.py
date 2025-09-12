#!/usr/bin/env python3
"""
Check how many French words exist in the entire vocabulary table.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_all_french_vocabulary_count():
    """Check total French vocabulary count in the entire database"""
    print("🔍 Checking ALL French vocabulary in entire database...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get total vocabulary count
        total_result = supabase.table('vocabulary').select('*', count='exact').execute()
        print(f"📊 Total vocabulary entries in database: {total_result.count}")
        
        # Get French words by looking for French accent patterns
        french_patterns = ['é', 'è', 'ê', 'ë', 'à', 'â', 'ä', 'ç', 'î', 'ï', 'ô', 'ö', 'ù', 'û', 'ü', 'ÿ']
        
        print(f"\n🇫🇷 Searching for French words with accent patterns...")
        
        # Get all vocabulary and filter for French patterns
        all_vocab_result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').execute()
        
        if not all_vocab_result.data:
            print("❌ No vocabulary found!")
            return
        
        french_words = []
        for vocab in all_vocab_result.data:
            word = vocab['language_a_word']
            if any(pattern in word for pattern in french_patterns):
                french_words.append(vocab)
        
        print(f"📊 Found {len(french_words)} French words with accent patterns")
        
        # Show sample French words
        print(f"\n📝 Sample French words from entire database:")
        for i, vocab in enumerate(french_words[:15]):
            print(f"   {i+1:2d}. ID {vocab['id']}: {vocab['language_a_word']} → {vocab['language_b_translation']}")
        
        if len(french_words) > 15:
            print(f"   ... and {len(french_words) - 15} more")
        
        # Check CSV sample words against ALL French vocabulary
        print(f"\n🔍 Checking CSV sample words against ALL French vocabulary...")
        
        csv_sample_words = ['abaissement', 'abaisser', 'abandon', 'abandonner', 'abcès', 'abnégation', 'aboi']
        
        found_count = 0
        for word in csv_sample_words:
            vocab_result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').eq('language_a_word', word.lower()).execute()
            if vocab_result.data:
                vocab = vocab_result.data[0]
                found_count += 1
                print(f"   ✅ Found: {word} → ID {vocab['id']} → '{vocab['language_b_translation']}'")
            else:
                print(f"   ❌ Not found: {word}")
        
        print(f"\n📊 Summary:")
        print(f"   • Total vocabulary in database: {total_result.count}")
        print(f"   • French words with accents: {len(french_words)}")
        print(f"   • CSV sample words found: {found_count}/{len(csv_sample_words)}")
        print(f"   • Success rate: {(found_count/len(csv_sample_words)*100):.1f}%")
        
        return len(french_words), found_count
        
    except Exception as e:
        print(f"❌ Error checking French vocabulary: {e}")
        return 0, 0

if __name__ == "__main__":
    french_count, found_count = check_all_french_vocabulary_count()
    print(f"\n🎯 French words with accents: {french_count}, CSV matches: {found_count}")
