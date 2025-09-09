#!/usr/bin/env python3
"""
Create HSK Deck Relationships Properly

Creates deck-vocabulary relationships by reading CSV files and matching vocabulary words.
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
                words.append(row['chinese_word'].strip())
        return words
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

def create_hsk_deck_relationships():
    """Create relationships for HSK decks by matching vocabulary words."""
    supabase = create_supabase_client()
    
    # HSK deck configurations
    hsk_configs = [
        (1, "cac171fc-c2d0-430d-92cd-849e4fe4ee73", 113),
        (2, "a77f89e8-f5c6-4c29-94e1-61440f63fdbf", 217),
        (3, "e3506b2b-9e0b-4141-9052-e87c3980e574", 406),
        (4, "64bc906f-ba97-4c7e-adbf-887756aacf28", 756),
        (5, "1d20e18a-e3d9-4b5b-b759-58bced617674", 756)
    ]
    
    for hsk_level, deck_id, expected_words in hsk_configs:
        print(f"\n🔧 Creating relationships for HSK Level {hsk_level}")
        print("=" * 50)
        
        # Read the CSV file
        csv_file = f"hsk_api_enhanced_vocabulary/hsk{hsk_level}_api_enhanced.csv"
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            continue
        
        chinese_words = read_hsk_csv(csv_file)
        print(f"📖 Read {len(chinese_words)} words from CSV")
        
        if len(chinese_words) != expected_words:
            print(f"⚠️  Expected {expected_words} words, got {len(chinese_words)}")
        
        # Get vocabulary IDs for these Chinese words
        word_ids = []
        for i, chinese_word in enumerate(chinese_words):
            try:
                response = supabase.table('vocabulary').select('id').eq('language_a_word', chinese_word).execute()
                if response.data:
                    word_id = response.data[0]['id']
                    word_ids.append(word_id)
                    print(f"✅ Found vocabulary ID {word_id} for '{chinese_word}'")
                else:
                    print(f"❌ No vocabulary found for '{chinese_word}'")
            except Exception as e:
                print(f"❌ Error finding vocabulary for '{chinese_word}': {e}")
        
        print(f"📊 Found {len(word_ids)} vocabulary IDs out of {len(chinese_words)} words")
        
        if word_ids:
            # Create relationships
            relationships = []
            for i, word_id in enumerate(word_ids):
                relationships.append({
                    'deck_id': deck_id,
                    'vocabulary_id': word_id,
                    'word_order': i + 1
                })
            
            try:
                # Delete any existing relationships for this deck
                supabase.table('deck_vocabulary').delete().eq('deck_id', deck_id).execute()
                print(f"🗑️  Deleted existing relationships for HSK Level {hsk_level}")
                
                # Insert new relationships
                response = supabase.table('deck_vocabulary').insert(relationships).execute()
                
                if response.data:
                    print(f"✅ Created {len(relationships)} relationships for HSK Level {hsk_level}")
                else:
                    print(f"❌ Failed to create relationships for HSK Level {hsk_level}")
                    
            except Exception as e:
                print(f"❌ Error creating relationships for HSK Level {hsk_level}: {e}")
        else:
            print(f"❌ No vocabulary IDs found for HSK Level {hsk_level}")
    
    print(f"\n🎊 HSK deck relationships creation complete!")

if __name__ == "__main__":
    create_hsk_deck_relationships()

