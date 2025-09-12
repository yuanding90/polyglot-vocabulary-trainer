import collections
import unicodedata
import time
import itertools
import sqlite3
import os
import csv
from typing import List, Dict, Tuple, Set

# -----------------------------------------------------------------------------
# Helper Functions for Metrics
# -----------------------------------------------------------------------------

def normalize_text(text):
    """Rule 1: Removes accents. 'Côté' -> 'cote'."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

def get_consonant_skeleton(word):
    """
    Rule 5a: Extracts the consonant skeleton. 'vieillir' -> 'vllr'.
    """
    # Comprehensive list of French vowels (lowercase).
    vowels = "aeiouyàâæéèêëîïôœùûüÿ"
    skeleton = ""
    for char in word.lower():
        # Treat 'ç' as 'c' for the skeleton
        if char == 'ç':
            skeleton += 'c'
        elif char not in vowels and char.isalpha():
            skeleton += char
    return skeleton

def get_bigrams(word):
    """Rule 3: Returns a set of bigrams."""
    return set([word[i:i+2] for i in range(len(word) - 1)])

def dice_coefficient(word1, word2):
    """Rule 3: Calculates bigram overlap (0 to 1)."""
    bigrams1 = get_bigrams(word1)
    bigrams2 = get_bigrams(word2)
    
    if not bigrams1 and not bigrams2:
        return 1.0 if word1 == word2 else 0.0

    intersection = len(bigrams1.intersection(bigrams2))
    return (2.0 * intersection) / (len(bigrams1) + len(bigrams2))

def damerau_levenshtein_distance(s1, s2):
    """Rules 2-4: Calculates DLD (handles transpositions)."""
    len1, len2 = len(s1), len(s2)
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1): d[i][0] = i
    for j in range(len2 + 1): d[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            d[i][j] = min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + cost)
            
            if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                d[i][j] = min(d[i][j], d[i-2][j-2] + 1)
    return d[len1][len2]

def get_common_prefix_len(s1, s2):
    """Rule 4: Calculates Longest Common Prefix (LCP)."""
    count = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2: count += 1
        else: break
    return count

def get_common_suffix_len(s1, s2):
    """Rule 4: Calculates Longest Common Suffix."""
    return get_common_prefix_len(s1[::-1], s2[::-1])

def longest_common_subsequence_length(s1, s2):
    """
    Rule 5b: Calculates the length of the LCS using space-optimized DP.
    """
    n, m = len(s1), len(s2)
    # Ensure s2 is the shorter string for optimization (O(min(N,M)) space)
    if n < m:
        s1, s2 = s2, s1
        n, m = m, n
        
    dp = [0] * (m + 1)
    
    for i in range(1, n + 1):
        prev = 0 # Stores the diagonal value (dp[i-1][j-1])
        for j in range(1, m + 1):
            temp = dp[j]
            if s1[i-1] == s2[j-1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j-1])
            prev = temp
    return dp[m]

# -----------------------------------------------------------------------------
# French Vocabulary Extraction from SQLite Databases
# -----------------------------------------------------------------------------

def extract_french_words_from_db(db_path: str) -> List[str]:
    """Extract French words from a SQLite database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT french_word 
            FROM vocabulary 
            WHERE french_word IS NOT NULL AND french_word != ''
            ORDER BY french_word
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        french_words = [row[0].strip() for row in rows if row[0].strip()]
        print(f"📖 Extracted {len(french_words)} French words from {os.path.basename(db_path)}")
        return french_words
        
    except Exception as e:
        print(f"❌ Error reading {db_path}: {e}")
        return []

def load_all_french_vocabulary() -> List[str]:
    """Load French words from all 16 vocabulary databases"""
    vocab_bank_path = "/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank"
    
    # All 16 French vocabulary databases
    french_databases = [
        # Pre-vocabulary batches
        "pre_vocab_batch_1.db",
        "pre_vocab_batch_2.db", 
        "pre_vocab_batch_3.db",
        
        # Main vocabulary batches
        "french_vocab_batch_1.db",
        "french_vocab_batch_2.db",
        "french_vocab_batch_3.db",
        "french_vocab_batch_4.db",
        "french_vocab_batch_5.db",
        "french_vocab_batch_6.db",
        "french_vocab_batch_7.db",
        "french_vocab_batch_8.db",
        "french_vocab_batch_9.db",
        "french_vocab_batch_10.db",
        "french_vocab_batch_11.db",
        "french_vocab_batch_12.db",
        "french_vocab_batch_13.db",
    ]
    
    all_french_words = []
    
    for db_file in french_databases:
        db_path = os.path.join(vocab_bank_path, db_file)
        if os.path.exists(db_path):
            french_words = extract_french_words_from_db(db_path)
            all_french_words.extend(french_words)
        else:
            print(f"⚠️  Database not found: {db_path}")
    
    # Remove duplicates while preserving order
    unique_french_words = list(dict.fromkeys(all_french_words))
    print(f"🎯 Total unique French words: {len(unique_french_words)}")
    
    return unique_french_words

# -----------------------------------------------------------------------------
# Main Algorithm Logic: Enhanced Cognitive Rules Engine with Progress Tracking
# -----------------------------------------------------------------------------

def find_confusable_words_enhanced(vocabulary, min_word_length=4):
    """
    Enhanced Cognitive Rules Engine with 6 rules and progress tracking
    """
    
    # --- Configuration ---
    MAX_LEN_DIFF = 4           # Max length difference for comparison (Optimization)
    MAX_DLD_THRESHOLD = 3      # Max DLD for rules 2-4
    
    # Rule 3 (Jumble)
    DICE_JUMBLE_THRESHOLD = 0.70 
    
    # Rule 4 (Shell)
    LCP_SHELL_THRESHOLD = 3    
    LCS_SHELL_THRESHOLD = 1

    # Rule 5a (Skeleton)
    SKELETON_MIN_LENGTH = 3 # Min skeleton length (e.g., 'vllr' is 4)

    # Rule 5b (LCS Ratio)
    LCSQ_RATIO_THRESHOLD = 0.75 # 75% overlap
    
    # 1. Preprocessing
    cleaned_vocab = set([
        word.strip().lower() for word in vocabulary if len(word.strip()) >= min_word_length
    ])
    similar_words = collections.defaultdict(set)
    
    print(f"🔍 Starting Enhanced Cognitive Rules Engine analysis on {len(cleaned_vocab)} words...")
    
    # 2. Hashing-Based Rules (Efficient O(N))
    print("📊 Applying Hashing Rules (1: Accent Confusion, 5a: Consonant Skeleton) with same first character constraint...")
    
    # Helper for adding matches found via hashing
    def _add_variants(variants_list):
        for word1, word2 in itertools.combinations(variants_list, 2):
            # First character constraint: Only consider words with same starting character
            if word1[0] == word2[0]:
                similar_words[word1].add(word2)
                similar_words[word2].add(word1)

    # Rule 1: Accent Confusion & Rule 5a: Consonant Skeleton Match
    normalized_map = collections.defaultdict(list)
    skeleton_map = collections.defaultdict(list)
    
    processed_words = 0
    for word in cleaned_vocab:
        processed_words += 1
        if processed_words % 1000 == 0:
            print(f"  Processing word {processed_words}/{len(cleaned_vocab)} for hashing rules...")
            
        # Rule 1
        normalized_map[normalize_text(word)].append(word)
        # Rule 5a
        skeleton = get_consonant_skeleton(word)
        if len(skeleton) >= SKELETON_MIN_LENGTH:
             skeleton_map[skeleton].append(word)

    print("  Finding accent variants...")
    accent_pairs = 0
    for variants in normalized_map.values():
        if len(variants) > 1:
            _add_variants(variants)
            accent_pairs += len(variants) * (len(variants) - 1) // 2
    print(f"  Found {accent_pairs} accent confusion pairs")
    
    print("  Finding consonant skeleton matches...")
    skeleton_pairs = 0
    for variants in skeleton_map.values():
        if len(variants) > 1:
            _add_variants(variants)
            skeleton_pairs += len(variants) * (len(variants) - 1) // 2
    print(f"  Found {skeleton_pairs} consonant skeleton pairs")

    # 3. Optimization for Iterative Rules: Group by length
    words_by_length = collections.defaultdict(list)
    for word in cleaned_vocab:
        words_by_length[len(word)].append(word)
    lengths = sorted(words_by_length.keys())
    
    # 4. Iterative Comparison (Rules 2, 3, 4, 5b)
    print("🔄 Starting Iterative Pattern Matching (Rules 2-4, 5b: LCS Ratio) with same first character constraint...")
    total_comparisons = 0
    confusable_pairs = len([pair for word in similar_words for pair in similar_words[word]]) // 2
    
    for length_idx, length in enumerate(lengths):
        print(f"  Processing length {length} ({length_idx+1}/{len(lengths)})...")
        
        # Optimization: Only compare words whose lengths differ by at most MAX_LEN_DIFF
        for other_length in range(length, length + MAX_LEN_DIFF + 1):
            if other_length not in words_by_length:
                continue

            # Define iterator to avoid duplicate comparisons
            if length == other_length:
                iterator = itertools.combinations(words_by_length[length], 2)
            else:
                iterator = itertools.product(words_by_length[length], words_by_length[other_length])

            # Apply Rules Engine
            for word1, word2 in iterator:
                total_comparisons += 1
                
                if total_comparisons % 50000 == 0:
                    print(f"    Processed {total_comparisons:,} comparisons, found {confusable_pairs} confusable pairs...")
                
                # If already matched by hashing rules, skip
                if word2 in similar_words[word1]:
                    continue
                
                # First character constraint: Only consider words with same starting character
                if word1[0] != word2[0]:
                    continue

                is_confusable = False
                len1, len2 = len(word1), len(word2)
                max_len = max(len1, len2)
                min_len = min(len1, len2)

                # Optimization: Check if LCS Ratio is mathematically possible.
                # LCS <= min_len. If min_len/max_len < threshold, LCS/max_len is also < threshold.
                can_meet_lcs_ratio = (min_len / max_len) >= LCSQ_RATIO_THRESHOLD

                # --- Apply Rules 2, 3, 4 (DLD-based) ---
                # Optimization: Only calculate DLD if length difference is within the threshold
                if abs(len1 - len2) <= MAX_DLD_THRESHOLD:
                    dl_dist = damerau_levenshtein_distance(word1, word2)

                    if dl_dist <= MAX_DLD_THRESHOLD and dl_dist > 0:
                        # Rule 2: The Near Miss
                        if dl_dist == 1:
                            is_confusable = True
                        
                        # Rule 3: The Internal Jumble
                        elif dl_dist == 2:
                            if dice_coefficient(word1, word2) > DICE_JUMBLE_THRESHOLD:
                                is_confusable = True

                        # Rule 4: The Shell Match
                        else: 
                            lcp = get_common_prefix_len(word1, word2)
                            lcs = get_common_suffix_len(word1, word2)
                            if lcp >= LCP_SHELL_THRESHOLD and lcs >= LCS_SHELL_THRESHOLD:
                                 is_confusable = True
                
                # --- Apply Rule 5b (LCS Ratio) ---
                # Only run if not already confusable AND the ratio is possible
                if not is_confusable and can_meet_lcs_ratio:
                    lcs_len = longest_common_subsequence_length(word1, word2)
                    if (lcs_len / max_len) >= LCSQ_RATIO_THRESHOLD:
                        is_confusable = True

                # --- Store Result ---
                if is_confusable:
                    similar_words[word1].add(word2)
                    similar_words[word2].add(word1)
                    confusable_pairs += 1
                    
                    # Save partial results every 1000 confusable pairs
                    if confusable_pairs % 1000 == 0:
                        print(f"    💾 Checkpoint: Saving partial results with {confusable_pairs} pairs...")
                        save_partial_results(similar_words, confusable_pairs)

    print(f"  Completed {total_comparisons:,} total comparisons, found {confusable_pairs} confusable pairs")

    # 5. Format Output
    final_mapping = {}
    for word, similarities in similar_words.items():
        if similarities:
            final_mapping[word] = sorted(list(similarities))
        
    return final_mapping

# -----------------------------------------------------------------------------
# Ranking and Top-K Selection
# -----------------------------------------------------------------------------

def calculate_similarity_score(word1: str, word2: str) -> float:
    """Calculate a composite similarity score for ranking"""
    # Get individual metrics
    dl_dist = damerau_levenshtein_distance(word1, word2)
    dice_score = dice_coefficient(word1, word2)
    lcp = get_common_prefix_len(word1, word2)
    lcs = get_common_suffix_len(word1, word2)
    
    # Normalize edit distance (lower is better)
    max_len = max(len(word1), len(word2))
    normalized_dl = 1.0 - (dl_dist / max_len) if max_len > 0 else 0.0
    
    # Weighted composite score
    # Higher weights for more important factors
    composite_score = (
        0.4 * normalized_dl +      # Edit distance (40%)
        0.3 * dice_score +         # Dice coefficient (30%)
        0.2 * (lcp / max_len) +    # Prefix similarity (20%)
        0.1 * (lcs / max_len)      # Suffix similarity (10%)
    )
    
    return composite_score

def get_top_similar_words(word: str, similar_words: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
    """Get top K most similar words with their scores"""
    if not similar_words:
        return []
    
    # Calculate similarity scores for all similar words
    scored_words = []
    for similar_word in similar_words:
        score = calculate_similarity_score(word, similar_word)
        scored_words.append((similar_word, score))
    
    # Sort by score (descending) and take top K
    scored_words.sort(key=lambda x: x[1], reverse=True)
    return scored_words[:top_k]

# -----------------------------------------------------------------------------
# File Management and Batch Processing
# -----------------------------------------------------------------------------

def create_batch_folders():
    """Create subfolders for organizing batch results"""
    folders = [
        'batch_results',
        'partial_results', 
        'consolidated_results'
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"📁 Created folder: {folder}")

def save_partial_results(similar_words: Dict[str, Set[str]], checkpoint_num: int):
    """Save partial results to batch folder"""
    try:
        # Create partial mapping
        partial_mapping = {}
        for word, similarities in similar_words.items():
            if similarities:
                partial_mapping[word] = sorted(list(similarities))
        
        # Save simple format
        filename = f'partial_results/partial_results_{checkpoint_num}_pairs.csv'
        save_results_to_csv(partial_mapping, filename)
        
        # Save detailed format with scores
        detailed_mapping = {}
        for word, similarities in partial_mapping.items():
            if similarities:
                top_similar = get_top_similar_words(word, similarities, 5)
                detailed_mapping[word] = top_similar
        
        detailed_filename = f'partial_results/partial_detailed_{checkpoint_num}_pairs.csv'
        save_detailed_results_to_csv(detailed_mapping, detailed_filename)
        
        print(f"    ✅ Saved checkpoint {checkpoint_num} to batch folders")
        
    except Exception as e:
        print(f"    ❌ Error saving checkpoint {checkpoint_num}: {e}")

def save_results_to_csv(results: Dict[str, List[str]], filename: str):
    """Save word similarity results to CSV file with 2 columns"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['target_word', 'similar_words'])
            
            # Write data
            for word in sorted(results.keys()):
                similar_words = results[word]
                # Join similar words with comma and space, limit to 5 words
                similar_words_str = ', '.join(similar_words[:5])
                writer.writerow([word, similar_words_str])
        
        print(f"✅ Results saved to CSV: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving CSV file: {e}")

def save_detailed_results_to_csv(results: Dict[str, List[Tuple[str, float]]], filename: str):
    """Save detailed word similarity results with scores to CSV file"""
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['target_word', 'similar_words_with_scores'])
            
            # Write data
            for word in sorted(results.keys()):
                similar_words = results[word]
                # Format: "word1 (score1), word2 (score2), ..."
                similar_words_str = ', '.join([f"{similar_word} ({score:.3f})" for similar_word, score in similar_words[:5]])
                writer.writerow([word, similar_words_str])
        
        print(f"✅ Detailed results saved to CSV: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving detailed CSV file: {e}")

def consolidate_final_results(results: Dict[str, List[str]]):
    """Create consolidated final results file"""
    try:
        consolidated_filename = 'consolidated_results/consolidated_enhanced_french_similarities.csv'
        
        with open(consolidated_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['target_word', 'similar_words', 'similarity_count'])
            
            # Write data
            for word in sorted(results.keys()):
                similar_words = results[word]
                similar_words_str = ', '.join(similar_words) if similar_words else ''
                similarity_count = len(similar_words)
                writer.writerow([word, similar_words_str, similarity_count])
        
        print(f"✅ Consolidated results saved to: {consolidated_filename}")
        
        # Create summary report
        create_summary_report(results)
        
    except Exception as e:
        print(f"❌ Error creating consolidated file: {e}")

def create_summary_report(results: Dict[str, List[str]]):
    """Create a summary report of the enhanced analysis"""
    try:
        summary_filename = 'consolidated_results/enhanced_analysis_summary.txt'
        
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("ENHANCED FRENCH WORD SIMILARITY ANALYSIS - SUMMARY REPORT\n")
            f.write("=" * 65 + "\n\n")
            
            f.write("ENHANCED ALGORITHM FEATURES:\n")
            f.write("- Cognitive Rules Engine with 6 enhanced rules:\n")
            f.write("  * Rule 1: Accent Confusion (diacritic sensitivity)\n")
            f.write("  * Rule 2: The Near Miss (DLD = 1)\n")
            f.write("  * Rule 3: The Internal Jumble (DLD = 2, Dice > 0.70)\n")
            f.write("  * Rule 4: The Shell Match (LCP ≥ 3, LCS ≥ 1)\n")
            f.write("  * Rule 5a: Perfect Consonant Skeleton Match (NEW)\n")
            f.write("  * Rule 5b: Deep Structural Overlap LCS Ratio ≥ 0.75 (NEW)\n")
            f.write("- Same starting character constraint (ENFORCED)\n")
            f.write("- Top-5 similar words per target word\n")
            f.write("- Composite similarity scoring\n")
            f.write("- Batch processing with progress tracking\n\n")
            
            total_words = len(results)
            total_pairs = sum(len(words) for words in results.values())
            words_with_similarities = sum(1 for words in results.values() if words)
            
            f.write("ANALYSIS RESULTS:\n")
            f.write(f"- Total words with similarities: {total_words}\n")
            f.write(f"- Total similar word pairs: {total_pairs}\n")
            f.write(f"- Words with similarities: {words_with_similarities}\n")
            f.write(f"- Average similarities per word: {total_pairs / total_words if total_words > 0 else 0:.2f}\n\n")
            
            f.write("OUTPUT FILES:\n")
            f.write("- consolidated_enhanced_french_similarities.csv (main results)\n")
            f.write("- Multiple partial results in partial_results/ folder\n")
            f.write("- Batch results in batch_results/ folder\n\n")
            
            f.write("USE CASES:\n")
            f.write("- Language learning: Identify confusing word pairs\n")
            f.write("- Vocabulary training: Focus on similar words\n")
            f.write("- Error analysis: Understand common mistakes\n")
            f.write("- Curriculum design: Group related vocabulary\n")
        
        print(f"✅ Summary report saved to: {summary_filename}")
        
    except Exception as e:
        print(f"❌ Error creating summary report: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    output_file = 'batch_results/enhanced_french_word_similarities.csv'
    detailed_output_file = 'batch_results/enhanced_french_word_similarities_detailed.csv'
    # Adjust minimum length to ignore very short, simple words
    MIN_LENGTH = 4  # French words can be shorter than English
    TOP_K = 5  # Number of top similar words to keep
    # ---------------------
    
    print("🇫🇷 Enhanced French Word Similarity Analyzer")
    print("=" * 60)
    
    # Create batch folders
    create_batch_folders()
    
    # Load French vocabulary from all 16 databases
    print("📚 Loading French vocabulary from all 16 databases...")
    full_vocabulary = load_all_french_vocabulary()

    if full_vocabulary:
        print(f"🔍 Analyzing {len(full_vocabulary)} French words using the Enhanced Cognitive Rules Engine (Min Length={MIN_LENGTH})...")
        start_time = time.time()
        
        # Find confusable words using your enhanced cognitive rules engine
        confusable_mappings = find_confusable_words_enhanced(
            full_vocabulary, 
            min_word_length=MIN_LENGTH
        )

        end_time = time.time()
        
        print(f"\n⏱️  Analysis complete in {end_time - start_time:.2f} seconds.")
        print(f"🎯 Found {len(confusable_mappings)} words with confusing similarities.")
        
        # Apply top-K ranking to get the most similar words
        print(f"📊 Applying top-{TOP_K} ranking to get the most similar words...")
        ranked_results = {}
        detailed_results = {}
        
        total_words = len(confusable_mappings)
        processed_words = 0
        
        for word, similar_words in confusable_mappings.items():
            if similar_words:  # Only process words that have similar words
                top_similar = get_top_similar_words(word, similar_words, TOP_K)
                ranked_results[word] = [word_score[0] for word_score in top_similar]
                detailed_results[word] = top_similar
            
            processed_words += 1
            if processed_words % 1000 == 0:
                print(f"  Ranked {processed_words}/{total_words} words...")
        
        print(f"✅ Ranking complete. {len(ranked_results)} words have similar word mappings.")
        
        # Save final results to batch folders
        save_results_to_csv(ranked_results, output_file)
        save_detailed_results_to_csv(detailed_results, detailed_output_file)
        
        # Create consolidated results
        consolidate_final_results(ranked_results)
        
        # Print some examples
        print(f"\n📋 Sample enhanced results (first 10 words):")
        for i, (word, similar_words) in enumerate(list(ranked_results.items())[:10]):
            print(f"  {word}: {', '.join(similar_words)}")
        
        print(f"\n🎉 Enhanced analysis complete! Check the folders:")
        print(f"  - batch_results/ (main results)")
        print(f"  - partial_results/ (checkpoint files)")
        print(f"  - consolidated_results/ (final consolidated file)")
        
    else:
        print("❌ Failed to load French vocabulary. Please check the database paths.")
