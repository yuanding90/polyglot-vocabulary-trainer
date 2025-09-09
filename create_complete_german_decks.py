#!/usr/bin/env python3
"""
Create complete set of German decks from the B1 vocabulary list
This will create all German decks from scratch to ensure complete coverage
"""

import csv
import os
import math
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url = 'https://ifgitxejnakfrfeiipkx.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM'

def read_all_german_vocabulary():
    """Read all German vocabulary from the original CSV file"""
    print("📖 Reading all German vocabulary from CSV...")
    
    input_file = '/Users/ding/Desktop/Vocabulary Deck/B1_Wortliste.csv'
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return []
    
    all_vocabulary = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        
        for row_num, row in enumerate(reader, 2):
            if len(row) >= 8:
                german_word = row[0].strip()
                english_translation = row[1].strip()
                german_sentence = row[6].strip()
                english_sentence = row[7].strip()
                
                if german_word and english_translation:
                    all_vocabulary.append({
                        'german_word': german_word,
                        'english_translation': english_translation,
                        'german_sentence': german_sentence,
                        'english_sentence': english_sentence
                    })
            else:
                print(f"⚠️  Row {row_num}: Insufficient fields ({len(row)})")
    
    print(f"📚 Total vocabulary entries: {len(all_vocabulary)}")
    return all_vocabulary

def delete_existing_german_decks(supabase):
    """Delete existing German decks to start fresh"""
    print("🗑️  Deleting existing German decks...")
    
    try:
        # Get existing German deck IDs
        result = supabase.table('vocabulary_decks').select('id').eq('language_a_code', 'de-DE').execute()
        deck_ids = [deck['id'] for deck in result.data]
        
        if deck_ids:
            # Delete deck-vocabulary relationships first
            for deck_id in deck_ids:
                supabase.table('deck_vocabulary').delete().eq('deck_id', deck_id).execute()
            
            # Delete the decks
            supabase.table('vocabulary_decks').delete().eq('language_a_code', 'de-DE').execute()
            print(f"✅ Deleted {len(deck_ids)} existing German decks")
        else:
            print("ℹ️  No existing German decks found")
            
    except Exception as e:
        print(f"❌ Error deleting existing decks: {e}")

def create_german_deck(supabase, deck_name, total_words):
    """Create a German deck in Supabase"""
    print(f"📚 Creating deck: {deck_name}")
    
    deck_data = {
        'name': deck_name,
        'language_a_code': 'de-DE',
        'language_b_code': 'en-US',
        'language_a_name': 'German',
        'language_b_name': 'English',
        'total_words': total_words,
        'description': f'German B1 vocabulary deck - {total_words} words'
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
            'language_a_word': entry['german_word'],
            'language_b_translation': entry['english_translation'],
            'language_a_sentence': entry['german_sentence'] if entry['german_sentence'] else None,
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

def main():
    """Main function"""
    print("🎯 Creating Complete German Vocabulary Decks")
    print("=" * 60)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Delete existing German decks
    delete_existing_german_decks(supabase)
    
    # Read all vocabulary
    all_vocabulary = read_all_german_vocabulary()
    
    if not all_vocabulary:
        print("❌ No vocabulary data found")
        return
    
    # Split into chunks of 1000 words
    chunk_size = 1000
    total_chunks = math.ceil(len(all_vocabulary) / chunk_size)
    
    print(f"📦 Creating {total_chunks} chunks of {chunk_size} words each")
    
    created_decks = []
    
    # Process each chunk
    for chunk_num in range(total_chunks):
        start_idx = chunk_num * chunk_size
        end_idx = min((chunk_num + 1) * chunk_size, len(all_vocabulary))
        
        chunk_data = all_vocabulary[start_idx:end_idx]
        deck_name = f"German {chunk_num + 1:02d}"
        
        print(f"\n🔧 Processing chunk {chunk_num + 1}/{total_chunks}")
        print(f"📊 Words {start_idx + 1}-{end_idx} of {len(all_vocabulary)}")
        
        # Create deck
        deck_id = create_german_deck(supabase, deck_name, len(chunk_data))
        
        if deck_id:
            # Add vocabulary to deck
            add_vocabulary_to_deck(supabase, deck_id, chunk_data)
            created_decks.append((deck_name, len(chunk_data)))
        else:
            print(f"❌ Failed to create deck: {deck_name}")
    
    print(f"\n🎉 Migration Complete!")
    print(f"📊 Created {len(created_decks)} German decks:")
    for deck_name, word_count in created_decks:
        print(f"   - {deck_name}: {word_count} words")
    
    # Final summary
    final_result = supabase.table('vocabulary_decks').select('*').eq('language_a_code', 'de-DE').execute()
    total_german_decks = len(final_result.data)
    total_german_words = sum(deck['total_words'] for deck in final_result.data)
    
    print(f"\n📈 Final German Deck Summary:")
    print(f"   - Total German decks: {total_german_decks}")
    print(f"   - Total German words: {total_german_words}")
    print(f"   - Average words per deck: {total_german_words // total_german_decks if total_german_decks > 0 else 0}")

if __name__ == "__main__":
    main()

