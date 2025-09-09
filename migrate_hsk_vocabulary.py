#!/usr/bin/env python3
"""
Migrate HSK 1-5 vocabulary to Supabase
Create Chinese to English decks from the enhanced HSK vocabulary files
"""

import csv
import os
import re
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url = 'https://ifgitxejnakfrfeiipkx.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM'

def clean_translation(translation):
    """Clean the translation to make it more readable"""
    # Remove extra spaces and clean up
    translation = re.sub(r'\s+', ' ', translation)
    translation = re.sub(r'\[[^\]]*\]', '', translation)  # Remove bracketed content
    translation = re.sub(r'\([^)]*\)', '', translation)   # Remove parenthetical content
    translation = re.sub(r'[;,]', '', translation)        # Remove semicolons and commas
    translation = translation.strip()
    
    # Take only the first meaningful part
    parts = translation.split()
    if len(parts) > 3:
        # Keep only first few words
        translation = ' '.join(parts[:3])
    
    return translation

def create_hsk_deck(supabase, deck_name, total_words, hsk_level):
    """Create an HSK deck in Supabase"""
    print(f"📚 Creating deck: {deck_name}")
    
    deck_data = {
        'name': deck_name,
        'language_a_code': 'zh-CN',
        'language_b_code': 'en-US',
        'language_a_name': 'Chinese',
        'language_b_name': 'English',
        'total_words': total_words,
        'description': f'HSK {hsk_level} vocabulary deck - {total_words} words'
    }
    
    try:
        result = supabase.table('vocabulary_decks').insert(deck_data).execute()
        deck_id = result.data[0]['id']
        print(f"✅ Created deck: {deck_name} (ID: {deck_id})")
        return deck_id
    except Exception as e:
        print(f"❌ Error creating deck {deck_name}: {e}")
        return None

def add_vocabulary_to_deck(supabase, deck_id, vocabulary_data):
    """Add vocabulary to the deck"""
    print(f"📝 Adding {len(vocabulary_data)} vocabulary entries...")
    
    # First, add vocabulary to the vocabulary table
    vocab_entries = []
    for entry in vocabulary_data:
        vocab_entry = {
            'language_a_word': entry['chinese_word'],
            'language_b_translation': entry['english_translation'],
            'language_a_sentence': entry['chinese_sentence'] if entry['chinese_sentence'] else None,
            'language_b_sentence': entry['english_sentence'] if entry['english_sentence'] else None
        }
        vocab_entries.append(vocab_entry)
    
    try:
        # Insert vocabulary entries
        vocab_result = supabase.table('vocabulary').insert(vocab_entries).execute()
        vocab_ids = [entry['id'] for entry in vocab_result.data]
        print(f"✅ Added {len(vocab_ids)} vocabulary entries")
        
        # Create deck-vocabulary relationships
        deck_vocab_entries = []
        for i, vocab_id in enumerate(vocab_ids):
            deck_vocab_entries.append({
                'deck_id': deck_id,
                'vocabulary_id': vocab_id,
                'word_order': i + 1
            })
        
        # Insert in batches of 100
        batch_size = 100
        for i in range(0, len(deck_vocab_entries), batch_size):
            batch = deck_vocab_entries[i:i + batch_size]
            supabase.table('deck_vocabulary').insert(batch).execute()
            print(f"📝 Inserted batch {i//batch_size + 1}: {len(batch)} relationships")
        
        print(f"✅ Created {len(deck_vocab_entries)} deck-vocabulary relationships")
        
    except Exception as e:
        print(f"❌ Error adding vocabulary: {e}")

def read_enhanced_vocabulary(file_path):
    """Read enhanced vocabulary from CSV file"""
    vocabulary_data = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Clean the translation
            english_translation = clean_translation(row['english_translation'])
            
            vocabulary_data.append({
                'chinese_word': row['chinese_word'].strip(),
                'english_translation': english_translation,
                'chinese_sentence': row['chinese_sentence'].strip(),
                'english_sentence': row['english_sentence'].strip()
            })
    
    return vocabulary_data

def main():
    """Main function"""
    print("🎯 Migrating HSK 1-5 Vocabulary to Supabase")
    print("=" * 60)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Define HSK files
    hsk_files = [
        (1, "hsk_enhanced_vocabulary/hsk1_enhanced.csv", "HSK 1"),
        (2, "hsk_enhanced_vocabulary/hsk2_enhanced.csv", "HSK 2"),
        (3, "hsk_enhanced_vocabulary/hsk3_enhanced.csv", "HSK 3"),
        (4, "hsk_enhanced_vocabulary/hsk4_enhanced.csv", "HSK 4"),
        (5, "hsk_enhanced_vocabulary/hsk5_enhanced.csv", "HSK 5")
    ]
    
    created_decks = []
    
    # Process each HSK file
    for hsk_level, file_path, deck_name in hsk_files:
        if os.path.exists(file_path):
            print(f"\n🔧 Processing {deck_name}...")
            
            # Read vocabulary data
            vocabulary_data = read_enhanced_vocabulary(file_path)
            
            # Create deck
            deck_id = create_hsk_deck(supabase, deck_name, len(vocabulary_data), hsk_level)
            
            if deck_id:
                # Add vocabulary to deck
                add_vocabulary_to_deck(supabase, deck_id, vocabulary_data)
                created_decks.append((deck_name, len(vocabulary_data)))
            else:
                print(f"❌ Failed to create deck: {deck_name}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎉 Migration Complete!")
    print(f"📊 Created {len(created_decks)} HSK decks:")
    for deck_name, word_count in created_decks:
        print(f"   - {deck_name}: {word_count} words")
    
    # Final summary
    final_result = supabase.table('vocabulary_decks').select('*').eq('language_a_code', 'zh-CN').execute()
    total_chinese_decks = len(final_result.data)
    total_chinese_words = sum(deck['total_words'] for deck in final_result.data)
    
    print(f"\n📈 Final Chinese Deck Summary:")
    print(f"   - Total Chinese decks: {total_chinese_decks}")
    print(f"   - Total Chinese words: {total_chinese_words}")

if __name__ == "__main__":
    main()

