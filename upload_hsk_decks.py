#!/usr/bin/env python3
"""
Upload HSK 1-5 Decks to Supabase

Uploads the processed HSK vocabulary decks to Supabase with proper naming.
"""

import csv
import os
import json
from supabase import create_client, Client
from typing import List, Dict

# Supabase configuration
SUPABASE_URL = "https://ifgitxejnakfrfeiipkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"

def create_supabase_client() -> Client:
    """Create and return Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def read_hsk_csv(file_path: str) -> List[Dict]:
    """Read HSK CSV file and return vocabulary data."""
    vocabulary = []
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return vocabulary
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                vocabulary.append({
                    'language_a_word': row['chinese_word'].strip(),
                    'language_b_translation': row['english_translation'].strip(),
                    'language_a_sentence': row['chinese_sentence'].strip(),
                    'language_b_sentence': row['english_sentence'].strip()
                })
        
        print(f"📖 Loaded {len(vocabulary)} words from {file_path}")
        return vocabulary
        
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return vocabulary

def create_deck(supabase: Client, deck_name: str, language_a_name: str, language_b_name: str, total_words: int) -> int:
    """Create a new deck and return its ID."""
    try:
        deck_data = {
            'name': deck_name,
            'language_a_name': language_a_name,
            'language_b_name': language_b_name,
            'language_a_code': 'zh-CN',
            'language_b_code': 'en-US',
            'total_words': total_words,
            'is_active': True
        }
        
        response = supabase.table('vocabulary_decks').insert(deck_data).execute()
        
        if response.data:
            deck_id = response.data[0]['id']
            print(f"✅ Created deck '{deck_name}' with ID: {deck_id}")
            return deck_id
        else:
            print(f"❌ Failed to create deck '{deck_name}'")
            return None
            
    except Exception as e:
        print(f"❌ Error creating deck '{deck_name}': {e}")
        return None

def add_vocabulary_to_deck(supabase: Client, vocabulary: List[Dict]) -> List[int]:
    """Add vocabulary words to the vocabulary table and return their IDs."""
    try:
        response = supabase.table('vocabulary').insert(vocabulary).execute()
        
        if response.data:
            word_ids = [word['id'] for word in response.data]
            print(f"✅ Added {len(word_ids)} words to vocabulary table")
            return word_ids
        else:
            print(f"❌ Failed to add vocabulary words")
            return []
            
    except Exception as e:
        print(f"❌ Error adding vocabulary: {e}")
        return []

def create_deck_vocabulary_relationships(supabase: Client, deck_id: int, word_ids: List[int]):
    """Create relationships between deck and vocabulary words."""
    try:
        relationships = [{'deck_id': deck_id, 'vocabulary_id': word_id, 'word_order': i + 1} for i, word_id in enumerate(word_ids)]
        
        response = supabase.table('deck_vocabulary').insert(relationships).execute()
        
        if response.data:
            print(f"✅ Created {len(relationships)} deck-vocabulary relationships")
        else:
            print(f"❌ Failed to create deck-vocabulary relationships")
            
    except Exception as e:
        print(f"❌ Error creating relationships: {e}")

def upload_hsk_deck(hsk_level: int, supabase: Client):
    """Upload a single HSK deck."""
    print(f"\n🚀 Uploading HSK Level {hsk_level}")
    print("=" * 50)
    
    # File paths
    input_file = f"hsk_api_enhanced_vocabulary/hsk{hsk_level}_api_enhanced.csv"
    deck_name = f"HSK Level {hsk_level}"
    
    # Read vocabulary data
    vocabulary = read_hsk_csv(input_file)
    if not vocabulary:
        print(f"❌ No vocabulary found for HSK {hsk_level}")
        return False
    
    # Create deck
    deck_id = create_deck(
        supabase=supabase,
        deck_name=deck_name,
        language_a_name="Chinese",
        language_b_name="English",
        total_words=len(vocabulary)
    )
    
    if not deck_id:
        return False
    
    # Add vocabulary words
    word_ids = add_vocabulary_to_deck(supabase, vocabulary)
    if not word_ids:
        return False
    
    # Create relationships
    create_deck_vocabulary_relationships(supabase, deck_id, word_ids)
    
    print(f"🎉 HSK Level {hsk_level} upload complete!")
    return True

def main():
    """Main function to upload all HSK decks."""
    print("🎯 Uploading HSK 1-5 Decks to Supabase")
    print("=" * 60)
    
    # Create Supabase client
    supabase = create_supabase_client()
    
    # Check if output directory exists
    if not os.path.exists("hsk_api_enhanced_vocabulary"):
        print("❌ hsk_api_enhanced_vocabulary directory not found")
        return
    
    # Upload each HSK level
    success_count = 0
    for hsk_level in [1, 2, 3, 4, 5]:
        if upload_hsk_deck(hsk_level, supabase):
            success_count += 1
    
    # Summary
    print(f"\n🎉 Upload Complete!")
    print("=" * 60)
    print(f"✅ Successfully uploaded: {success_count}/5 HSK decks")
    
    if success_count == 5:
        print("🎊 All HSK decks uploaded successfully!")
    else:
        print(f"⚠️  {5 - success_count} decks failed to upload")

if __name__ == "__main__":
    main()
