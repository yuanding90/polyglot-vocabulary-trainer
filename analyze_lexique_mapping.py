#!/usr/bin/env python3
"""
LexiqueData.txt Ranking Analysis and Mapping Proposal

This script analyzes the relationship between LexiqueData.txt rankings and current vocabulary
to propose a method for mapping frequency rankings back to vocabulary entries.
"""

import sqlite3
import re
import os
from typing import List, Dict, Tuple, Set
from collections import defaultdict, Counter
from supabase import create_client, Client

# Supabase connection
supabase_url = "https://ifgitxejnakfrfeiipkx.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlmZ2l0eGVqbmFrZnJmZWlpcGt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY2ODQ3NjAsImV4cCI6MjA3MjI2MDc2MH0.aeUT8BnQOezCNjhVIwVQlxvoQnvCoh4TnjwuVbNjsEM"
supabase: Client = create_client(supabase_url, supabase_key)

class LexiqueRankingAnalyzer:
    def __init__(self):
        self.lexique_data = {}  # word -> (rank, frequency)
        self.vocabulary_data = {}  # word -> vocabulary_id
        self.conflicts = []  # words with multiple rankings
        
    def parse_lexique_file(self, file_path: str) -> Dict[str, Tuple[int, float]]:
        """
        Parse LexiqueData.txt and extract word rankings and frequencies.
        
        Returns:
            Dict mapping word -> (rank, frequency)
        """
        print(f"📖 Parsing LexiqueData.txt from {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return {}
            
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
            print(f"📊 Rank range: {min(rank for rank, _ in lexique_data.values())} to {max(rank for rank, _ in lexique_data.values())}")
            
            return lexique_data
            
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
            return {}
    
    def fetch_vocabulary_from_supabase(self) -> Dict[str, int]:
        """
        Fetch all French vocabulary from Supabase.
        
        Returns:
            Dict mapping word -> vocabulary_id
        """
        print("📚 Fetching French vocabulary from Supabase...")
        
        try:
            # Get all French vocabulary
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
    
    def analyze_mapping_potential(self):
        """
        Analyze the potential for mapping LexiqueData rankings to vocabulary.
        """
        print("\n" + "="*60)
        print("🔍 MAPPING ANALYSIS")
        print("="*60)
        
        # Find matches
        matches = []
        lexique_only = []
        vocab_only = []
        
        for word in self.lexique_data:
            if word in self.vocabulary_data:
                rank, freq = self.lexique_data[word]
                vocab_id = self.vocabulary_data[word]
                matches.append((word, rank, freq, vocab_id))
            else:
                lexique_only.append((word, self.lexique_data[word][0], self.lexique_data[word][1]))
        
        for word in self.vocabulary_data:
            if word not in self.lexique_data:
                vocab_only.append((word, self.vocabulary_data[word]))
        
        print(f"📊 MATCHING STATISTICS:")
        print(f"   ✅ Direct matches: {len(matches)}")
        print(f"   📖 LexiqueData only: {len(lexique_only)}")
        print(f"   📚 Vocabulary only: {len(vocab_only)}")
        print(f"   📈 Match rate: {len(matches)/len(self.vocabulary_data)*100:.1f}%")
        
        # Analyze match quality by rank ranges
        print(f"\n📊 MATCHES BY RANK RANGES:")
        rank_ranges = [
            (1, 1000, "Very High Frequency"),
            (1001, 2500, "High Frequency"), 
            (2501, 5000, "Medium Frequency"),
            (5001, 10000, "Lower Frequency"),
            (10001, float('inf'), "Low Frequency")
        ]
        
        for min_rank, max_rank, label in rank_ranges:
            count = sum(1 for _, rank, _, _ in matches if min_rank <= rank <= max_rank)
            percentage = count / len(matches) * 100 if matches else 0
            print(f"   {label} (ranks {min_rank}-{max_rank}): {count} words ({percentage:.1f}%)")
        
        # Sample some matches and non-matches
        print(f"\n📝 SAMPLE DIRECT MATCHES:")
        for i, (word, rank, freq, vocab_id) in enumerate(matches[:10]):
            print(f"   {i+1:2d}. '{word}' → Rank {rank} (freq: {freq}) → Vocab ID {vocab_id}")
        
        if len(matches) > 10:
            print(f"   ... and {len(matches)-10} more matches")
        
        print(f"\n📝 SAMPLE LEXIQUE-ONLY WORDS:")
        for i, (word, rank, freq) in enumerate(lexique_only[:5]):
            print(f"   {i+1:2d}. '{word}' → Rank {rank} (freq: {freq})")
        
        print(f"\n📝 SAMPLE VOCABULARY-ONLY WORDS:")
        for i, (word, vocab_id) in enumerate(vocab_only[:5]):
            print(f"   {i+1:2d}. '{word}' → Vocab ID {vocab_id}")
        
        return matches, lexique_only, vocab_only
    
    def propose_mapping_strategy(self, matches: List[Tuple], lexique_only: List[Tuple], vocab_only: List[Tuple]):
        """
        Propose a strategy for mapping LexiqueData rankings to vocabulary.
        """
        print("\n" + "="*60)
        print("💡 MAPPING STRATEGY PROPOSAL")
        print("="*60)
        
        total_vocab = len(self.vocabulary_data)
        direct_matches = len(matches)
        coverage = direct_matches / total_vocab * 100
        
        print(f"📊 CURRENT COVERAGE: {coverage:.1f}% ({direct_matches}/{total_vocab} words)")
        
        if coverage >= 90:
            print("✅ EXCELLENT: Direct mapping provides >90% coverage")
            strategy = "direct"
        elif coverage >= 70:
            print("✅ GOOD: Direct mapping provides >70% coverage, consider normalization for remaining")
            strategy = "direct_plus_normalization"
        else:
            print("⚠️  MODERATE: Consider additional normalization strategies")
            strategy = "comprehensive"
        
        print(f"\n🎯 RECOMMENDED STRATEGY: {strategy.upper()}")
        
        if strategy == "direct":
            print("""
📋 IMPLEMENTATION STEPS:
1. Add 'lexique_rank' INTEGER column to vocabulary table
2. Direct mapping for exact word matches
3. Handle conflicts by choosing highest frequency (lowest rank number)
4. No additional normalization needed
            """)
            
        elif strategy == "direct_plus_normalization":
            print("""
📋 IMPLEMENTATION STEPS:
1. Add 'lexique_rank' INTEGER column to vocabulary table
2. Direct mapping for exact word matches
3. Apply normalization for remaining words:
   - Remove accents: café → cafe
   - Case insensitive matching
   - Handle common variations (plurals, conjugations)
4. Manual review of remaining unmatched words
            """)
            
        else:  # comprehensive
            print("""
📋 IMPLEMENTATION STEPS:
1. Add 'lexique_rank' INTEGER column to vocabulary table
2. Direct mapping for exact word matches
3. Comprehensive normalization:
   - Remove accents and diacritics
   - Case insensitive matching
   - Stemming/lemmatization
   - Handle contractions and common variations
4. Fuzzy matching for close matches
5. Manual review and validation
            """)
        
        # Calculate potential final coverage
        estimated_final_coverage = min(95, coverage + (100 - coverage) * 0.3)
        print(f"\n📈 ESTIMATED FINAL COVERAGE: ~{estimated_final_coverage:.1f}%")
        
        return strategy, estimated_final_coverage
    
    def generate_sql_migration(self, strategy: str):
        """
        Generate SQL migration to add lexique_rank column.
        """
        print(f"\n" + "="*60)
        print("🗄️  SQL MIGRATION GENERATION")
        print("="*60)
        
        migration_sql = f"""-- Migration: Add LexiqueData ranking to vocabulary table
-- Strategy: {strategy.upper()}

-- Add lexique_rank column to vocabulary table
ALTER TABLE vocabulary 
ADD COLUMN IF NOT EXISTS lexique_rank INTEGER;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_vocabulary_lexique_rank ON vocabulary(lexique_rank);

-- Add comment explaining the column
COMMENT ON COLUMN vocabulary.lexique_rank IS 'Frequency ranking from LexiqueData.txt (lower number = higher frequency)';

-- Example update statements (to be populated by mapping script):
-- UPDATE vocabulary SET lexique_rank = 2500 WHERE language_a_word = 'patrie';
-- UPDATE vocabulary SET lexique_rank = 1234 WHERE language_a_word = 'maison';
"""
        
        print("📄 GENERATED MIGRATION SQL:")
        print(migration_sql)
        
        return migration_sql
    
    def generate_mapping_script_template(self, strategy: str):
        """
        Generate Python script template for performing the mapping.
        """
        print(f"\n" + "="*60)
        print("🐍 MAPPING SCRIPT TEMPLATE")
        print("="*60)
        
        script_template = f'''#!/usr/bin/env python3
"""
LexiqueData Ranking Mapping Script
Strategy: {strategy.upper()}
"""

import sqlite3
import re
from typing import Dict, List, Tuple
from supabase import create_client, Client

class LexiqueRankingMapper:
    def __init__(self):
        self.supabase = create_client(supabase_url, supabase_key)
        self.lexique_data = {{}}
        self.conflicts = []
    
    def parse_lexique_file(self, file_path: str):
        """Parse LexiqueData.txt and extract rankings."""
        # Implementation here
        pass
    
    def fetch_vocabulary_from_supabase(self):
        """Fetch all French vocabulary from Supabase."""
        # Implementation here
        pass
    
    def apply_direct_mapping(self):
        """Apply direct word-to-word mapping."""
        # Implementation here
        pass
    
    def apply_normalization_mapping(self):
        """Apply normalized matching for remaining words."""
        # Implementation here
        pass
    
    def update_supabase_rankings(self, mappings: Dict[str, int]):
        """Update vocabulary table with lexique rankings."""
        # Implementation here
        pass
    
    def generate_conflict_report(self):
        """Generate report of mapping conflicts."""
        # Implementation here
        pass

if __name__ == "__main__":
    mapper = LexiqueRankingMapper()
    # Run mapping process
    pass
'''
        
        print("📄 GENERATED SCRIPT TEMPLATE:")
        print(script_template)
        
        return script_template

def main():
    """Main analysis function."""
    print("🚀 LEXIQUE DATA RANKING ANALYSIS")
    print("="*60)
    
    analyzer = LexiqueRankingAnalyzer()
    
    # Step 1: Parse LexiqueData.txt
    lexique_file = "/Users/ding/Desktop/Coding/Vocabulary Learning App/LexiqueData.txt"
    analyzer.lexique_data = analyzer.parse_lexique_file(lexique_file)
    
    if not analyzer.lexique_data:
        print("❌ Failed to parse LexiqueData.txt. Exiting.")
        return
    
    # Step 2: Fetch vocabulary from Supabase
    analyzer.vocabulary_data = analyzer.fetch_vocabulary_from_supabase()
    
    if not analyzer.vocabulary_data:
        print("❌ Failed to fetch vocabulary data. Exiting.")
        return
    
    # Step 3: Analyze mapping potential
    matches, lexique_only, vocab_only = analyzer.analyze_mapping_potential()
    
    # Step 4: Propose mapping strategy
    strategy, estimated_coverage = analyzer.propose_mapping_strategy(matches, lexique_only, vocab_only)
    
    # Step 5: Generate implementation artifacts
    migration_sql = analyzer.generate_sql_migration(strategy)
    script_template = analyzer.generate_mapping_script_template(strategy)
    
    # Save results
    with open("lexique_mapping_analysis_results.md", "w") as f:
        f.write(f"# LexiqueData Ranking Mapping Analysis\n\n")
        f.write(f"**Strategy**: {strategy.upper()}\n")
        f.write(f"**Estimated Coverage**: {estimated_coverage:.1f}%\n")
        f.write(f"**Direct Matches**: {len(matches)}/{len(analyzer.vocabulary_data)} words\n\n")
        f.write("## SQL Migration\n\n```sql\n")
        f.write(migration_sql)
        f.write("\n```\n\n## Mapping Script Template\n\n```python\n")
        f.write(script_template)
        f.write("\n```\n")
    
    print(f"\n✅ Analysis complete! Results saved to 'lexique_mapping_analysis_results.md'")

if __name__ == "__main__":
    main()
