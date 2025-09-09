#!/usr/bin/env python3
"""
HSK Vocabulary Processor

This script:
1. Loads HSK 1-5 vocabulary from CSV files
2. Calls Anthropic API to get English translations and example sentences
3. Creates enhanced CSV files for vocabulary training
4. Processes vocabulary in batches for efficiency
"""

import csv
import json
import re
import time
import requests
import random
import os
import math
import pickle
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional

class HSKVocabularyProcessor:
    def __init__(self, api_key: str):
        """
        Initialize the HSK vocabulary processor.
        
        Args:
            api_key: Anthropic API key
        """
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Rate limiting configuration
        self.requests_per_minute = 50
        self.requests_per_hour = 1000
        self.request_times = []
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2.0
        self.max_delay = 60.0
        
        # Efficiency configuration
        self.words_per_api_call = 15  # Conservative for Chinese-English translation
        self.max_output_tokens = 4096
        
        # Progress tracking
        self.progress_file = "hsk_processing_progress.pkl"
        self.start_time = datetime.now()
        self.total_api_calls = 0
        self.successful_api_calls = 0
        self.failed_api_calls = 0
    
    def parse_hsk_csv(self, file_path: str) -> List[Tuple[int, str, str]]:
        """
        Parse HSK CSV file and extract Chinese words with existing translations.
        
        Args:
            file_path: Path to the HSK CSV file
            
        Returns:
            List of tuples (word_number, chinese_word, existing_translation)
        """
        words = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for i, row in enumerate(reader, 1):
                    chinese_word = row['chinese_word'].strip()
                    existing_translation = row['translation'].strip()
                    
                    if chinese_word and existing_translation:
                        words.append((i, chinese_word, existing_translation))
            
            print(f"Extracted {len(words)} words from {file_path}")
            return words
            
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return []
    
    def check_rate_limit(self):
        """Check if we need to wait due to rate limiting."""
        now = datetime.now()
        
        # Remove old request times (older than 1 hour)
        self.request_times = [t for t in self.request_times if now - t < timedelta(hours=1)]
        
        # Check requests per minute
        requests_last_minute = len([t for t in self.request_times if now - t < timedelta(minutes=1)])
        if requests_last_minute >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]).seconds
            print(f"Rate limit reached (minute). Waiting {wait_time} seconds...")
            time.sleep(wait_time)
        
        # Check requests per hour
        if len(self.request_times) >= self.requests_per_hour:
            wait_time = 3600 - (now - self.request_times[0]).seconds
            print(f"Rate limit reached (hour). Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    def call_anthropic_api_bulk(self, words_batch: List[Tuple[int, str, str]]) -> List[Dict]:
        """
        Call Anthropic API to process Chinese words and get English translations.
        
        Args:
            words_batch: List of (word_number, chinese_word, existing_translation) tuples
            
        Returns:
            List of dictionaries with translation data
        """
        # Check rate limits before making request
        self.check_rate_limit()
        
        # Create the word list for the prompt
        word_list = []
        for word_num, word, existing_translation in words_batch:
            word_list.append(f"{word_num}. {word} (current: {existing_translation})")
        
        words_text = "\n".join(word_list)
        
        # Prompt for Chinese to English translation
        prompt = f"""
        Translate these {len(words_batch)} Chinese words/phrases to English and provide example sentences. Return ONLY the structured data in this exact format:

        Chinese words:
        {words_text}

        Return format (one line per word):
        ("chinese_word", "English translation", "Chinese example sentence", "English sentence translation"),
        ("chinese_word", "English translation", "Chinese example sentence", "English sentence translation"),
        ...

        Requirements:
        - Provide clear, concise English translations
        - Create natural Chinese example sentences appropriate for HSK learners
        - Provide accurate English translations of examples
        - Use exact format with quotes and commas
        - Include all {len(words_batch)} words
        - Keep examples simple but natural
        - Focus on the main meaning of each word
        """
        
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_output_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        self.total_api_calls += 1
        
        for attempt in range(self.max_retries):
            try:
                # Record request time for rate limiting
                self.request_times.append(datetime.now())
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=body,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['content'][0]['text']
                    
                    # Parse the response to extract all structured data
                    pattern = r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)'
                    matches = re.findall(pattern, content)
                    
                    if len(matches) == len(words_batch):
                        self.successful_api_calls += 1
                        results = []
                        for i, match in enumerate(matches):
                            word_num, chinese_word, existing_translation = words_batch[i]
                            results.append({
                                'word_number': word_num,
                                'chinese_word': match[0],
                                'english_translation': match[1],
                                'chinese_sentence': match[2],
                                'english_sentence': match[3]
                            })
                        return results
                    else:
                        print(f"Expected {len(words_batch)} words, got {len(matches)}. Response: {content[:200]}...")
                        # Try to salvage partial results
                        if len(matches) > 0:
                            self.successful_api_calls += 1
                            results = []
                            for i, match in enumerate(matches):
                                if i < len(words_batch):
                                    word_num, chinese_word, existing_translation = words_batch[i]
                                    results.append({
                                        'word_number': word_num,
                                        'chinese_word': match[0],
                                        'english_translation': match[1],
                                        'chinese_sentence': match[2],
                                        'english_sentence': match[3]
                                    })
                            print(f"Salvaged {len(results)} words from partial response")
                            return results
                        return []
                
                elif response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get('Retry-After', self.base_delay * (2 ** attempt)))
                    print(f"Rate limited. Retrying in {retry_after} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(retry_after)
                    continue
                
                elif response.status_code >= 500:  # Server error
                    retry_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    print(f"Server error. Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(retry_delay)
                    continue
                
                else:
                    print(f"API request failed: {response.status_code} - {response.text}")
                    return []
                    
            except requests.exceptions.Timeout:
                retry_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                print(f"Timeout. Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(retry_delay)
                continue
                
            except Exception as e:
                print(f"Error calling API: {e}")
                if attempt < self.max_retries - 1:
                    retry_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    print(f"Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(retry_delay)
                    continue
                return []
        
        self.failed_api_calls += 1
        print(f"Failed to process request after {self.max_retries} attempts")
        return []
    
    def save_progress(self, hsk_level: int, chunk_index: int, vocabulary_data: List[Dict]):
        """Save progress to allow resuming from where we left off."""
        progress = {
            'hsk_level': hsk_level,
            'chunk_index': chunk_index,
            'vocabulary_data': vocabulary_data,
            'total_api_calls': self.total_api_calls,
            'successful_api_calls': self.successful_api_calls,
            'failed_api_calls': self.failed_api_calls,
            'timestamp': datetime.now()
        }
        
        with open(self.progress_file, 'wb') as f:
            pickle.dump(progress, f)
        
        print(f"💾 Progress saved: HSK{hsk_level}, chunk {chunk_index}, {len(vocabulary_data)} words processed")
    
    def load_progress(self) -> Optional[Dict]:
        """Load progress to resume from where we left off."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'rb') as f:
                    progress = pickle.load(f)
                print(f"📂 Resuming from: HSK{progress['hsk_level']}, chunk {progress['chunk_index']}")
                return progress
            except Exception as e:
                print(f"⚠️  Could not load progress: {e}")
        return None
    
    def print_progress_stats(self):
        """Print current progress statistics."""
        elapsed_time = datetime.now() - self.start_time
        success_rate = (self.successful_api_calls / self.total_api_calls * 100) if self.total_api_calls > 0 else 0
        
        print(f"\n📊 Progress Statistics:")
        print(f"   ⏱️  Elapsed time: {elapsed_time}")
        print(f"   📞 Total API calls: {self.total_api_calls}")
        print(f"   ✅ Successful calls: {self.successful_api_calls}")
        print(f"   ❌ Failed calls: {self.failed_api_calls}")
        print(f"   📈 Success rate: {success_rate:.1f}%")
        print(f"   🚀 API calls per hour: {self.total_api_calls / (elapsed_time.total_seconds() / 3600):.1f}")
    
    def process_hsk_file(self, hsk_level: int, input_file: str, output_file: str):
        """
        Process a single HSK file and create enhanced vocabulary.
        
        Args:
            hsk_level: HSK level (1-5)
            input_file: Path to input CSV file
            output_file: Path to output CSV file
        """
        print(f"\n🔧 Processing HSK {hsk_level} vocabulary...")
        
        # Parse the input file
        all_words = self.parse_hsk_csv(input_file)
        
        if not all_words:
            print("No words found in file. Skipping.")
            return []
        
        vocabulary_data = []
        processed_count = 0
        failed_count = 0
        
        # Process words in chunks
        total_chunks = (len(all_words) + self.words_per_api_call - 1) // self.words_per_api_call
        
        for i in range(0, len(all_words), self.words_per_api_call):
            chunk = all_words[i:i + self.words_per_api_call]
            chunk_index = i // self.words_per_api_call + 1
            
            print(f"\n🔄 Processing chunk {chunk_index}/{total_chunks}")
            print(f"📝 Words in chunk: {len(chunk)}")
            print(f"🔤 Sample words: {[word[1] for word in chunk[:3]]}...")
            
            # Call API with bulk processing
            results = self.call_anthropic_api_bulk(chunk)
            
            if results:
                for result in results:
                    vocabulary_data.append({
                        'chinese_word': result['chinese_word'],
                        'english_translation': result['english_translation'],
                        'chinese_sentence': result['chinese_sentence'],
                        'english_sentence': result['english_sentence']
                    })
                    processed_count += 1
                    print(f"✅ Successfully processed: {result['chinese_word']} → {result['english_translation']}")
            else:
                failed_count += len(chunk)
                print(f"❌ Failed to process chunk: {[word[1] for word in chunk]}")
            
            # Save progress every chunk
            if vocabulary_data:
                with open(output_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=['chinese_word', 'english_translation', 'chinese_sentence', 'english_sentence'])
                    writer.writeheader()
                    writer.writerows(vocabulary_data)
                print(f"💾 Saved {len(vocabulary_data)} words to {output_file}")
            
            # Save progress for resuming
            self.save_progress(hsk_level, chunk_index, vocabulary_data)
            
            # Print progress stats every 5 chunks
            if chunk_index % 5 == 0:
                self.print_progress_stats()
            
            # Add small random delay to avoid predictable patterns
            delay = self.base_delay + random.uniform(0, 1)
            time.sleep(delay)
        
        print(f"\nHSK {hsk_level} complete!")
        print(f"Successfully processed: {processed_count} words")
        print(f"Failed: {failed_count} words")
        
        return vocabulary_data
    
    def process_all_hsk_files(self, resume: bool = True):
        """Process all HSK 1-5 files."""
        print("🎯 Processing HSK 1-5 Vocabulary with Anthropic API")
        print("=" * 60)
        
        # Check for existing progress
        if resume:
            progress = self.load_progress()
            if progress:
                # Restore progress state
                self.total_api_calls = progress.get('total_api_calls', 0)
                self.successful_api_calls = progress.get('successful_api_calls', 0)
                self.failed_api_calls = progress.get('failed_api_calls', 0)
                print(f"📂 Resuming from previous session")
        
        # Define HSK files
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
        resume_hsk_level = progress['hsk_level'] if progress else 0
        
        # Process each HSK file
        for hsk_level, input_file, output_file in hsk_files:
            if hsk_level < resume_hsk_level:
                print(f"⏭️  Skipping HSK {hsk_level} (already completed)")
                continue
                
            if os.path.exists(input_file):
                output_path = os.path.join(output_dir, output_file)
                print(f"\n🚀 Starting HSK {hsk_level}...")
                
                # If resuming this level, load existing data
                if progress and hsk_level == resume_hsk_level:
                    existing_data = progress.get('vocabulary_data', [])
                    print(f"📂 Loading {len(existing_data)} existing words for HSK {hsk_level}")
                    
                    # Save existing data to file
                    if existing_data:
                        with open(output_path, 'w', newline='', encoding='utf-8') as file:
                            writer = csv.DictWriter(file, fieldnames=['chinese_word', 'english_translation', 'chinese_sentence', 'english_sentence'])
                            writer.writeheader()
                            writer.writerows(existing_data)
                
                vocabulary = self.process_hsk_file(hsk_level, input_file, output_path)
                all_vocabulary[f"HSK{hsk_level}"] = vocabulary
            else:
                print(f"⚠️  File not found: {input_file}")
        
        # Final summary
        print(f"\n🎉 Processing Complete!")
        print(f"📊 Final Summary:")
        for hsk_level, vocabulary in all_vocabulary.items():
            print(f"   - {hsk_level}: {len(vocabulary)} words")
        
        total_words = sum(len(vocab) for vocab in all_vocabulary.values())
        print(f"   - Total words: {total_words}")
        print(f"   - Output directory: {output_dir}/")
        
        # Final progress stats
        self.print_progress_stats()
        
        # Clean up progress file
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
            print(f"🧹 Progress file cleaned up")
    
    def process_single_hsk_file(self, hsk_level: int, input_file: str, output_file: str):
        """Process a single HSK file for testing."""
        print(f"🧪 Testing HSK {hsk_level} processing...")
        print("=" * 60)
        
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return
        
        # Create output directory
        output_dir = "hsk_api_enhanced_vocabulary"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
        
        vocabulary = self.process_hsk_file(hsk_level, input_file, output_path)
        
        print(f"\n🎉 HSK {hsk_level} test complete!")
        print(f"📊 Words processed: {len(vocabulary)}")
        self.print_progress_stats()

def main():
    """Main function to run the HSK vocabulary processor."""
    # Load API key from config file
    config_path = "api-config.json"
    
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found. Please create it with your Anthropic API key.")
        return
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            api_key = config.get('anthropicApiKey')
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    if not api_key:
        print("Error: No API key found in config file.")
        return
    
    # Initialize processor
    processor = HSKVocabularyProcessor(api_key)
    
    # Check for command line arguments or provide options
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test" and len(sys.argv) > 2:
            # Test mode: process single HSK level
            hsk_level = int(sys.argv[2])
            input_file = f"/Users/ding/Desktop/Vocabulary Deck/hsk{hsk_level}_vocab.csv"
            output_file = f"hsk{hsk_level}_api_enhanced.csv"
            processor.process_single_hsk_file(hsk_level, input_file, output_file)
        elif sys.argv[1] == "resume":
            # Resume mode
            processor.process_all_hsk_files(resume=True)
        else:
            print("Usage:")
            print("  python hsk_vocab_processor.py          # Process all HSK files")
            print("  python hsk_vocab_processor.py test 1   # Test HSK 1 only")
            print("  python hsk_vocab_processor.py resume   # Resume from where left off")
    else:
        # Default: process all HSK files
        processor.process_all_hsk_files(resume=True)

if __name__ == "__main__":
    main()
