#!/usr/bin/env python3
"""
Fix French Deck Relationships Script
Creates deck_vocabulary relationships for French decks
"""

import sqlite3
import os
from supabase import create_client, Client
from typing import List, Dict, Any

# Initialize Supabase client
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

# French vocabulary files in order
FRENCH_DECKS = [
    # Pre-vocabulary batches (foundational) - French 1, 2, 3
    ("pre_vocab_batch_1.db", "French 1"),
    ("pre_vocab_batch_2.db", "French 2"),
    ("pre_vocab_batch_3.db", "French 3"),
    
    # Main vocabulary batches - French 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16
    ("french_vocab_batch_1.db", "French 4"),
    ("french_vocab_batch_2.db", "French 5"),
    ("french_vocab_batch_3.db", "French 6"),
    ("french_vocab_batch_4.db", "French 7"),
    ("french_vocab_batch_5.db", "French 8"),
    ("french_vocab_batch_6.db", "French 9"),
    ("french_vocab_batch_7.db", "French 10"),
    ("french_vocab_batch_8.db", "French 11"),
    ("french_vocab_batch_9.db", "French 12"),
    ("french_vocab_batch_10.db", "French 13"),
    ("french_vocab_batch_11.db", "French 14"),
    ("french_vocab_batch_12.db", "French 15"),
    ("french_vocab_batch_13.db", "French 16"),
]

VOCAB_BANK_PATH = "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank"

def get_deck_id(deck_name: str) -> str:
    """Get deck ID by name"""
    try:
        result = supabase.table("vocabulary_decks").select("id").eq("name", deck_name).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]["id"]
        else:
            print(f"❌ Deck not found: {deck_name}")
            return None
    except Exception as e:
        print(f"❌ Error getting deck ID for {deck_name}: {e}")
        return None

def get_vocabulary_ids(french_words: List[str]) -> List[int]:
    """Get vocabulary IDs by French words"""
    try:
        # Get vocabulary IDs for the French words
        result = supabase.table("vocabulary").select("id").in_("language_a_word", french_words).execute()
        if result.data:
            return [item["id"] for item in result.data]
        else:
            print(f"❌ No vocabulary found for {len(french_words)} French words")
            return []
    except Exception as e:
        print(f"❌ Error getting vocabulary IDs: {e}")
        return []

def read_french_words_from_db(db_path: str) -> List[str]:
    """Read French words from SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT french_word FROM vocabulary ORDER BY word_number")
        rows = cursor.fetchall()
        conn.close()
        
        french_words = [row[0] for row in rows]
        print(f"📖 Read {len(french_words)} French words from {os.path.basename(db_path)}")
        return french_words
        
    except Exception as e:
        print(f"❌ Error reading {db_path}: {e}")
        return []

def create_deck_vocabulary_relationships(deck_id: str, vocabulary_ids: List[int]) -> int:
    """Create deck_vocabulary relationships"""
    try:
        # Prepare relationship data
        relationships = []
        for i, vocab_id in enumerate(vocabulary_ids):
            relationship = {
                "deck_id": deck_id,
                "vocabulary_id": vocab_id,
                "word_order": i + 1
            }
            relationships.append(relationship)
        
        # Insert relationships in batches
        batch_size = 100
        total_inserted = 0
        
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i + batch_size]
            result = supabase.table("deck_vocabulary").insert(batch).execute()
            total_inserted += len(result.data)
            print(f"📝 Inserted batch {i//batch_size + 1}: {len(batch)} relationships")
        
        print(f"✅ Created {total_inserted} deck-vocabulary relationships")
        return total_inserted
        
    except Exception as e:
        print(f"❌ Error creating relationships: {e}")
        return 0

def main():
    """Main function"""
    print("🔧 Fixing French Deck Relationships")
    print("=" * 50)
    
    total_relationships = 0
    
    # Process each deck
    for db_file, deck_name in FRENCH_DECKS:
        db_path = os.path.join(VOCAB_BANK_PATH, db_file)
        
        if not os.path.exists(db_path):
            print(f"⚠️  Skipping {db_file} - file not found")
            continue
        
        print(f"\n📚 Processing: {deck_name}")
        print("-" * 30)
        
        # Get deck ID
        deck_id = get_deck_id(deck_name)
        if not deck_id:
            continue
        
        # Read French words from SQLite
        french_words = read_french_words_from_db(db_path)
        if not french_words:
            continue
        
        # Get vocabulary IDs
        vocabulary_ids = get_vocabulary_ids(french_words)
        if not vocabulary_ids:
            print(f"⚠️  No vocabulary IDs found for {deck_name}")
            continue
        
        print(f"Found {len(vocabulary_ids)} vocabulary IDs for {len(french_words)} French words")
        
        # Create deck-vocabulary relationships
        relationships_created = create_deck_vocabulary_relationships(deck_id, vocabulary_ids)
        
        if relationships_created > 0:
            total_relationships += relationships_created
        
        print(f"✅ Completed: {deck_name} - {relationships_created} relationships")
    
    print("\n" + "=" * 50)
    print(f"🎉 Relationship Creation Complete!")
    print(f"📊 Total relationships created: {total_relationships}")
    print("=" * 50)

if __name__ == "__main__":
    main()
