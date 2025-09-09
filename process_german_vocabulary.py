#!/usr/bin/env python3
"""
Process German vocabulary from CSV file
Extract fields: 1 (German), 2 (English), 7 (German sentence), 8 (English sentence)
Split into chunks of 1000 words each
"""

import csv
import os
import math

def process_german_vocabulary():
    """Process the German vocabulary CSV file"""
    print("🔧 Processing German Vocabulary")
    print("=" * 50)
    
    # Input file path
    input_file = '/Users/ding/Desktop/Vocabulary Deck/B1_Wortliste.csv'
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    # Read and process the CSV
    vocabulary_data = []
    
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        # Skip header row
        next(reader)
        
        for row_num, row in enumerate(reader, 2):  # Start from 2 since we skipped header
            if len(row) >= 8:  # Ensure we have at least 8 fields
                german_word = row[0].strip()
                english_translation = row[1].strip()
                german_sentence = row[6].strip()  # Field 7 (0-indexed = 6)
                english_sentence = row[7].strip()  # Field 8 (0-indexed = 7)
                
                # Skip empty entries
                if german_word and english_translation:
                    vocabulary_data.append({
                        'german_word': german_word,
                        'english_translation': english_translation,
                        'german_sentence': german_sentence,
                        'english_sentence': english_sentence
                    })
            else:
                print(f"⚠️  Row {row_num}: Insufficient fields ({len(row)})")
    
    print(f"📚 Total vocabulary entries: {len(vocabulary_data)}")
    
    # Split into chunks of 1000
    chunk_size = 1000
    total_chunks = math.ceil(len(vocabulary_data) / chunk_size)
    
    print(f"📦 Creating {total_chunks} chunks of {chunk_size} words each")
    
    # Create output directory
    output_dir = 'german_vocab_chunks'
    os.makedirs(output_dir, exist_ok=True)
    
    # Split and save chunks
    for chunk_num in range(total_chunks):
        start_idx = chunk_num * chunk_size
        end_idx = min((chunk_num + 1) * chunk_size, len(vocabulary_data))
        
        chunk_data = vocabulary_data[start_idx:end_idx]
        
        # Save as CSV
        output_file = os.path.join(output_dir, f'german_vocab_chunk_{chunk_num + 1}.csv')
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(['german_word', 'english_translation', 'german_sentence', 'english_sentence'])
            # Write data
            for entry in chunk_data:
                writer.writerow([
                    entry['german_word'],
                    entry['english_translation'],
                    entry['german_sentence'],
                    entry['english_sentence']
                ])
        
        print(f"✅ Chunk {chunk_num + 1}: {len(chunk_data)} words → {output_file}")
    
    print(f"\n🎉 Created {total_chunks} vocabulary chunks in '{output_dir}' directory")
    
    # Show sample of first few entries
    print(f"\n📝 Sample entries (first 3):")
    for i, entry in enumerate(vocabulary_data[:3]):
        print(f"{i+1}. {entry['german_word']} → {entry['english_translation']}")
        if entry['german_sentence']:
            print(f"   Sentence: {entry['german_sentence']}")
    
    return vocabulary_data, total_chunks

def main():
    """Main function"""
    print("🎯 German Vocabulary Processing")
    print("=" * 50)
    
    vocabulary_data, total_chunks = process_german_vocabulary()
    
    print(f"\n📊 Summary:")
    print(f"- Total entries: {len(vocabulary_data)}")
    print(f"- Total chunks: {total_chunks}")
    print(f"- Chunk size: 1000 words")
    print(f"- Output directory: german_vocab_chunks/")

if __name__ == "__main__":
    main()

