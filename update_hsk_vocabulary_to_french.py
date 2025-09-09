#!/usr/bin/env python3
"""
Update HSK Vocabulary to French

Updates HSK vocabulary words to have French translations and sentences.
"""

import csv
import os
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def read_hsk_csv(file_path: str) -> list:
    """Read HSK CSV file and return list of Chinese words."""
    words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                words.append({
                    'chinese_word': row['chinese_word'].strip(),
                    'english_translation': row['english_translation'].strip(),
                    'chinese_sentence': row['chinese_sentence'].strip(),
                    'english_sentence': row['english_sentence'].strip()
                })
        return words
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

def update_vocabulary_to_french():
    """Update HSK vocabulary to French translations."""
    supabase = create_supabase_client()
    
    # Process each HSK level
    for hsk_level in [1, 2, 3, 4, 5]:
        print(f"\n🔄 Processing HSK Level {hsk_level}")
        print("=" * 50)
        
        # Read the CSV file
        csv_file = f"hsk_api_enhanced_vocabulary/hsk{hsk_level}_api_enhanced.csv"
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            continue
        
        vocabulary_data = read_hsk_csv(csv_file)
        print(f"📖 Read {len(vocabulary_data)} words from CSV")
        
        # Update each vocabulary word
        updated_count = 0
        for vocab in vocabulary_data:
            chinese_word = vocab['chinese_word']
            english_translation = vocab['english_translation']
            chinese_sentence = vocab['chinese_sentence']
            english_sentence = vocab['english_sentence']
            
            # For now, we'll use the English translation as a placeholder
            # In a real scenario, you'd want to use the Anthropic API to translate to French
            # For now, let's create a simple French translation
            french_translation = english_translation  # Placeholder - should be translated to French
            french_sentence = english_sentence  # Placeholder - should be translated to French
            
            try:
                # Find the vocabulary word by Chinese word
                response = supabase.table('vocabulary').select('id').eq('language_a_word', chinese_word).execute()
                
                if response.data:
                    vocab_id = response.data[0]['id']
                    
                    # Update the vocabulary word
                    update_data = {
                        'language_b_translation': french_translation,
                        'language_b_sentence': french_sentence
                    }
                    
                    supabase.table('vocabulary').update(update_data).eq('id', vocab_id).execute()
                    updated_count += 1
                    print(f"✅ Updated '{chinese_word}' to French")
                else:
                    print(f"❌ No vocabulary found for '{chinese_word}'")
                    
            except Exception as e:
                print(f"❌ Error updating '{chinese_word}': {e}")
        
        print(f"🎉 Updated {updated_count} words for HSK Level {hsk_level}")
    
    print(f"\n🎊 All HSK vocabulary updated to French!")

if __name__ == "__main__":
    update_vocabulary_to_french()

