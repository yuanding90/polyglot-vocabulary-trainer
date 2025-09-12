import collections
import unicodedata
import time
import sqlite3
import os
import csv
from typing import List, Dict, Tuple, Set

# -----------------------------------------------------------------------------
# Helper Functions for Metrics
# -----------------------------------------------------------------------------

def normalize_text(text):
    """
    Removes accents and converts to lowercase. e.g., 'Côté' -> 'cote'.
    """
    # Normalize using NFD to separate base characters from diacritics, then filter out diacritics.
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

def get_bigrams(word):
    """Returns a set of bigrams (2-character sequences) for the word."""
    return set([word[i:i+2] for i in range(len(word) - 1)])

def dice_coefficient(word1, word2):
    """
    Calculates the Dice coefficient based on bigram overlap (0 to 1).
    """
    bigrams1 = get_bigrams(word1)
    bigrams2 = get_bigrams(word2)
    
    if not bigrams1 and not bigrams2:
        return 1.0 if word1 == word2 else 0.0

    intersection = len(bigrams1.intersection(bigrams2))
    # Formula: (2 * Intersection) / (Total Bigrams)
    return (2.0 * intersection) / (len(bigrams1) + len(bigrams2))

def damerau_levenshtein_distance(s1, s2):
    """
    Calculates the Damerau-Levenshtein distance (handles transpositions).
    """
    len1, len2 = len(s1), len(s2)
    # Initialize DP matrix
    d = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        d[i][0] = i
    for j in range(len2 + 1):
        d[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            
            d[i][j] = min(
                d[i-1][j] + 1,  # Deletion
                d[i][j-1] + 1,  # Insertion
                d[i-1][j-1] + cost  # Substitution
            )
            
            # Transposition check
            if i > 1 and j > 1 and s1[i-1] == s2[j-2] and s1[i-2] == s2[j-1]:
                d[i][j] = min(d[i][j], d[i-2][j-2] + 1)

    return d[len1][len2]

def get_common_prefix_len(s1, s2):
    count = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            count += 1
        else:
            break
    return count

def get_common_suffix_len(s1, s2):
    return get_common_prefix_len(s1[::-1], s2[::-1])

# -----------------------------------------------------------------------------
# Main Algorithm Logic: Cognitive Rules Engine
# -----------------------------------------------------------------------------

def find_confusable_words(vocabulary, min_word_length=4):
    """
    Identifies cognitively confusing words using the rules-based approach.
    """
    # Configuration for the rules
    MAX_DLD_THRESHOLD = 3      # Maximum distance considered
    DICE_JUMBLE_THRESHOLD = 0.70 # Similarity required for Rule 3
    LCP_SHELL_THRESHOLD = 3    # Prefix length required for Rule 4
    LCS_SHELL_THRESHOLD = 1    # Suffix length required for Rule 4

    # 1. Preprocessing
    cleaned_vocab = set([
        word.strip().lower() for word in vocabulary if len(word.strip()) >= min_word_length
    ])

    # Initialize results storage
    similar_words = collections.defaultdict(set)
    
    # 2. Rule 1: Accent Confusion (Handled efficiently via normalization map)
    print("Checking for accent confusion (Rule 1)...")
    normalized_map = collections.defaultdict(list)
    for i, word in enumerate(cleaned_vocab):
        if i % 1000 == 0:
            print(f"  Processing word {i+1}/{len(cleaned_vocab)} for accent normalization...")
        normalized = normalize_text(word)
        normalized_map[normalized].append(word)

    print("  Finding accent variants...")
    accent_pairs = 0
    for variants in normalized_map.values():
        if len(variants) > 1:
            # If multiple words normalize to the same base, they are confusable
            for i in range(len(variants)):
                for j in range(i + 1, len(variants)):
                    word1, word2 = variants[i], variants[j]
                    # Only consider pairs that start with the same character
                    if word1[0] == word2[0]:
                        similar_words[word1].add(word2)
                        similar_words[word2].add(word1)
                        accent_pairs += 1
    print(f"  Found {accent_pairs} accent confusion pairs (same starting character)")

    # 3. Optimization: Group by length
    words_by_length = collections.defaultdict(list)
    for word in cleaned_vocab:
        words_by_length[len(word)].append(word)

    lengths = sorted(words_by_length.keys())
    
    # 4. Iterative Comparison and Pattern Matching (Rules 2, 3, 4)
    print("Starting iterative pattern matching (Rules 2-4)...")
    total_comparisons = 0
    confusable_pairs = 0
    
    for length_idx, length in enumerate(lengths):
        print(f"  Processing length {length} ({length_idx+1}/{len(lengths)})...")
        
        # Optimization: Only compare words whose lengths differ by at most MAX_DLD_THRESHOLD
        for other_length in range(length, length + MAX_DLD_THRESHOLD + 1):
            if other_length not in words_by_length:
                continue

            words1_list = words_by_length[length]
            words2_list = words_by_length[other_length]

            # Define how to iterate to avoid duplicate comparisons
            if length == other_length:
                iterator = ((words1_list[i], words2_list[j]) 
                            for i in range(len(words1_list)) 
                            for j in range(i + 1, len(words2_list)))
            else:
                iterator = ((word1, word2) 
                            for word1 in words1_list 
                            for word2 in words2_list)

            # Apply Rules Engine
            for word1, word2 in iterator:
                total_comparisons += 1
                
                if total_comparisons % 50000 == 0:
                    print(f"    Processed {total_comparisons:,} comparisons, found {confusable_pairs} confusable pairs...")
                
                # Only consider pairs that start with the same character
                if word1[0] != word2[0]:
                    continue
                
                dl_dist = damerau_levenshtein_distance(word1, word2)

                if dl_dist > MAX_DLD_THRESHOLD:
                    continue

                is_confusable = False

                # Rule 2: The Near Miss
                if dl_dist == 1:
                    is_confusable = True
                
                # Rule 3: The Internal Jumble
                elif dl_dist == 2:
                    if dice_coefficient(word1, word2) > DICE_JUMBLE_THRESHOLD:
                        is_confusable = True

                # Rule 4: The Shell Match
                elif dl_dist > 0: 
                    lcp = get_common_prefix_len(word1, word2)
                    lcs = get_common_suffix_len(word1, word2)
                    if lcp >= LCP_SHELL_THRESHOLD and lcs >= LCS_SHELL_THRESHOLD:
                         is_confusable = True
                
                if is_confusable:
                    # We use sets, so duplicates (e.g., caught by Rule 1 and Rule 2) are handled automatically
                    similar_words[word1].add(word2)
                    similar_words[word2].add(word1)
                    confusable_pairs += 1
                    
                    # Save partial results every 1000 confusable pairs
                    if confusable_pairs % 1000 == 0:
                        print(f"    💾 Checkpoint: Saving partial results with {confusable_pairs} pairs...")
                        partial_mapping = {}
                        for word, similarities in similar_words.items():
                            if similarities:
                                partial_mapping[word] = sorted(list(similarities))
                        save_results_to_csv(partial_mapping, f'partial_results_{confusable_pairs}_pairs.csv')
                        
                        # Also save detailed results with scores
                        detailed_partial = {}
                        for word, similarities in partial_mapping.items():
                            if similarities:
                                top_similar = get_top_similar_words(word, similarities, 5)
                                detailed_partial[word] = top_similar
                        save_detailed_results_to_csv(detailed_partial, f'partial_detailed_{confusable_pairs}_pairs.csv')
    
    print(f"  Completed {total_comparisons:,} total comparisons, found {confusable_pairs} confusable pairs")
    
    # Save final results after all processing
    print(f"💾 Saving final results with {confusable_pairs} confusable pairs...")
    final_mapping = {}
    for word, similarities in similar_words.items():
        if similarities:
            final_mapping[word] = sorted(list(similarities))
    save_results_to_csv(final_mapping, 'final_french_word_similarities.csv')
    
    # Save detailed final results
    detailed_final = {}
    for word, similarities in final_mapping.items():
        if similarities:
            top_similar = get_top_similar_words(word, similarities, 5)
            detailed_final[word] = top_similar
    save_detailed_results_to_csv(detailed_final, 'final_detailed_french_word_similarities.csv')

    return final_mapping

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
# CSV Export Functions
# -----------------------------------------------------------------------------

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

if __name__ == "__main__":
    # --- Configuration ---
    output_file = 'french_word_similarities.csv'
    detailed_output_file = 'french_word_similarities_detailed.csv'
    # Adjust minimum length to ignore very short, simple words
    MIN_LENGTH = 4  # French words can be shorter than English
    TOP_K = 5  # Number of top similar words to keep
    # ---------------------
    
    print("🇫🇷 French Word Similarity Analyzer")
    print("=" * 50)
    
    # Load French vocabulary from all 16 databases
    print("📚 Loading French vocabulary from all 16 databases...")
    full_vocabulary = load_all_french_vocabulary()

    if full_vocabulary:
        print(f"🔍 Analyzing {len(full_vocabulary)} French words using the Cognitive Rules Engine (Min Length={MIN_LENGTH})...")
        start_time = time.time()
        
        # Find confusable words using your cognitive rules engine
        confusable_mappings = find_confusable_words(
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
        
        # Save results to CSV files
        save_results_to_csv(ranked_results, output_file)
        save_detailed_results_to_csv(detailed_results, detailed_output_file)
        
        # Print some examples
        print(f"\n📋 Sample results (first 10 words):")
        for i, (word, similar_words) in enumerate(list(ranked_results.items())[:10]):
            print(f"  {word}: {', '.join(similar_words)}")
        
        print(f"\n🎉 Analysis complete! Check the CSV files:")
        print(f"  - {output_file} (simple format)")
        print(f"  - {detailed_output_file} (with scores)")
        
    else:
        print("❌ Failed to load French vocabulary. Please check the database paths.")