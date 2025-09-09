#!/usr/bin/env python3
"""
HSK to French Processor

Processes HSK levels 1-5 to generate Chinese to French translations and sentences using Anthropic API.
"""

import csv
import json
import re
import time
import requests
import random
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

class HSKToFrenchProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"

        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        # Rate limiting
        self.requests_per_minute = 50
        self.request_times = []

        # Processing config
        self.words_per_api_call = 15
        self.max_retries = 3
        self.base_delay = 2.0

        # Progress tracking
        self.start_time = datetime.now()
        self.total_api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0

    def check_rate_limit(self):
        """Check rate limits and wait if needed."""
        now = datetime.now()
        self.request_times = [t for t in self.request_times if now - t < timedelta(minutes=1)]

        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]).seconds
            print(f"⏳ Rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)

    def call_api(self, words_batch: List[Tuple[int, str, str]]) -> List[Dict]:
        """Call Anthropic API to process words."""
        self.check_rate_limit()

        # Create word list for prompt
        word_list = []
        for word_num, word, existing_translation in words_batch:
            word_list.append(f"{word_num}. {word} (current: {existing_translation})")

        words_text = "\n".join(word_list)

        prompt = f"""
        Translate these {len(words_batch)} Chinese words/phrases to French and provide example sentences. Return ONLY the structured data in this exact format:

        Chinese words:
        {words_text}

        Return format (one line per word):
        ("chinese_word", "French translation", "Chinese example sentence", "French sentence translation"),
        ("chinese_word", "French translation", "Chinese example sentence", "French sentence translation"),
        ...

        Requirements:
        - Provide clear, concise French translations
        - Create natural Chinese example sentences appropriate for HSK learners
        - Provide accurate French translations of examples
        - Use exact format with quotes and commas
        - Include all {len(words_batch)} words
        - Keep examples simple but natural
        - Use proper French grammar and vocabulary
        """

        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }

        self.total_api_calls += 1
        self.request_times.append(datetime.now())

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=body,
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['content'][0]['text']

                    # Parse response
                    pattern = r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)'
                    matches = re.findall(pattern, content)

                    if len(matches) == len(words_batch):
                        self.successful_calls += 1
                        results = []
                        for i, match in enumerate(matches):
                            word_num, chinese_word, existing_translation = words_batch[i]
                            results.append({
                                'chinese_word': match[0],
                                'french_translation': match[1],
                                'chinese_sentence': match[2],
                                'french_sentence': match[3]
                            })
                        return results
                    else:
                        print(f"⚠️  Expected {len(words_batch)} words, got {len(matches)}")
                        if len(matches) > 0:
                            self.successful_calls += 1
                            results = []
                            for i, match in enumerate(matches):
                                if i < len(words_batch):
                                    word_num, chinese_word, existing_translation = words_batch[i]
                                    results.append({
                                        'chinese_word': match[0],
                                        'french_translation': match[1],
                                        'chinese_sentence': match[2],
                                        'french_sentence': match[3]
                                    })
                            return results
                        return []

                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.base_delay * (2 ** attempt)))
                    print(f"⏳ Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue

                else:
                    print(f"❌ API error: {response.status_code}")
                    return []

            except Exception as e:
                print(f"❌ Error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.base_delay * (2 ** attempt))
                    continue
                return []

        self.failed_calls += 1
        return []

    def parse_csv(self, file_path: str) -> List[Tuple[int, str, str]]:
        """Parse HSK CSV file."""
        words = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for i, row in enumerate(reader, 1):
                    chinese_word = row['chinese_word'].strip()
                    existing_translation = row['translation'].strip()
                    if chinese_word and existing_translation:
                        words.append((i, chinese_word, existing_translation))
            print(f"📖 Loaded {len(words)} words from {file_path}")
            return words
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return []

    def process_hsk_level(self, hsk_level: int) -> List[Dict]:
        """Process a single HSK level."""
        print(f"\n🚀 Starting HSK {hsk_level} (Chinese to French)")
        print("=" * 60)

        input_file = f"/Users/ding/Desktop/Vocabulary Deck/hsk{hsk_level}_vocab.csv"
        output_file = f"hsk_french_enhanced_vocabulary/hsk{hsk_level}_french_enhanced.csv"

        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return []

        # Parse input file
        all_words = self.parse_csv(input_file)
        if not all_words:
            return []

        # Create output directory
        os.makedirs("hsk_french_enhanced_vocabulary", exist_ok=True)

        vocabulary_data = []
        total_chunks = (len(all_words) + self.words_per_api_call - 1) // self.words_per_api_call

        print(f"📊 Processing {len(all_words)} words in {total_chunks} chunks")

        # Process in chunks
        for i in range(0, len(all_words), self.words_per_api_call):
            chunk = all_words[i:i + self.words_per_api_call]
            chunk_num = i // self.words_per_api_call + 1

            print(f"\n🔄 Chunk {chunk_num}/{total_chunks} ({len(chunk)} words)")
            print(f"🔤 Sample: {[word[1] for word in chunk[:3]]}...")

            # Call API
            results = self.call_api(chunk)

            if results:
                vocabulary_data.extend(results)
                for result in results:
                    print(f"✅ {result['chinese_word']} → {result['french_translation']}")

                # Save progress
                with open(output_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=['chinese_word', 'french_translation', 'chinese_sentence', 'french_sentence'])
                    writer.writeheader()
                    writer.writerows(vocabulary_data)
                print(f"💾 Saved {len(vocabulary_data)} words to {output_file}")
            else:
                print(f"❌ Failed to process chunk {chunk_num}")

            # Progress update
            if chunk_num % 5 == 0:
                self.print_stats()

            # Small delay
            time.sleep(self.base_delay + random.uniform(0, 1))

        print(f"\n🎉 HSK {hsk_level} complete! {len(vocabulary_data)} words processed")
        return vocabulary_data

    def print_stats(self):
        """Print current statistics."""
        elapsed = datetime.now() - self.start_time
        success_rate = (self.successful_calls / self.total_api_calls * 100) if self.total_api_calls > 0 else 0

        print(f"\n📊 Stats: {self.total_api_calls} calls, {self.successful_calls} success ({success_rate:.1f}%), {elapsed}")

    def process_all(self):
        """Process HSK 1-5 sequentially."""
        print("🎯 Processing HSK 1-5 to French with Anthropic API")
        print("=" * 60)

        all_results = {}

        for hsk_level in [1, 2, 3, 4, 5]:
            print(f"\n{'='*20} HSK {hsk_level} {'='*20}")
            results = self.process_hsk_level(hsk_level)
            all_results[f"HSK{hsk_level}"] = results

            # Final stats for this level
            self.print_stats()

        # Final summary
        print(f"\n🎉 ALL COMPLETE!")
        print("=" * 60)
        total_words = sum(len(vocab) for vocab in all_results.values())
        print(f"📊 Total words processed: {total_words}")
        for hsk_level, vocab in all_results.items():
            print(f"   - {hsk_level}: {len(vocab)} words")

        self.print_stats()

def main():
    """Main function."""
    # Load API key
    config_path = "api-config.json"
    if not os.path.exists(config_path):
        print(f"❌ {config_path} not found")
        return

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            api_key = config.get('anthropicApiKey')
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return

    if not api_key:
        print("❌ No API key found")
        return

    # Process all levels
    processor = HSKToFrenchProcessor(api_key)
    processor.process_all()

if __name__ == "__main__":
    main()

