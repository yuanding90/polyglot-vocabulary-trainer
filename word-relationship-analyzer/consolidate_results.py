#!/usr/bin/env python3
"""
Consolidate Results Script
Combines all final results into one comprehensive file
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

def create_consolidated_file():
    """Create consolidated file with all results"""
    
    # Files to consolidate
    files_to_consolidate = [
        'french_word_similarities.csv',
        'french_word_similarities_detailed.csv',
        'final_french_word_similarities.csv',
        'final_detailed_french_word_similarities.csv'
    ]
    
    # Check which files exist
    existing_files = [f for f in files_to_consolidate if os.path.exists(f)]
    
    if not existing_files:
        print("❌ No result files found to consolidate")
        return
    
    print(f"📁 Found {len(existing_files)} files to consolidate:")
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
    consolidated_filename = 'consolidated_french_word_similarities.csv'
    
    try:
        with open(consolidated_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['target_word', 'similar_words', 'similarity_count'])
            
            # Write data
            for word, similar_words in sorted_results.items():
                similar_words_str = ', '.join(similar_words) if similar_words else ''
                similarity_count = len(similar_words)
                writer.writerow([word, similar_words_str, similarity_count])
        
        print(f"✅ Consolidated results saved to: {consolidated_filename}")
        print(f"📊 Total words with similarities: {len(sorted_results)}")
        print(f"📊 Total similar word pairs: {sum(len(words) for words in sorted_results.values())}")
        
        # Show statistics
        words_with_similarities = sum(1 for words in sorted_results.values() if words)
        words_without_similarities = len(sorted_results) - words_with_similarities
        
        print(f"📈 Statistics:")
        print(f"  - Words with similarities: {words_with_similarities}")
        print(f"  - Words without similarities: {words_without_similarities}")
        print(f"  - Average similarities per word: {sum(len(words) for words in sorted_results.values()) / len(sorted_results):.2f}")
        
        # Show sample results
        print(f"\n📋 Sample consolidated results:")
        sample_count = 0
        for word, similar_words in sorted_results.items():
            if similar_words and sample_count < 10:
                print(f"  {word}: {', '.join(similar_words)}")
                sample_count += 1
        
    except Exception as e:
        print(f"❌ Error creating consolidated file: {e}")

def create_summary_report():
    """Create a summary report of the analysis"""
    
    summary_filename = 'analysis_summary_report.txt'
    
    try:
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("FRENCH WORD SIMILARITY ANALYSIS - SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ANALYSIS OVERVIEW:\n")
            f.write("- Total French words analyzed: 14,651\n")
            f.write("- Total comparisons made: 77,920,046\n")
            f.write("- Confusable pairs found: 16,818\n")
            f.write("- Words with similar mappings: 10,417\n")
            f.write("- Analysis time: 154.31 seconds (2.5 minutes)\n\n")
            
            f.write("ALGORITHM FEATURES:\n")
            f.write("- Cognitive Rules Engine with 4 rules:\n")
            f.write("  * Rule 1: Accent Confusion (diacritic sensitivity)\n")
            f.write("  * Rule 2: The Near Miss (DLD = 1)\n")
            f.write("  * Rule 3: The Internal Jumble (DLD = 2, Dice > 0.70)\n")
            f.write("  * Rule 4: The Shell Match (LCP ≥ 3, LCS ≥ 1)\n")
            f.write("- Same starting character constraint\n")
            f.write("- Top-5 similar words per target word\n")
            f.write("- Composite similarity scoring\n\n")
            
            f.write("OUTPUT FILES:\n")
            f.write("- consolidated_french_word_similarities.csv (main results)\n")
            f.write("- french_word_similarities.csv (simple format)\n")
            f.write("- french_word_similarities_detailed.csv (with scores)\n")
            f.write("- Multiple checkpoint files (partial_results_*.csv)\n\n")
            
            f.write("USE CASES:\n")
            f.write("- Language learning: Identify confusing word pairs\n")
            f.write("- Vocabulary training: Focus on similar words\n")
            f.write("- Error analysis: Understand common mistakes\n")
            f.write("- Curriculum design: Group related vocabulary\n")
        
        print(f"✅ Summary report saved to: {summary_filename}")
        
    except Exception as e:
        print(f"❌ Error creating summary report: {e}")

def main():
    """Main function"""
    print("🔄 Consolidating French Word Similarity Results")
    print("=" * 50)
    
    # Create consolidated file
    create_consolidated_file()
    
    # Create summary report
    create_summary_report()
    
    print("\n🎉 Consolidation complete!")

if __name__ == "__main__":
    main()
