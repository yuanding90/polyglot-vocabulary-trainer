#!/usr/bin/env python3
"""
Process HSK 1-5 vocabulary files using Anthropic API
Generate high-quality Chinese to English translations and example sentences
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
    """Generate high-quality English translation and example sentences using Anthropic API"""
    
    prompt = f"""You are a Chinese language expert and HSK exam preparation specialist. For the Chinese word "{chinese_word}" which has the basic meaning "{existing_translation}", please provide:

1. A clear, concise English translation (preferably a single word or short phrase that captures the main meaning)
2. A natural, practical Chinese example sentence using this word (appropriate for HSK learners)
3. The English translation of that example sentence

Important guidelines:
- Keep translations simple and clear for HSK learners
- Use natural, everyday Chinese sentences
- Make sure the example sentence demonstrates the word's meaning clearly
- Avoid overly complex grammar or vocabulary

Format your response as JSON only:
{{
    "english_translation": "clear English translation",
    "chinese_sentence": "Chinese example sentence",
    "english_sentence": "English translation of the example sentence"
}}"""

    try:
        response = anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        content = response.content[0].text.strip()
        
        # Find JSON in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            result = json.loads(json_str)
            return result
        else:
            # Fallback if JSON parsing fails
            print(f"⚠️  JSON parsing failed for {chinese_word}, using fallback")
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
    """Process a single HSK file and generate enhanced vocabulary using API"""
    print(f"🔧 Processing HSK {hsk_level} vocabulary with Anthropic API...")
    
    vocabulary_data = []
    
    # Read the input file to get total count
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
            
            # Generate enhanced content using API
            content = generate_vocabulary_content(chinese_word, existing_translation)
            
            vocabulary_data.append({
                'chinese_word': chinese_word,
                'english_translation': content['english_translation'],
                'chinese_sentence': content['chinese_sentence'],
                'english_sentence': content['english_sentence']
            })
            
            # Rate limiting - pause between API calls
            time.sleep(1.5)
            
            # Save progress every 10 words
            if i % 10 == 0:
                print(f"💾 Saving progress... ({i}/{total_words})")
                with open(output_file, 'w', newline='', encoding='utf-8') as save_file:
                    writer = csv.DictWriter(save_file, fieldnames=['chinese_word', 'english_translation', 'chinese_sentence', 'english_sentence'])
                    writer.writeheader()
                    writer.writerows(vocabulary_data)
    
    # Final save
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
        (1, "/Users/ding/Desktop/Vocabulary Deck/hsk1_vocab.csv", "hsk1_api_enhanced.csv"),
        (2, "/Users/ding/Desktop/Vocabulary Deck/hsk2_vocab.csv", "hsk2_api_enhanced.csv"),
        (3, "/Users/ding/Desktop/Vocabulary Deck/hsk3_vocab.csv", "hsk3_api_enhanced.csv"),
        (4, "/Users/ding/Desktop/Vocabulary Deck/hsk4_vocab.csv", "hsk4_api_enhanced.csv"),
        (5, "/Users/ding/Desktop/Vocabulary Deck/hsk5_vocab.csv", "hsk5_api_enhanced.csv")
    ]
    
    # Create output directory
    output_dir = "hsk_api_enhanced_vocabulary"
    os.makedirs(output_dir, exist_ok=True)
    
    all_vocabulary = {}
    
    # Process each HSK file
    for hsk_level, input_file, output_file in hsk_files:
        if os.path.exists(input_file):
            output_path = os.path.join(output_dir, output_file)
            print(f"\n🚀 Starting HSK {hsk_level}...")
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

