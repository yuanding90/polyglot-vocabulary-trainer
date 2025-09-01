#!/usr/bin/env python3
"""
Migration Script for Multi-Language Vocabulary Trainer
Transfers data from existing SQLite databases to Supabase
"""

import sqlite3
import os
import sys
from typing import Dict, List, Any, Tuple
from supabase import create_client, Client
import json
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Supabase credentials not found in environment variables")
    print("Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Language code mappings
LANGUAGE_CODES = {
    'Chinese': 'zh',
    'French': 'fr', 
    'English': 'en',
    'Spanish': 'es',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Japanese': 'ja',
    'Korean': 'ko'
}

def create_deck(language_a: str, language_b: str, name: str, description: str, total_words: int) -> str:
    """Create a new deck in Supabase and return the deck ID"""
    
    deck_data = {
        'name': name,
        'description': description,
        'language_a_code': LANGUAGE_CODES.get(language_a, language_a.lower()[:2]),
        'language_b_code': LANGUAGE_CODES.get(language_b, language_b.lower()[:2]),
        'language_a_name': language_a,
        'language_b_name': language_b,
        'difficulty_level': 'beginner',
        'total_words': total_words,
        'is_active': True
    }
    
    print(f"  📝 Creating deck: {name}")
    
    result = supabase.table('vocabulary_decks').insert(deck_data).execute()
    
    if result.data:
        deck_id = result.data[0]['id']
        print(f"  ✅ Deck created with ID: {deck_id}")
        return deck_id
    else:
        raise Exception(f"Failed to create deck: {result.error}")

def migrate_vocabulary_data(db_path: str, language_a: str, language_b: str, deck_id: str) -> int:
    """Migrate vocabulary data from SQLite to Supabase"""
    
    print(f"  📚 Migrating vocabulary data from {Path(db_path).name}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all vocabulary data
    cursor.execute("SELECT * FROM vocabulary ORDER BY id")
    rows = cursor.fetchall()
    
    # Determine column mapping based on language pair
    if language_a == 'Chinese' and language_b == 'French':
        # Chinese → French mapping
        word_col = 2  # chinese_word
        translation_col = 3  # french_translation
        sentence_col = 4  # example_sentence
        sentence_translation_col = 5  # sentence_translation
    elif language_a == 'French' and language_b == 'English':
        # French → English mapping
        word_col = 2  # french_word
        translation_col = 3  # english_translation
        sentence_col = 4  # example_sentence
        sentence_translation_col = 5  # sentence_translation
    else:
        # Generic mapping (assume standard order)
        word_col = 2
        translation_col = 3
        sentence_col = 4
        sentence_translation_col = 5
    
    # Prepare vocabulary data for insertion
    vocabulary_data = []
    for row in rows:
        vocab_item = {
            'language_a_word': row[word_col],
            'language_b_translation': row[translation_col],
            'language_a_sentence': row[sentence_col],
            'language_b_sentence': row[sentence_translation_col]
        }
        vocabulary_data.append(vocab_item)
    
    # Insert vocabulary data in batches
    batch_size = 100
    total_inserted = 0
    
    for i in range(0, len(vocabulary_data), batch_size):
        batch = vocabulary_data[i:i + batch_size]
        
        print(f"    📦 Inserting batch {i//batch_size + 1}/{(len(vocabulary_data) + batch_size - 1)//batch_size}")
        
        result = supabase.table('vocabulary').insert(batch).execute()
        
        if result.data:
            batch_inserted = len(result.data)
            total_inserted += batch_inserted
            print(f"    ✅ Inserted {batch_inserted} words")
        else:
            print(f"    ❌ Error inserting batch: {result.error}")
            raise Exception(f"Failed to insert vocabulary batch: {result.error}")
    
    # Get the vocabulary IDs for deck relationship
    print(f"  🔗 Creating deck-vocabulary relationships")
    
    # Get all vocabulary IDs for this language pair
    result = supabase.table('vocabulary').select('id').execute()
    
    if not result.data:
        raise Exception("Failed to retrieve vocabulary IDs")
    
    # Create deck-vocabulary relationships
    deck_vocab_data = []
    for i, vocab in enumerate(result.data):
        deck_vocab_data.append({
            'deck_id': deck_id,
            'vocabulary_id': vocab['id'],
            'word_order': i + 1
        })
    
    # Insert deck-vocabulary relationships
    result = supabase.table('deck_vocabulary').insert(deck_vocab_data).execute()
    
    if result.data:
        print(f"  ✅ Created {len(result.data)} deck-vocabulary relationships")
    else:
        print(f"  ❌ Error creating relationships: {result.error}")
        raise Exception(f"Failed to create deck-vocabulary relationships: {result.error}")
    
    conn.close()
    return total_inserted

def main():
    """Main migration function"""
    
    print("🌐 Multi-Language Vocabulary Database Migration")
    print("=" * 50)
    
    # Define databases to migrate
    databases = [
        {
            "path": "/Users/ding/Desktop/Coding/Chinese App/vocab database/financial_vocab_batch_1.db",
            "language_a": "Chinese",
            "language_b": "French",
            "name": "Chinese Financial Terms → French",
            "description": "Financial vocabulary from Chinese to French"
        },
        {
            "path": "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank/french_vocab_batch_4.db",
            "language_a": "French",
            "language_b": "English",
            "name": "French Vocabulary Batch 4 → English",
            "description": "French vocabulary batch 4 with English translations"
        }
    ]
    
    total_migrated = 0
    
    for db_info in databases:
        print(f"\n🔄 Migrating {db_info['language_a']} → {db_info['language_b']}")
        print(f"   Database: {Path(db_info['path']).name}")
        
        try:
            # Get total word count
            conn = sqlite3.connect(db_info['path'])
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vocabulary")
            total_words = cursor.fetchone()[0]
            conn.close()
            
            # Create deck
            deck_id = create_deck(
                db_info['language_a'],
                db_info['language_b'],
                db_info['name'],
                db_info['description'],
                total_words
            )
            
            # Migrate vocabulary data
            migrated_count = migrate_vocabulary_data(
                db_info['path'],
                db_info['language_a'],
                db_info['language_b'],
                deck_id
            )
            
            total_migrated += migrated_count
            print(f"  ✅ Successfully migrated {migrated_count} words")
            
        except Exception as e:
            print(f"  ❌ Error migrating {db_info['path']}: {e}")
            continue
    
    print(f"\n🎉 Migration Complete!")
    print(f"   Total words migrated: {total_migrated}")
    print(f"   Language pairs: {len(databases)}")
    
    # Verify migration
    print(f"\n🔍 Verifying migration...")
    
    try:
        # Check decks
        decks_result = supabase.table('vocabulary_decks').select('*').execute()
        print(f"   Decks created: {len(decks_result.data)}")
        
        # Check vocabulary
        vocab_result = supabase.table('vocabulary').select('id').execute()
        print(f"   Vocabulary items: {len(vocab_result.data)}")
        
        # Check relationships
        rel_result = supabase.table('deck_vocabulary').select('id').execute()
        print(f"   Deck-vocabulary relationships: {len(rel_result.data)}")
        
    except Exception as e:
        print(f"   ❌ Error during verification: {e}")

if __name__ == "__main__":
    main()
