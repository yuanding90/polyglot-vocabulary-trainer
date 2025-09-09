#!/usr/bin/env python3
"""
Process HSK 1-5 vocabulary files and create basic Chinese to English structure
This creates the foundation that can be enhanced later with API calls
"""

import csv
import os
import re

def clean_translation(translation):
    """Clean and extract the main translation from the existing translation field"""
    # Remove classifier information and extra details
    translation = re.sub(r'CL:.*?\]', '', translation)
    translation = re.sub(r'\([^)]*\)', '', translation)
    translation = re.sub(r'[;,]', '', translation)
    return translation.strip()

def create_basic_sentence(chinese_word, english_translation):
    """Create a basic example sentence"""
    # Simple template sentences
    templates = [
        f"这个{chinese_word}很好。",
        f"我喜欢这个{chinese_word}。",
        f"这个{chinese_word}很漂亮。",
        f"我有一个{chinese_word}。",
        f"这个{chinese_word}很贵。"
    ]
    
    english_templates = [
        f"This {english_translation} is good.",
        f"I like this {english_translation}.",
        f"This {english_translation} is beautiful.",
        f"I have a {english_translation}.",
        f"This {english_translation} is expensive."
    ]
    
    # Use a simple hash to pick consistent templates
    index = hash(chinese_word) % len(templates)
    return templates[index], english_templates[index]

def process_hsk_file(hsk_level, input_file, output_file):
    """Process a single HSK file and create enhanced vocabulary"""
    print(f"🔧 Processing HSK {hsk_level} vocabulary...")
    
    vocabulary_data = []
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for i, row in enumerate(reader, 1):
            chinese_word = row['chinese_word'].strip()
            existing_translation = row['translation'].strip()
            
            # Clean the translation
            english_translation = clean_translation(existing_translation)
            
            # Create basic example sentences
            chinese_sentence, english_sentence = create_basic_sentence(chinese_word, english_translation)
            
            vocabulary_data.append({
                'chinese_word': chinese_word,
                'english_translation': english_translation,
                'chinese_sentence': chinese_sentence,
                'english_sentence': english_sentence
            })
            
            if i % 50 == 0:
                print(f"📝 Processed {i} words...")
    
    # Save to output file
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['chinese_word', 'english_translation', 'chinese_sentence', 'english_sentence'])
        writer.writeheader()
        writer.writerows(vocabulary_data)
    
    print(f"✅ HSK {hsk_level} completed: {len(vocabulary_data)} words → {output_file}")
    return vocabulary_data

def main():
    """Main function to process all HSK files"""
    print("🎯 Processing HSK 1-5 Vocabulary (Basic Version)")
    print("=" * 60)
    
    # Define input and output files
    hsk_files = [
        (1, "/Users/ding/Desktop/Vocabulary Deck/hsk1_vocab.csv", "hsk1_enhanced.csv"),
        (2, "/Users/ding/Desktop/Vocabulary Deck/hsk2_vocab.csv", "hsk2_enhanced.csv"),
        (3, "/Users/ding/Desktop/Vocabulary Deck/hsk3_vocab.csv", "hsk3_enhanced.csv"),
        (4, "/Users/ding/Desktop/Vocabulary Deck/hsk4_vocab.csv", "hsk4_enhanced.csv"),
        (5, "/Users/ding/Desktop/Vocabulary Deck/hsk5_vocab.csv", "hsk5_enhanced.csv")
    ]
    
    # Create output directory
    output_dir = "hsk_enhanced_vocabulary"
    os.makedirs(output_dir, exist_ok=True)
    
    all_vocabulary = {}
    
    # Process each HSK file
    for hsk_level, input_file, output_file in hsk_files:
        if os.path.exists(input_file):
            output_path = os.path.join(output_dir, output_file)
            vocabulary = process_hsk_file(hsk_level, input_file, output_path)
            all_vocabulary[f"HSK{hsk_level}"] = vocabulary
        else:
            print(f"⚠️  File not found: {input_file}")
    
    # Summary
    print(f"\n🎉 Processing Complete!")
    print(f"📊 Summary:")
    for hsk_level, vocabulary in all_vocabulary.items():
        print(f"   - {hsk_level}: {len(vocabulary)} words")
    
    total_words = sum(len(vocab) for vocab in all_vocabulary.values())
    print(f"   - Total words: {total_words}")
    print(f"   - Output directory: {output_dir}/")
    
    # Show sample output
    print(f"\n📝 Sample output from HSK1:")
    if all_vocabulary.get("HSK1"):
        sample = all_vocabulary["HSK1"][0]
        print(f"   Chinese: {sample['chinese_word']}")
        print(f"   English: {sample['english_translation']}")
        print(f"   Sentence: {sample['chinese_sentence']}")
        print(f"   Translation: {sample['english_sentence']}")

if __name__ == "__main__":
    main()

