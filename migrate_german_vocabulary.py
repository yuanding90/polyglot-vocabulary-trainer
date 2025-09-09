#!/usr/bin/env python3
"""
Migrate German vocabulary chunks to Supabase
Create German decks with proper language codes
"""

import csv
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
supabase_url = 'https://ifgitxejnakfrfeiipkx.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM'

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

def read_vocabulary_chunk(chunk_file):
    """Read vocabulary from a chunk file"""
    vocabulary_data = []
    
    with open(chunk_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            vocabulary_data.append({
                'german_word': row['german_word'],
                'english_translation': row['english_translation'],
                'german_sentence': row['german_sentence'],
                'english_sentence': row['english_sentence']
            })
    
    return vocabulary_data

def create_additional_chunks():
    """Create additional chunks from the remaining data for testing"""
    print("🔧 Creating additional test chunks...")
    
    # Read the original file again to create more chunks
    input_file = '/Users/ding/Desktop/Vocabulary Deck/B1_Wortliste.csv'
    
    all_vocabulary = []
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        
        for row in reader:
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
    
    # Create additional chunks
    chunk_size = 500  # Smaller chunks for testing
    additional_chunks = []
    
    for i in range(3, 6):  # Create chunks 4, 5, 6
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(all_vocabulary))
        
        if start_idx < len(all_vocabulary):
            chunk_data = all_vocabulary[start_idx:end_idx]
            additional_chunks.append(chunk_data)
            
            # Save as CSV
            output_file = f'german_vocab_chunks/german_vocab_chunk_{i + 1}.csv'
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['german_word', 'english_translation', 'german_sentence', 'english_sentence'])
                for entry in chunk_data:
                    writer.writerow([
                        entry['german_word'],
                        entry['english_translation'],
                        entry['german_sentence'],
                        entry['english_sentence']
                    ])
            
            print(f"✅ Created additional chunk {i + 1}: {len(chunk_data)} words")
    
    return additional_chunks

def main():
    """Main function"""
    print("🎯 Migrating German Vocabulary to Supabase")
    print("=" * 60)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Create additional chunks for testing
    additional_chunks = create_additional_chunks()
    
    # Define the 5 test decks
    test_decks = [
        ("German 01", "german_vocab_chunks/german_vocab_chunk_1.csv"),
        ("German 02", "german_vocab_chunks/german_vocab_chunk_2.csv"),
        ("German 03", "german_vocab_chunks/german_vocab_chunk_3.csv"),
        ("German 04", "german_vocab_chunks/german_vocab_chunk_4.csv"),
        ("German 05", "german_vocab_chunks/german_vocab_chunk_5.csv")
    ]
    
    created_decks = []
    
    # Process each deck
    for deck_name, chunk_file in test_decks:
        if os.path.exists(chunk_file):
            # Read vocabulary data
            vocabulary_data = read_vocabulary_chunk(chunk_file)
            
            # Create deck
            deck_id = create_german_deck(supabase, deck_name, len(vocabulary_data))
            
            if deck_id:
                # Add vocabulary to deck
                add_vocabulary_to_deck(supabase, deck_id, vocabulary_data)
                created_decks.append((deck_name, len(vocabulary_data)))
            else:
                print(f"❌ Failed to create deck: {deck_name}")
        else:
            print(f"⚠️  Chunk file not found: {chunk_file}")
    
    print(f"\n🎉 Migration Complete!")
    print(f"📊 Created {len(created_decks)} German decks:")
    for deck_name, word_count in created_decks:
        print(f"   - {deck_name}: {word_count} words")

if __name__ == "__main__":
    main()

