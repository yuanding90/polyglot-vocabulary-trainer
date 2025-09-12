#!/usr/bin/env python3
"""
Consolidate Enhanced Results Script
Combines all enhanced results into one comprehensive file
"""

import csv
import os
from typing import Dict, List, Tuple

def read_csv_results(filename: str) -> Dict[str, List[str]]:
    """Read CSV results file and return as dictionary"""
    results = {}
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                target_word = row['target_word']
                similar_words_str = row.get('similar_words', '') or row.get('similar_words_with_scores', '')
                
                if similar_words_str:
                    # Parse similar words (remove scores if present)
                    similar_words = []
                    for word_score in similar_words_str.split(', '):
                        # Remove score if present (format: "word (score)")
                        if '(' in word_score:
                            word = word_score.split(' (')[0].strip()
                        else:
                            word = word_score.strip()
                        if word:
                            similar_words.append(word)
                    results[target_word] = similar_words
                else:
                    results[target_word] = []
        
        print(f"✅ Read {len(results)} entries from {filename}")
        return results
        
    except Exception as e:
        print(f"❌ Error reading {filename}: {e}")
        return {}

def create_enhanced_consolidated_file():
    """Create consolidated file with all enhanced results"""
    
    # Files to consolidate (check multiple possible locations)
    possible_files = [
        'enhanced_french_word_similarities.csv',
        'enhanced_french_word_similarities_detailed.csv',
        'batch_results/enhanced_french_word_similarities.csv',
        'batch_results/enhanced_french_word_similarities_detailed.csv',
        'consolidated_results/consolidated_enhanced_french_similarities.csv'
    ]
    
    # Check which files exist
    existing_files = [f for f in possible_files if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No enhanced result files found to consolidate")
        return
    
    print(f"📁 Found {len(existing_files)} enhanced result files to consolidate:")
    for file in existing_files:
        print(f"  - {file}")
    
    # Read all results
    all_results = {}
    for filename in existing_files:
        results = read_csv_results(filename)
        # Merge results (keep the most comprehensive version)
        for word, similar_words in results.items():
            if word not in all_results or len(similar_words) > len(all_results[word]):
                all_results[word] = similar_words
    
    # Sort results alphabetically
    sorted_results = dict(sorted(all_results.items()))
    
    # Create consolidated file
    consolidated_filename = 'consolidated_results/final_enhanced_french_similarities.csv'
    
    # Ensure directory exists
    os.makedirs('consolidated_results', exist_ok=True)
    
    try:
        with open(consolidated_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['target_word', 'similar_words', 'similarity_count', 'rule_types'])
            
            # Write data
            for word, similar_words in sorted_results.items():
                similar_words_str = ', '.join(similar_words) if similar_words else ''
                similarity_count = len(similar_words)
                
                # Determine rule types based on word characteristics
                rule_types = determine_rule_types(word, similar_words)
                
                writer.writerow([word, similar_words_str, similarity_count, rule_types])
        
        print(f"✅ Enhanced consolidated results saved to: {consolidated_filename}")
        print(f"📊 Total words with similarities: {len(sorted_results)}")
        print(f"📊 Total similar word pairs: {sum(len(words) for words in sorted_results.values())}")
        
        # Show statistics
        words_with_similarities = sum(1 for words in sorted_results.values() if words)
        words_without_similarities = len(sorted_results) - words_with_similarities
        
        print(f"📈 Enhanced Algorithm Statistics:")
        print(f"  - Words with similarities: {words_with_similarities}")
        print(f"  - Words without similarities: {words_without_similarities}")
        print(f"  - Average similarities per word: {sum(len(words) for words in sorted_results.values()) / len(sorted_results):.2f}")
        
        # Show sample results
        print(f"\n📋 Sample enhanced consolidated results:")
        sample_count = 0
        for word, similar_words in sorted_results.items():
            if similar_words and sample_count < 15:
                print(f"  {word}: {', '.join(similar_words)}")
                sample_count += 1
        
        # Create enhanced summary report
        create_enhanced_summary_report(sorted_results)
        
    except Exception as e:
        print(f"❌ Error creating consolidated file: {e}")

def determine_rule_types(word: str, similar_words: List[str]) -> str:
    """Determine which rules likely matched this word"""
    rule_types = []
    
    # Check for accent confusion (Rule 1)
    normalized_word = ''.join(c for c in word.lower() if c.isalpha())
    for similar in similar_words:
        normalized_similar = ''.join(c for c in similar.lower() if c.isalpha())
        if normalized_word == normalized_similar:
            rule_types.append("Rule1_Accent")
            break
    
    # Check for consonant skeleton (Rule 5a)
    vowels = "aeiouyàâæéèêëîïôœùûüÿ"
    word_skeleton = ''.join(c for c in word.lower() if c not in vowels and c.isalpha())
    for similar in similar_words:
        similar_skeleton = ''.join(c for c in similar.lower() if c not in vowels and c.isalpha())
        if word_skeleton == similar_skeleton and len(word_skeleton) >= 3:
            rule_types.append("Rule5a_Skeleton")
            break
    
    # Check for edit distance patterns (Rules 2-4)
    for similar in similar_words:
        if len(word) == len(similar):
            # Could be Rule 2 (Near Miss) or Rule 3 (Jumble)
            rule_types.append("Rule2-4_EditDistance")
            break
    
    # Check for structural overlap (Rule 5b)
    for similar in similar_words:
        if len(word) != len(similar):
            rule_types.append("Rule5b_Structural")
            break
    
    return ', '.join(set(rule_types)) if rule_types else "Mixed"

def create_enhanced_summary_report(results: Dict[str, List[str]]):
    """Create a summary report of the enhanced analysis"""
    
    summary_filename = 'consolidated_results/enhanced_analysis_final_summary.txt'
    
    try:
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("ENHANCED FRENCH WORD SIMILARITY ANALYSIS - FINAL SUMMARY REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("ENHANCED ALGORITHM FEATURES:\n")
            f.write("- Cognitive Rules Engine with 6 enhanced rules:\n")
            f.write("  * Rule 1: Accent Confusion (diacritic sensitivity)\n")
            f.write("  * Rule 2: The Near Miss (DLD = 1)\n")
            f.write("  * Rule 3: The Internal Jumble (DLD = 2, Dice > 0.70)\n")
            f.write("  * Rule 4: The Shell Match (LCP ≥ 3, LCS ≥ 1)\n")
            f.write("  * Rule 5a: Perfect Consonant Skeleton Match (NEW)\n")
            f.write("  * Rule 5b: Deep Structural Overlap LCS Ratio ≥ 0.75 (NEW)\n")
            f.write("- Same starting character constraint\n")
            f.write("- Top-5 similar words per target word\n")
            f.write("- Composite similarity scoring\n")
            f.write("- Batch processing with progress tracking\n")
            f.write("- Organized output in subfolders\n\n")
            
            total_words = len(results)
            total_pairs = sum(len(words) for words in results.values())
            words_with_similarities = sum(1 for words in results.values() if words)
            
            f.write("FINAL ANALYSIS RESULTS:\n")
            f.write(f"- Total words with similarities: {total_words}\n")
            f.write(f"- Total similar word pairs: {total_pairs}\n")
            f.write(f"- Words with similarities: {words_with_similarities}\n")
            f.write(f"- Average similarities per word: {total_pairs / total_words if total_words > 0 else 0:.2f}\n\n")
            
            f.write("OUTPUT STRUCTURE:\n")
            f.write("- batch_results/ (main analysis results)\n")
            f.write("- partial_results/ (checkpoint files during processing)\n")
            f.write("- consolidated_results/ (final consolidated files)\n")
            f.write("- final_enhanced_french_similarities.csv (main output)\n\n")
            
            f.write("ENHANCED FEATURES:\n")
            f.write("- Progress tracking with real-time updates\n")
            f.write("- Batch saves every 1000 pairs found\n")
            f.write("- Organized folder structure for results\n")
            f.write("- Rule type identification for each match\n")
            f.write("- Comprehensive similarity scoring\n\n")
            
            f.write("USE CASES:\n")
            f.write("- Language learning: Identify confusing word pairs\n")
            f.write("- Vocabulary training: Focus on similar words\n")
            f.write("- Error analysis: Understand common mistakes\n")
            f.write("- Curriculum design: Group related vocabulary\n")
            f.write("- Research: Analyze French word confusion patterns\n")
        
        print(f"✅ Enhanced summary report saved to: {summary_filename}")
        
    except Exception as e:
        print(f"❌ Error creating enhanced summary report: {e}")

def main():
    """Main function"""
    print("🔄 Consolidating Enhanced French Word Similarity Results")
    print("=" * 60)
    
    # Create consolidated file
    create_enhanced_consolidated_file()
    
    print("\n🎉 Enhanced consolidation complete!")

if __name__ == "__main__":
    main()
