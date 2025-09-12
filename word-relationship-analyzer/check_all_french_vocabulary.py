#!/usr/bin/env python3
"""
Check all French vocabulary in the database, not just the French decks.
This will help us understand if there are more French words available.
"""

import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def check_all_french_vocabulary():
    """Check all French vocabulary in the database"""
    print("🔍 Checking ALL French vocabulary in the database...")
    print("=" * 60)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get all vocabulary that might be French
        # Look for words that contain French characters or patterns
        print("📚 Searching for French vocabulary patterns...")
        
        # Get a sample of vocabulary to analyze
        vocab_result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').limit(1000).execute()
        
        if not vocab_result.data:
            print("❌ No vocabulary found!")
            return
        
        print(f"📊 Analyzing {len(vocab_result.data)} vocabulary entries...")
        
        # Look for French words (words with accents, common French patterns)
        french_words = []
        french_patterns = ['é', 'è', 'ê', 'ë', 'à', 'â', 'ä', 'ç', 'î', 'ï', 'ô', 'ö', 'ù', 'û', 'ü', 'ÿ']
        
        for vocab in vocab_result.data:
            word = vocab['language_a_word']
            if any(pattern in word for pattern in french_patterns):
                french_words.append(vocab)
        
        print(f"🇫🇷 Found {len(french_words)} potential French words with accents:")
        
        # Show sample French words
        for i, vocab in enumerate(french_words[:10]):
            print(f"   {i+1}. ID {vocab['id']}: {vocab['language_a_word']} → {vocab['language_b_translation']}")
        
        if len(french_words) > 10:
            print(f"   ... and {len(french_words) - 10} more")
        
        # Check if any of our CSV words exist
        print(f"\n🔍 Checking if CSV words exist in vocabulary...")
        
        # Sample words from our CSV
        csv_sample_words = ['abaissement', 'abaisser', 'abandon', 'abandonner', 'abcès', 'abnégation', 'aboi']
        
        found_words = []
        for word in csv_sample_words:
            result = supabase.table('vocabulary').select('id, language_a_word, language_b_translation').eq('language_a_word', word.lower()).execute()
            if result.data:
                found_words.append((word, result.data[0]))
                print(f"   ✅ Found: {word} → ID {result.data[0]['id']}")
            else:
                print(f"   ❌ Not found: {word}")
        
        print(f"\n📊 Summary:")
        print(f"   • Total vocabulary analyzed: {len(vocab_result.data)}")
        print(f"   • French words with accents: {len(french_words)}")
        print(f"   • CSV sample words found: {len(found_words)}/{len(csv_sample_words)}")
        
        if len(found_words) == 0:
            print(f"\n💡 Recommendation:")
            print(f"   The CSV contains French words that aren't in your current Supabase vocabulary.")
            print(f"   You may need to:")
            print(f"   1. Import more French vocabulary from the original SQLite databases")
            print(f"   2. Or use the CSV data directly without Supabase integration")
            print(f"   3. Or create a separate similarity table that references the CSV data")
        
        return found_words
        
    except Exception as e:
        print(f"❌ Error checking French vocabulary: {e}")
        return []

if __name__ == "__main__":
    found_words = check_all_french_vocabulary()
    if found_words:
        print(f"\n🎯 Found {len(found_words)} CSV words in current vocabulary!")
    else:
        print(f"\n⚠️  No CSV words found in current vocabulary.")
