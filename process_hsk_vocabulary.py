#!/usr/bin/env python3
"""
Process HSK 1-5 vocabulary files and generate Chinese to English translations
using Anthropic API to create example sentences and translations
"""

import csv
import os
import json
import time
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def generate_vocabulary_content(chinese_word, existing_translation):
    """Generate English translation and example sentences using Anthropic API"""
    
    prompt = f"""You are a Chinese language expert. For the Chinese word "{chinese_word}" which has the basic translation "{existing_translation}", please provide:

1. A clear, concise English translation (preferably a single word or short phrase)
2. A simple Chinese example sentence using this word
3. The English translation of that example sentence

Format your response as JSON:
{{
    "english_translation": "clear English translation",
    "chinese_sentence": "Chinese example sentence",
    "english_sentence": "English translation of the example sentence"
}}

Keep the example sentences simple and practical for HSK learners."""

    try:
        response = anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        # Find JSON in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)
            return result
        else:
            # Fallback if JSON parsing fails
            return {
                "english_translation": existing_translation.split(';')[0].strip(),
                "chinese_sentence": f"这个{chinese_word}很好。",
                "english_sentence": f"This {existing_translation.split(';')[0].strip()} is good."
            }
            
    except Exception as e:
        print(f"❌ Error generating content for {chinese_word}: {e}")
        # Fallback response
        return {
            "english_translation": existing_translation.split(';')[0].strip(),
            "chinese_sentence": f"这个{chinese_word}很好。",
            "english_sentence": f"This {existing_translation.split(';')[0].strip()} is good."
        }

def process_hsk_file(hsk_level, input_file, output_file):
    """Process a single HSK file and generate enhanced vocabulary"""
    print(f"🔧 Processing HSK {hsk_level} vocabulary...")
    
    vocabulary_data = []
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        total_words = sum(1 for row in reader)
    
    # Re-read to process
    with open(input_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for i, row in enumerate(reader, 1):
            chinese_word = row['chinese_word'].strip()
            existing_translation = row['translation'].strip()
            
            print(f"📝 Processing {i}/{total_words}: {chinese_word}")
            
            # Generate enhanced content
            content = generate_vocabulary_content(chinese_word, existing_translation)
            
            vocabulary_data.append({
                'chinese_word': chinese_word,
                'english_translation': content['english_translation'],
                'chinese_sentence': content['chinese_sentence'],
                'english_sentence': content['english_sentence']
            })
            
            # Rate limiting - pause between API calls
            time.sleep(1)
    
    # Save to output file
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['chinese_word', 'english_translation', 'chinese_sentence', 'english_sentence'])
        writer.writeheader()
        writer.writerows(vocabulary_data)
    
    print(f"✅ HSK {hsk_level} completed: {len(vocabulary_data)} words → {output_file}")
    return vocabulary_data

def main():
    """Main function to process all HSK files"""
    print("🎯 Processing HSK 1-5 Vocabulary with Anthropic API")
    print("=" * 60)
    
    # Check if API key is available
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("Please add your Anthropic API key to .env.local")
        return
    
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

if __name__ == "__main__":
    main()

