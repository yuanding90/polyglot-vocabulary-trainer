#!/usr/bin/env python3
"""
LexiqueData Ranking Mapping Implementation
Strategy: DIRECT_PLUS_NORMALIZATION

This script implements the mapping of LexiqueData.txt frequency rankings to vocabulary entries.
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from supabase import create_client, Client

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

class LexiqueRankingMapper:
    def __init__(self):
        self.supabase = supabase
        self.lexique_data = {}  # word -> (rank, frequency)
        self.vocabulary_data = {}  # word -> vocab_id
        self.mappings = {}  # vocab_id -> rank
        self.conflicts = []
        self.unmatched = []
        
        # French-specific normalization rules
        self.accent_map = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o', 'œ': 'oe',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ç': 'c', 'ñ': 'n'
        }
        
        # Common French contractions and variations
        self.contractions = {
            'du': ['de', 'le'],
            'des': ['de', 'les'],
            'au': ['à', 'le'],
            'aux': ['à', 'les'],
            "d'": ['de'],
            "l'": ['le', 'la'],
            "qu'": ['que'],
            "n'": ['ne'],
            "j'": ['je'],
            "s'": ['se'],
            "m'": ['me'],
            "t'": ['te']
        }
    
    def normalize_word(self, word: str) -> str:
        """
        Normalize a French word for matching.
        
        Args:
            word: French word to normalize
            
        Returns:
            Normalized word
        """
        if not word:
            return word
            
        # Convert to lowercase
        normalized = word.lower().strip()
        
        # Remove accents
        normalized = ''.join(self.accent_map.get(c, c) for c in normalized)
        
        # Remove common punctuation
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def parse_lexique_file(self, file_path: str) -> Dict[str, Tuple[int, float]]:
        """
        Parse LexiqueData.txt and extract word rankings.
        
        Args:
            file_path: Path to LexiqueData.txt
            
        Returns:
            Dict mapping word -> (rank, frequency)
        """
        print(f"📖 Parsing LexiqueData.txt from {file_path}")
        
        lexique_data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or line.startswith('-') or line.startswith('NUM'):
                    continue
                
                # Pattern to match entries like "2500      29.19 patrie"
                match = re.match(r'(\d+)\s+([\d.]+)\s+(.+)$', line)
                
                if match:
                    rank = int(match.group(1))
                    frequency = float(match.group(2))
                    word = match.group(3).strip()
                    
                    # Handle conflicts (same word, different rankings)
                    if word in lexique_data:
                        old_rank, old_freq = lexique_data[word]
                        print(f"⚠️  Conflict: '{word}' appears at rank {old_rank} (freq: {old_freq}) and rank {rank} (freq: {frequency})")
                        # Keep the higher frequency (lower rank number)
                        if frequency > old_freq:
                            lexique_data[word] = (rank, frequency)
                            print(f"   → Keeping rank {rank} (higher frequency)")
                        else:
                            print(f"   → Keeping rank {old_rank} (higher frequency)")
                    else:
                        lexique_data[word] = (rank, frequency)
            
            print(f"✅ Parsed {len(lexique_data)} unique words from LexiqueData.txt")
            return lexique_data
            
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
            return {}
    
    def fetch_french_vocabulary_from_supabase(self) -> Dict[str, int]:
        """
        Fetch all French vocabulary from Supabase.
        
        Returns:
            Dict mapping word -> vocabulary_id
        """
        print("📚 Fetching French vocabulary from Supabase...")
        
        try:
            # Get all vocabulary with French words (language_a_word is French)
            response = supabase.table('vocabulary').select('id, language_a_word').execute()
            
            if not response.data:
                print("❌ No vocabulary data found")
                return {}
            
            vocabulary_data = {}
            for item in response.data:
                word = item['language_a_word']
                vocab_id = item['id']
                
                if word in vocabulary_data:
                    print(f"⚠️  Duplicate word in vocabulary: '{word}' (IDs: {vocabulary_data[word]}, {vocab_id})")
                else:
                    vocabulary_data[word] = vocab_id
            
            print(f"✅ Found {len(vocabulary_data)} unique French words in vocabulary")
            return vocabulary_data
            
        except Exception as e:
            print(f"❌ Error fetching vocabulary: {e}")
            return {}
    
    def apply_direct_mapping(self) -> int:
        """
        Apply direct word-to-word mapping for exact matches.
        
        Returns:
            Number of direct matches found
        """
        print("\n🔍 Applying direct mapping...")
        
        direct_matches = 0
        
        for word in self.lexique_data:
            if word in self.vocabulary_data:
                rank, freq = self.lexique_data[word]
                vocab_id = self.vocabulary_data[word]
                self.mappings[vocab_id] = rank
                direct_matches += 1
        
        print(f"✅ Found {direct_matches} direct matches")
        return direct_matches
    
    def apply_normalization_mapping(self) -> int:
        """
        Apply normalized matching for remaining words.
        
        Returns:
            Number of additional matches found through normalization
        """
        print("\n🔍 Applying normalization mapping...")
        
        # Create normalized lookup tables
        lexique_normalized = {}
        vocab_normalized = {}
        
        # Build normalized lexique data (excluding already matched words)
        for word, (rank, freq) in self.lexique_data.items():
            if word not in self.vocabulary_data:  # Only unmatched words
                normalized = self.normalize_word(word)
                if normalized:
                    lexique_normalized[normalized] = (word, rank, freq)
        
        # Build normalized vocabulary data (excluding already matched words)
        for word, vocab_id in self.vocabulary_data.items():
            if vocab_id not in self.mappings:  # Only unmatched vocabulary
                normalized = self.normalize_word(word)
                if normalized:
                    vocab_normalized[normalized] = (word, vocab_id)
        
        # Find normalized matches
        normalized_matches = 0
        
        for normalized_word in lexique_normalized:
            if normalized_word in vocab_normalized:
                original_lexique, rank, freq = lexique_normalized[normalized_word]
                original_vocab, vocab_id = vocab_normalized[normalized_word]
                
                self.mappings[vocab_id] = rank
                normalized_matches += 1
                
                print(f"   ✅ Normalized match: '{original_vocab}' → '{original_lexique}' (rank {rank})")
        
        print(f"✅ Found {normalized_matches} additional matches through normalization")
        return normalized_matches
    
    def update_supabase_rankings(self) -> int:
        """
        Update vocabulary table with lexique rankings.
        
        Returns:
            Number of records updated
        """
        print(f"\n💾 Updating Supabase with {len(self.mappings)} rankings...")
        
        updated_count = 0
        
        try:
            # Update in batches for better performance
            batch_size = 100
            mappings_list = list(self.mappings.items())
            
            for i in range(0, len(mappings_list), batch_size):
                batch = mappings_list[i:i + batch_size]
                
                for vocab_id, rank in batch:
                    try:
                        response = supabase.table('vocabulary').update({
                            'lexique_rank': rank
                        }).eq('id', vocab_id).execute()
                        
                        if response.data:
                            updated_count += 1
                        
                    except Exception as e:
                        print(f"❌ Error updating vocab ID {vocab_id}: {e}")
            
            print(f"✅ Successfully updated {updated_count} vocabulary records")
            return updated_count
            
        except Exception as e:
            print(f"❌ Error updating Supabase: {e}")
            return 0
    
    def generate_mapping_report(self):
        """
        Generate a comprehensive mapping report.
        """
        print(f"\n" + "="*60)
        print("📊 MAPPING REPORT")
        print("="*60)
        
        total_vocab = len(self.vocabulary_data)
        mapped_count = len(self.mappings)
        unmapped_count = total_vocab - mapped_count
        coverage = mapped_count / total_vocab * 100
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total vocabulary words: {total_vocab}")
        print(f"   Successfully mapped: {mapped_count}")
        print(f"   Unmapped: {unmapped_count}")
        print(f"   Coverage: {coverage:.1f}%")
        
        # Analyze rankings by frequency ranges
        print(f"\n📊 MAPPED WORDS BY FREQUENCY RANGES:")
        rank_ranges = [
            (1, 1000, "Very High Frequency"),
            (1001, 2500, "High Frequency"), 
            (2501, 5000, "Medium Frequency"),
            (5001, 10000, "Lower Frequency"),
            (10001, float('inf'), "Low Frequency")
        ]
        
        for min_rank, max_rank, label in rank_ranges:
            count = sum(1 for rank in self.mappings.values() if min_rank <= rank <= max_rank)
            percentage = count / mapped_count * 100 if mapped_count else 0
            print(f"   {label} (ranks {min_rank}-{max_rank}): {count} words ({percentage:.1f}%)")
        
        # Show sample mappings
        print(f"\n📝 SAMPLE MAPPINGS:")
        sample_mappings = list(self.mappings.items())[:10]
        for vocab_id, rank in sample_mappings:
            word = next((w for w, v_id in self.vocabulary_data.items() if v_id == vocab_id), "Unknown")
            print(f"   '{word}' (ID: {vocab_id}) → Rank {rank}")
        
        # Show unmapped words
        if unmapped_count > 0:
            print(f"\n❌ SAMPLE UNMAPPED WORDS:")
            unmapped_words = [word for word, vocab_id in self.vocabulary_data.items() 
                            if vocab_id not in self.mappings]
            for word in unmapped_words[:10]:
                print(f"   '{word}'")
            
            if len(unmapped_words) > 10:
                print(f"   ... and {len(unmapped_words)-10} more")
        
        return {
            'total_vocab': total_vocab,
            'mapped_count': mapped_count,
            'unmapped_count': unmapped_count,
            'coverage': coverage,
            'mappings': self.mappings
        }
    
    def run_mapping_process(self, lexique_file_path: str):
        """
        Run the complete mapping process.
        
        Args:
            lexique_file_path: Path to LexiqueData.txt
        """
        print("🚀 STARTING LEXIQUE RANKING MAPPING PROCESS")
        print("="*60)
        
        # Step 1: Parse LexiqueData.txt
        self.lexique_data = self.parse_lexique_file(lexique_file_path)
        if not self.lexique_data:
            print("❌ Failed to parse LexiqueData.txt. Exiting.")
            return
        
        # Step 2: Fetch vocabulary from Supabase
        self.vocabulary_data = self.fetch_french_vocabulary_from_supabase()
        if not self.vocabulary_data:
            print("❌ Failed to fetch vocabulary data. Exiting.")
            return
        
        # Step 3: Apply direct mapping
        direct_matches = self.apply_direct_mapping()
        
        # Step 4: Apply normalization mapping
        normalized_matches = self.apply_normalization_mapping()
        
        # Step 5: Update Supabase
        updated_count = self.update_supabase_rankings()
        
        # Step 6: Generate report
        report = self.generate_mapping_report()
        
        print(f"\n✅ MAPPING PROCESS COMPLETE!")
        print(f"📊 Final coverage: {report['coverage']:.1f}% ({report['mapped_count']}/{report['total_vocab']} words)")
        
        return report

def main():
    """Main function to run the mapping process."""
    lexique_file = "/Users/ding/Desktop/Coding/Vocabulary Learning App/LexiqueData.txt"
    
    mapper = LexiqueRankingMapper()
    report = mapper.run_mapping_process(lexique_file)
    
    if report:
        print(f"\n🎉 Successfully mapped {report['mapped_count']} out of {report['total_vocab']} vocabulary words!")
        print(f"📈 Coverage: {report['coverage']:.1f}%")

if __name__ == "__main__":
    main()
