#!/usr/bin/env python3
"""
French Vocabulary Migration Script
Migrates all French vocabulary decks from the vocab bank to Supabase
"""

import sqlite3
import os
import sys
from supabase import create_client, Client
from typing import List, Dict, Any
import json
from datetime import datetime
from dotenv import load_dotenv

# Initialize Supabase client
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

# French vocabulary files in order
FRENCH_DECKS = [
    # Pre-vocabulary batches (foundational) - French 1, 2, 3
    ("pre_vocab_batch_1.db", "French 1", "Basic French vocabulary - Part 1"),
    ("pre_vocab_batch_2.db", "French 2", "Basic French vocabulary - Part 2"),
    ("pre_vocab_batch_3.db", "French 3", "Basic French vocabulary - Part 3"),
    
    # Main vocabulary batches - French 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
    ("french_vocab_batch_1.db", "French 4", "French vocabulary - Batch 1"),
    ("french_vocab_batch_2.db", "French 5", "French vocabulary - Batch 2"),
    ("french_vocab_batch_3.db", "French 6", "French vocabulary - Batch 3"),
    ("french_vocab_batch_4.db", "French 7", "French vocabulary - Batch 4"),
    ("french_vocab_batch_5.db", "French 8", "French vocabulary - Batch 5"),
    ("french_vocab_batch_6.db", "French 9", "French vocabulary - Batch 6"),
    ("french_vocab_batch_7.db", "French 10", "French vocabulary - Batch 7"),
    ("french_vocab_batch_8.db", "French 11", "French vocabulary - Batch 8"),
    ("french_vocab_batch_9.db", "French 12", "French vocabulary - Batch 9"),
    ("french_vocab_batch_10.db", "French 13", "French vocabulary - Batch 10"),
    ("french_vocab_batch_11.db", "French 14", "French vocabulary - Batch 11"),
    ("french_vocab_batch_12.db", "French 15", "French vocabulary - Batch 12"),
    ("french_vocab_batch_13.db", "French 16", "French vocabulary - Batch 13"),
]

VOCAB_BANK_PATH = "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank"

def connect_to_supabase() -> Client:
    """Connect to Supabase"""
    try:
        print("✅ Connected to Supabase")
        return supabase
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)

def read_vocabulary_from_db(db_path: str) -> List[Dict[str, Any]]:
    """Read vocabulary from SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT word_number, french_word, english_translation, 
                   example_sentence, sentence_translation
            FROM vocabulary 
            ORDER BY word_number
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        vocabulary = []
        for row in rows:
            vocab_item = {
                "language_a_word": row[1],  # French word
                "language_b_translation": row[2],  # English translation
                "language_a_sentence": row[3],  # French example sentence
                "language_b_sentence": row[4],  # English sentence translation
            }
            vocabulary.append(vocab_item)
        
        print(f"📖 Read {len(vocabulary)} words from {os.path.basename(db_path)}")
        return vocabulary
        
    except Exception as e:
        print(f"❌ Error reading {db_path}: {e}")
        return []

def create_deck(supabase: Client, name: str, description: str) -> str:
    """Create a new deck in Supabase"""
    try:
        deck_data = {
            "name": name,
            "description": description,
            "language_a_code": "fr-FR",
            "language_b_code": "en-US",
            "language_a_name": "French",
            "language_b_name": "English",
            "total_words": 0  # Will be updated after adding vocabulary
        }
        
        result = supabase.table("vocabulary_decks").insert(deck_data).execute()
        deck_id = result.data[0]["id"]
        print(f"✅ Created deck: {name} (ID: {deck_id})")
        return deck_id
        
    except Exception as e:
        print(f"❌ Error creating deck {name}: {e}")
        return None

def add_vocabulary_to_deck(supabase: Client, deck_id: str, vocabulary: List[Dict[str, Any]]) -> int:
    """Add vocabulary to the vocabulary table"""
    try:
        # Prepare vocabulary data (no deck_id needed)
        vocab_data = []
        for vocab in vocabulary:
            vocab_item = {
                "language_a_word": vocab["language_a_word"],
                "language_b_translation": vocab["language_b_translation"],
                "language_a_sentence": vocab["language_a_sentence"],
                "language_b_sentence": vocab["language_b_sentence"]
            }
            vocab_data.append(vocab_item)
        
        # Insert vocabulary in batches
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(vocab_data), batch_size):
            batch = vocab_data[i:i + batch_size]
            result = supabase.table("vocabulary").insert(batch).execute()
            total_inserted += len(result.data)
            print(f"📝 Inserted batch {i//batch_size + 1}: {len(batch)} words")
        
        # Update deck total_words
        supabase.table("vocabulary_decks").update({"total_words": total_inserted}).eq("id", deck_id).execute()
        
        print(f"✅ Added {total_inserted} words to vocabulary table")
        return total_inserted
        
    except Exception as e:
        print(f"❌ Error adding vocabulary: {e}")
        return 0

def main():
    """Main migration function"""
    print("🚀 Starting French Vocabulary Migration")
    print("=" * 50)
    
    # Connect to Supabase
    supabase = connect_to_supabase()
    
    total_decks = 0
    total_words = 0
    
    # Process each deck in order
    for db_file, deck_name, deck_description in FRENCH_DECKS:
        db_path = os.path.join(VOCAB_BANK_PATH, db_file)
        
        if not os.path.exists(db_path):
            print(f"⚠️  Skipping {db_file} - file not found")
            continue
        
        print(f"\n📚 Processing: {deck_name}")
        print("-" * 30)
        
        # Read vocabulary from SQLite
        vocabulary = read_vocabulary_from_db(db_path)
        
        if not vocabulary:
            print(f"⚠️  No vocabulary found in {db_file}")
            continue
        
        # Create deck in Supabase
        deck_id = create_deck(supabase, deck_name, deck_description)
        
        if not deck_id:
            print(f"❌ Failed to create deck for {db_file}")
            continue
        
        # Add vocabulary to deck
        words_added = add_vocabulary_to_deck(supabase, deck_id, vocabulary)
        
        if words_added > 0:
            total_decks += 1
            total_words += words_added
        
        print(f"✅ Completed: {deck_name} - {words_added} words")
    
    print("\n" + "=" * 50)
    print(f"🎉 Migration Complete!")
    print(f"📊 Total decks created: {total_decks}")
    print(f"📊 Total words migrated: {total_words}")
    print("=" * 50)

if __name__ == "__main__":
    main()
