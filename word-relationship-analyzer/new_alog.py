import collections
import unicodedata
import time
import itertools

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
# Main Algorithm Logic: Enhanced Cognitive Rules Engine
# -----------------------------------------------------------------------------

def find_confusable_words(vocabulary, min_word_length=5):
    
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
    
    # 2. Hashing-Based Rules (Efficient O(N))
    print("Applying Hashing Rules (1: Accent Confusion, 5a: Consonant Skeleton) with same first character constraint...")
    
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
    
    for word in cleaned_vocab:
        # Rule 1
        normalized_map[normalize_text(word)].append(word)
        # Rule 5a
        skeleton = get_consonant_skeleton(word)
        if len(skeleton) >= SKELETON_MIN_LENGTH:
             skeleton_map[skeleton].append(word)

    # Process Rule 1 results
    for variants in normalized_map.values():
        if len(variants) > 1:
            _add_variants(variants)
            
    # Process Rule 5a results
    for variants in skeleton_map.values():
        if len(variants) > 1:
            _add_variants(variants)

    # 3. Optimization for Iterative Rules: Group by length
    words_by_length = collections.defaultdict(list)
    for word in cleaned_vocab:
        words_by_length[len(word)].append(word)
    lengths = sorted(words_by_length.keys())
    
    # 4. Iterative Comparison (Rules 2, 3, 4, 5b)
    print("Starting Iterative Pattern Matching (Rules 2-4, 5b: LCS Ratio) with same first character constraint...")
    for length in lengths:
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

    # 5. Format Output
    final_mapping = {}
    for word, similarities in similar_words.items():
        final_mapping[word] = sorted(list(similarities))
        
    return final_mapping

# -----------------------------------------------------------------------------
# Execution Helpers (Loading and Saving)
# -----------------------------------------------------------------------------

def load_vocabulary(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            vocabulary = [line.strip() for line in f if line.strip()]
        return vocabulary
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        # Fallback list for demonstration if the file is missing
        print("Using a sample list for demonstration.")
        return ["vieillir", "veiller", "poisson", "poison", "côte", "cote", 
                "message", "massage", "dessert", "désert", "fromage", "formage",
                "cousin", "cuisine", "perspective", "prospective"]
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def save_results(results, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Write CSV header
            f.write("target_word,similar_words\n")
            for word in sorted(results.keys()):
                similar = results[word]
                # Limit to top 5 similar words and format as CSV
                top_5_similar = similar[:5]
                similar_str = ', '.join(top_5_similar)
                f.write(f"{word},{similar_str}\n")
        print(f"Results successfully saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving the file: {e}")

if __name__ == "__main__":
    # --- Configuration ---
    vocab_file = 'french_vocab.txt' 
    output_file = 'enhanced_confusable_words.csv'
    MIN_LENGTH = 5 # Minimum length of words to include
    # ---------------------
    
    full_vocabulary = load_vocabulary(vocab_file)

    if full_vocabulary is not None:
        print(f"Analyzing {len(full_vocabulary)} words using the Enhanced Cognitive Rules Engine (Min Length={MIN_LENGTH})...")
        start_time = time.time()
        
        confusable_mappings = find_confusable_words(
            full_vocabulary, 
            min_word_length=MIN_LENGTH
        )

        end_time = time.time()
        
        print(f"\nAnalysis complete in {end_time - start_time:.2f} seconds.")
        print(f"Found {len(confusable_mappings)} words with confusing similarities.")
        
        # Verification check
        if "vieillir" in confusable_mappings and "veiller" in confusable_mappings.get("vieillir", []):
            print("\nVerification Success: 'vieillir' and 'veiller' identified as confusing.")
            
        save_results(confusable_mappings, output_file)