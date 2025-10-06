#!/usr/bin/env python3
"""
French LexiqueData Ranking Mapping Implementation
This script maps French word frequency rankings from LexiqueData.txt to vocabulary entries.
"""

import re
import unicodedata
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from difflib import SequenceMatcher
from supabase import create_client, Client

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

class FrenchLexiqueRankingMapper:
    def __init__(self):
        self.supabase = supabase
        self.lexique_data = {}  # word -> (rank, frequency)
        self.vocabulary_data = {}  # vocab_id -> word
        self.mappings = {}  # vocab_id -> (lexique_word_id, mapping_type, confidence)
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
    
    def normalize_french_word(self, word: str) -> str:
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
    
    def calculate_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate similarity between two words.
        
        Args:
            word1: First word
            word2: Second word
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        return SequenceMatcher(None, word1, word2).ratio()
    
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
    
    def fetch_french_vocabulary_from_supabase(self) -> Dict[int, str]:
        """
        Fetch all French vocabulary from Supabase.
        
        Returns:
            Dict mapping vocab_id -> word
        """
        print("📚 Fetching French vocabulary from Supabase...")
        
        try:
            # Get all vocabulary from French decks
            french_deck_response = supabase.table('vocabulary_decks').select('id').like('name', '%. French %').execute()
            
            if not french_deck_response.data:
                print("❌ No French decks found")
                return {}
            
            deck_ids = [deck['id'] for deck in french_deck_response.data]
            print(f"   Found {len(deck_ids)} French decks")
            
            # Get all vocabulary IDs from French decks
            all_vocab_ids = set()
            for deck_id in deck_ids:
                deck_vocab_response = supabase.table('deck_vocabulary').select('vocabulary_id').eq('deck_id', deck_id).execute()
                if deck_vocab_response.data:
                    for item in deck_vocab_response.data:
                        all_vocab_ids.add(item['vocabulary_id'])
            
            print(f"   Found {len(all_vocab_ids)} unique vocabulary IDs")
            
            # Get vocabulary details in batches
            vocabulary_data = {}
            batch_size = 1000
            all_vocab_ids_list = list(all_vocab_ids)
            
            for i in range(0, len(all_vocab_ids_list), batch_size):
                batch_ids = all_vocab_ids_list[i:i + batch_size]
                print(f"   Processing batch {i//batch_size + 1}/{(len(all_vocab_ids_list) + batch_size - 1)//batch_size}")
                
                vocab_response = supabase.table('vocabulary').select('id, language_a_word').in_('id', batch_ids).execute()
                if vocab_response.data:
                    for item in vocab_response.data:
                        vocabulary_data[item['id']] = item['language_a_word']
            
            print(f"✅ Retrieved {len(vocabulary_data)} French vocabulary entries")
            return vocabulary_data
            
        except Exception as e:
            print(f"❌ Error fetching vocabulary: {e}")
            return {}
    
    def load_lexique_data_to_database(self) -> Dict[str, int]:
        """
        Load LexiqueData.txt into the french_lexique_words table.
        
        Returns:
            Dict mapping word -> lexique_word_id
        """
        print(f"\n💾 Loading LexiqueData.txt into database...")
        
        try:
            # First, clear existing data
            supabase.table('french_lexique_words').delete().neq('id', 0).execute()
            print("   Cleared existing lexique data")
            
            # Insert lexique data in batches
            batch_size = 500
            lexique_words = list(self.lexique_data.items())
            word_to_id = {}
            
            for i in range(0, len(lexique_words), batch_size):
                batch = lexique_words[i:i + batch_size]
                batch_data = []
                
                for word, (rank, frequency) in batch:
                    normalized = self.normalize_french_word(word)
                    batch_data.append({
                        'word': word,
                        'normalized_word': normalized,
                        'frequency_rank': rank,
                        'frequency_score': frequency
                    })
                
                response = supabase.table('french_lexique_words').insert(batch_data).execute()
                
                if response.data:
                    for item in response.data:
                        word_to_id[item['word']] = item['id']
                
                print(f"   Loaded batch {i//batch_size + 1}/{(len(lexique_words) + batch_size - 1)//batch_size}")
            
            print(f"✅ Loaded {len(word_to_id)} lexique words into database")
            return word_to_id
            
        except Exception as e:
            print(f"❌ Error loading lexique data: {e}")
            return {}
    
    def apply_direct_mapping(self, word_to_lexique_id: Dict[str, int]) -> int:
        """
        Apply direct word-to-word mapping for exact matches.
        
        Args:
            word_to_lexique_id: Dict mapping word -> lexique_word_id
            
        Returns:
            Number of direct matches found
        """
        print(f"\n🔍 Applying direct mapping...")
        
        direct_matches = 0
        mapping_data = []
        
        for vocab_id, word in self.vocabulary_data.items():
            if word in word_to_lexique_id:
                lexique_word_id = word_to_lexique_id[word]
                mapping_data.append({
                    'vocabulary_id': vocab_id,
                    'french_lexique_word_id': lexique_word_id,
                    'mapping_type': 'direct',
                    'confidence_score': 1.0
                })
                self.mappings[vocab_id] = (lexique_word_id, 'direct', 1.0)
                direct_matches += 1
        
        # Insert mappings in batches
        if mapping_data:
            batch_size = 500
            for i in range(0, len(mapping_data), batch_size):
                batch = mapping_data[i:i + batch_size]
                supabase.table('french_vocabulary_lexique_mapping').insert(batch).execute()
        
        print(f"✅ Found {direct_matches} direct matches")
        return direct_matches
    
    def apply_normalized_mapping(self, word_to_lexique_id: Dict[str, int]) -> int:
        """
        Apply normalized matching for remaining words.
        
        Args:
            word_to_lexique_id: Dict mapping word -> lexique_word_id
            
        Returns:
            Number of additional matches found through normalization
        """
        print(f"\n🔍 Applying normalized mapping...")
        
        # Create normalized lookup for lexique words
        normalized_lexique = {}
        for word, lexique_id in word_to_lexique_id.items():
            normalized = self.normalize_french_word(word)
            if normalized:
                normalized_lexique[normalized] = (word, lexique_id)
        
        # Find normalized matches
        normalized_matches = 0
        mapping_data = []
        
        for vocab_id, word in self.vocabulary_data.items():
            if vocab_id not in self.mappings:  # Only unmatched vocabulary
                normalized = self.normalize_french_word(word)
                if normalized in normalized_lexique:
                    original_lexique, lexique_word_id = normalized_lexique[normalized]
                    mapping_data.append({
                        'vocabulary_id': vocab_id,
                        'french_lexique_word_id': lexique_word_id,
                        'mapping_type': 'normalized',
                        'confidence_score': 0.9
                    })
                    self.mappings[vocab_id] = (lexique_word_id, 'normalized', 0.9)
                    normalized_matches += 1
                    print(f"   ✅ Normalized match: '{word}' → '{original_lexique}' (rank {self.lexique_data[original_lexique][0]})")
        
        # Insert mappings in batches
        if mapping_data:
            batch_size = 500
            for i in range(0, len(mapping_data), batch_size):
                batch = mapping_data[i:i + batch_size]
                supabase.table('french_vocabulary_lexique_mapping').insert(batch).execute()
        
        print(f"✅ Found {normalized_matches} additional matches through normalization")
        return normalized_matches
    
    def apply_fuzzy_mapping(self, word_to_lexique_id: Dict[str, int], threshold: float = 0.8) -> int:
        """
        Apply fuzzy matching for close matches.
        
        Args:
            word_to_lexique_id: Dict mapping word -> lexique_word_id
            threshold: Minimum similarity threshold
            
        Returns:
            Number of additional matches found through fuzzy matching
        """
        print(f"\n🔍 Applying fuzzy mapping (threshold: {threshold})...")
        
        fuzzy_matches = 0
        mapping_data = []
        
        for vocab_id, word in self.vocabulary_data.items():
            if vocab_id not in self.mappings:  # Only unmatched vocabulary
                best_match = None
                best_similarity = 0.0
                
                for lexique_word, lexique_word_id in word_to_lexique_id.items():
                    similarity = self.calculate_similarity(word, lexique_word)
                    if similarity > best_similarity and similarity >= threshold:
                        best_match = (lexique_word, lexique_word_id, similarity)
                        best_similarity = similarity
                
                if best_match:
                    lexique_word, lexique_word_id, similarity = best_match
                    confidence = similarity * 0.7  # Reduce confidence for fuzzy matches
                    mapping_data.append({
                        'vocabulary_id': vocab_id,
                        'french_lexique_word_id': lexique_word_id,
                        'mapping_type': 'fuzzy',
                        'confidence_score': confidence
                    })
                    self.mappings[vocab_id] = (lexique_word_id, 'fuzzy', confidence)
                    fuzzy_matches += 1
                    print(f"   🔍 Fuzzy match: '{word}' → '{lexique_word}' (similarity: {similarity:.3f}, confidence: {confidence:.3f})")
        
        # Insert mappings in batches
        if mapping_data:
            batch_size = 500
            for i in range(0, len(mapping_data), batch_size):
                batch = mapping_data[i:i + batch_size]
                supabase.table('french_vocabulary_lexique_mapping').insert(batch).execute()
        
        print(f"✅ Found {fuzzy_matches} additional matches through fuzzy matching")
        return fuzzy_matches
    
    def generate_mapping_report(self, word_to_lexique_id: Dict[str, int]):
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
        
        # Count by mapping type
        mapping_type_counts = defaultdict(int)
        for vocab_id, (_, mapping_type, _) in self.mappings.items():
            mapping_type_counts[mapping_type] += 1
        
        print(f"📈 OVERALL STATISTICS:")
        print(f"   Total vocabulary words: {total_vocab}")
        print(f"   Successfully mapped: {mapped_count}")
        print(f"   Unmapped: {unmapped_count}")
        print(f"   Coverage: {coverage:.1f}%")
        
        print(f"\n📊 MAPPING BREAKDOWN BY TYPE:")
        for mapping_type, count in mapping_type_counts.items():
            percentage = count / mapped_count * 100 if mapped_count else 0
            print(f"   {mapping_type.capitalize()}: {count} words ({percentage:.1f}%)")
        
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
            count = 0
            for vocab_id, (lexique_word_id, _, _) in self.mappings.items():
                # Find the rank for this lexique word
                for word, (rank, _) in self.lexique_data.items():
                    if word in word_to_lexique_id and word_to_lexique_id[word] == lexique_word_id:
                        if min_rank <= rank <= max_rank:
                            count += 1
                        break
            
            percentage = count / mapped_count * 100 if mapped_count else 0
            print(f"   {label} (ranks {min_rank}-{max_rank}): {count} words ({percentage:.1f}%)")
        
        # Show sample mappings
        print(f"\n📝 SAMPLE MAPPINGS:")
        sample_mappings = list(self.mappings.items())[:10]
        for vocab_id, (lexique_word_id, mapping_type, confidence) in sample_mappings:
            word = self.vocabulary_data[vocab_id]
            # Find the lexique word and rank
            for lexique_word, (rank, freq) in self.lexique_data.items():
                if lexique_word in word_to_lexique_id and word_to_lexique_id[lexique_word] == lexique_word_id:
                    print(f"   '{word}' (ID: {vocab_id}) → '{lexique_word}' (rank {rank}, {mapping_type}, conf: {confidence:.3f})")
                    break
        
        # Show unmapped words
        if unmapped_count > 0:
            print(f"\n❌ SAMPLE UNMAPPED WORDS:")
            unmapped_words = [self.vocabulary_data[vocab_id] for vocab_id in self.vocabulary_data 
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
            'mapping_type_counts': dict(mapping_type_counts),
            'mappings': self.mappings
        }
    
    def run_mapping_process(self, lexique_file_path: str):
        """
        Run the complete mapping process.
        
        Args:
            lexique_file_path: Path to LexiqueData.txt
        """
        print("🚀 STARTING FRENCH LEXIQUE RANKING MAPPING PROCESS")
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
        
        # Step 3: Load lexique data into database
        word_to_lexique_id = self.load_lexique_data_to_database()
        if not word_to_lexique_id:
            print("❌ Failed to load lexique data into database. Exiting.")
            return
        
        # Step 4: Apply direct mapping
        direct_matches = self.apply_direct_mapping(word_to_lexique_id)
        
        # Step 5: Apply normalized mapping
        normalized_matches = self.apply_normalized_mapping(word_to_lexique_id)
        
        # Step 6: Apply fuzzy mapping
        fuzzy_matches = self.apply_fuzzy_mapping(word_to_lexique_id)
        
        # Step 7: Generate report
        report = self.generate_mapping_report(word_to_lexique_id)
        
        print(f"\n✅ MAPPING PROCESS COMPLETE!")
        print(f"📊 Final coverage: {report['coverage']:.1f}% ({report['mapped_count']}/{report['total_vocab']} words)")
        print(f"📈 Mapping breakdown:")
        for mapping_type, count in report['mapping_type_counts'].items():
            print(f"   {mapping_type.capitalize()}: {count} words")
        
        return report

def main():
    """Main function to run the mapping process."""
    lexique_file = "/Users/ding/Desktop/Coding/Vocabulary Learning App/LexiqueData.txt"
    
    mapper = FrenchLexiqueRankingMapper()
    report = mapper.run_mapping_process(lexique_file)
    
    if report:
        print(f"\n🎉 Successfully mapped {report['mapped_count']} out of {report['total_vocab']} French vocabulary words!")
        print(f"📈 Coverage: {report['coverage']:.1f}%")

if __name__ == "__main__":
    main()
