# Enhanced French Word Similarity Algorithm - Requirements Document

## Overview
This document outlines the complete requirements for running the Enhanced French Word Similarity Analysis algorithm. This algorithm uses a Cognitive Rules Engine to identify confusing word pairs in French vocabulary, specifically designed for language learning applications.

## Algorithm Specifications

### MANDATORY CONSTRAINTS (NON-NEGOTIABLE)
These requirements MUST be implemented in every iteration of the algorithm:

1. **Same First Character Constraint** 
   - Only words starting with the same character are considered similar
   - Applied to ALL 6 rules (Rules 1-5b)
   - Implementation: `if word1[0] != word2[0]: continue`

2. **Maximum 5 Similar Words Limit**
   - Each target word can have at most 5 similar words
   - Implementation: `top_5_similar = similar[:5]`
   - Applied during output generation

3. **2-Column CSV Output Format**
   - Must use CSV format with proper headers
   - Headers: `target_word,similar_words`
   - Implementation: `f.write("target_word,similar_words\n")`

### Core Algorithm Features
- **Enhanced Cognitive Rules Engine** with 6 sophisticated rules
- **Same First Character Constraint** - Only words starting with the same character are considered (MANDATORY)
- **Top-5 Similar Words Limit** - Each target word has at most 5 similar words (MANDATORY)
- **2-Column CSV Output Format** - Clean, readable CSV structure (MANDATORY)
- **Composite Similarity Scoring** - Multi-factor ranking system
- **Batch Processing** - Organized processing with progress tracking

### The 6 Enhanced Rules

#### Rule 1: Accent Confusion
- **Purpose**: Identifies words that differ only by diacritics
- **Example**: `côté` vs `cote`
- **Implementation**: Unicode normalization (NFD) to remove accents
- **Threshold**: Exact match after accent removal

#### Rule 2: The Near Miss
- **Purpose**: Identifies words with single character differences
- **Example**: `plan` vs `planque`
- **Implementation**: Damerau-Levenshtein Distance = 1
- **Threshold**: DLD exactly equal to 1

#### Rule 3: The Internal Jumble
- **Purpose**: Identifies words with internal character rearrangements
- **Example**: `message` vs `massage`
- **Implementation**: DLD = 2 AND Dice's Coefficient > 0.70
- **Thresholds**: 
  - DLD = 2
  - Dice coefficient > 0.70

#### Rule 4: The Shell Match
- **Purpose**: Identifies words with significant prefix/suffix overlap
- **Example**: `commander` vs `commando`
- **Implementation**: DLD ≤ 3 AND significant prefix/suffix match
- **Thresholds**:
  - DLD ≤ 3
  - Longest Common Prefix (LCP) ≥ 3
  - Longest Common Suffix (LCS) ≥ 1

#### Rule 5a: Perfect Consonant Skeleton Match (NEW)
- **Purpose**: Identifies words with identical consonant sequences
- **Example**: `vieillir` vs `veiller` (both have skeleton `vllr`)
- **Implementation**: Extract consonant skeleton, exact match
- **Threshold**: Minimum skeleton length ≥ 3 characters

#### Rule 5b: Deep Structural Overlap (NEW)
- **Purpose**: Identifies words with significant structural similarity
- **Example**: `perspective` vs `prospective`
- **Implementation**: Longest Common Subsequence (LCS) ratio ≥ 0.75
- **Threshold**: LCS ratio ≥ 0.75 (75% overlap)

## Data Requirements

### Input Data Sources
- **Source**: 16 French vocabulary databases in SQLite format
- **Location**: `/Users/ding/Desktop/Coding/Vocabulary Learning App/vocab bank/`
- **Database Files**:
  ```
  pre_vocab_batch_1.db
  pre_vocab_batch_2.db
  pre_vocab_batch_3.db
  french_vocab_batch_1.db through french_vocab_batch_13.db
  ```
- **Expected Vocabulary**: ~15,000 unique French words
- **Minimum Word Length**: 4 characters (configurable)

### Data Extraction
- **Table**: `vocabulary`
- **Column**: `french_word`
- **Filters**: 
  - Non-null values
  - Non-empty strings
  - Length ≥ minimum threshold
- **Processing**: Strip whitespace, convert to lowercase

## Processing Requirements

### Performance Specifications
- **Progress Tracking**: Real-time updates every 50,000 comparisons
- **Checkpoint Saves**: Every 1,000 confusable pairs found
- **Memory Management**: Efficient data structures for large vocabulary sets
- **Optimization**: Length-based grouping to reduce unnecessary comparisons

### Algorithm Parameters
```python
# Configuration Parameters
MAX_LEN_DIFF = 4                    # Max length difference for comparison
MAX_DLD_THRESHOLD = 3               # Max Damerau-Levenshtein Distance
DICE_JUMBLE_THRESHOLD = 0.70        # Dice coefficient threshold for jumble rule
LCP_SHELL_THRESHOLD = 3             # Longest Common Prefix threshold
LCS_SHELL_THRESHOLD = 1             # Longest Common Suffix threshold
SKELETON_MIN_LENGTH = 3             # Minimum consonant skeleton length
LCSQ_RATIO_THRESHOLD = 0.75         # LCS ratio threshold (75%)
MIN_WORD_LENGTH = 4                 # Minimum word length to consider
TOP_K = 5                          # Maximum similar words per target word (MANDATORY)

# MANDATORY CONSTRAINTS
FIRST_CHAR_CONSTRAINT = True        # Only words with same first character (MANDATORY)
MAX_SIMILAR_WORDS = 5              # Maximum 5 similar words per target word (MANDATORY)
CSV_OUTPUT_FORMAT = True           # 2-column CSV output format (MANDATORY)
```

## Output Requirements

### File Organization Structure
```
word-relationship-analyzer/
├── batch_results/                  # Main analysis results
│   ├── enhanced_french_word_similarities.csv
│   └── enhanced_french_word_similarities_detailed.csv
├── partial_results/               # Checkpoint files during processing
│   ├── partial_results_XXXX_pairs.csv
│   └── partial_detailed_XXXX_pairs.csv
├── consolidated_results/          # Final consolidated files
│   ├── final_enhanced_french_similarities.csv
│   └── enhanced_analysis_final_summary.txt
└── enhanced_word_similarity_algorithm.py
```

### CSV Output Formats

#### Simple Format (`enhanced_french_word_similarities.csv`)
```csv
target_word,similar_words
abaissement,"apaisement, aboutissement, ahurissement, abattement"
abasourdi,"abasourdir, assourdi, assourdir, absurde, absurdité"
```

#### Detailed Format (`enhanced_french_word_similarities_detailed.csv`)
```csv
target_word,similar_words_with_scores
abaissement,"apaisement (0.850), aboutissement (0.820), ahurissement (0.780)"
abasourdi,"abasourdir (0.920), assourdi (0.880), assourdir (0.860)"
```

#### Consolidated Format (`final_enhanced_french_similarities.csv`)
```csv
target_word,similar_words,similarity_count,rule_types
abaissement,"apaisement, aboutissement, ahurissement, abattement",4,Rule5b_Structural
abasourdi,"abasourdir, assourdi, assourdir, absurde, absurdité",5,"Rule5a_Skeleton, Rule2-4_EditDistance, Rule5b_Structural"
```

### Output Constraints (MANDATORY)
- **Same First Character**: All similar words must start with the same character as target word (MANDATORY)
- **Maximum 5 Similar Words**: Each target word limited to top 5 most similar words (MANDATORY)
- **2-Column CSV Format**: Clean, readable CSV structure with headers (MANDATORY)
- **Rule Type Identification**: Indicate which rules matched each pair
- **CSV Headers**: Must include "target_word,similar_words" headers (MANDATORY)

## Quality Assurance Requirements

### Validation Criteria (MANDATORY CHECKS)
1. **First Character Constraint**: Verify all similar words start with same character (MANDATORY)
2. **Top-5 Limit**: Ensure no target word has more than 5 similar words (MANDATORY)
3. **CSV Format Compliance**: Verify proper 2-column structure with headers (MANDATORY)
4. **CSV Headers**: Confirm "target_word,similar_words" headers are present (MANDATORY)
5. **Rule Type Accuracy**: Confirm correct rule type identification
6. **Progress Tracking**: Validate checkpoint saves and progress updates

### Expected Performance Metrics
- **Processing Time**: ~4-5 minutes for 15,000 words
- **Memory Usage**: Efficient processing without memory overflow
- **Accuracy**: High precision in identifying truly confusing word pairs
- **Completeness**: All words with similarities identified

## Execution Requirements

### Prerequisites
- **Python Environment**: Python 3.7+ with required packages
- **Required Packages**: 
  ```python
  collections
  unicodedata
  time
  itertools
  sqlite3
  os
  csv
  typing
  ```
- **Database Access**: Read access to SQLite vocabulary databases
- **File System**: Write permissions for output directories

### Execution Steps
1. **Setup**: Create required subdirectories
2. **Data Loading**: Extract French words from all 16 databases
3. **Preprocessing**: Clean and filter vocabulary
4. **Hashing Rules**: Apply Rules 1 and 5a (efficient O(N) processing)
5. **Iterative Rules**: Apply Rules 2-4 and 5b (comparison-based processing)
6. **Ranking**: Apply composite similarity scoring
7. **Top-K Selection**: Limit to 5 most similar words per target
8. **Output Generation**: Create all required CSV files
9. **Consolidation**: Merge results into final consolidated file
10. **Summary Report**: Generate comprehensive analysis summary

### Monitoring and Logging
- **Progress Updates**: Every 50,000 comparisons
- **Checkpoint Saves**: Every 1,000 pairs found
- **Error Handling**: Graceful handling of missing databases or files
- **Performance Metrics**: Processing time and memory usage tracking

## Success Criteria

### Functional Requirements (MANDATORY)
✅ **Algorithm Completeness**: All 6 rules implemented and functioning
✅ **First Character Constraint**: Enforced across all similarity matches (MANDATORY)
✅ **Top-5 Limit**: Maximum 5 similar words per target word (MANDATORY)
✅ **2-Column CSV Output**: Clean CSV format with proper headers (MANDATORY)
✅ **CSV Headers**: "target_word,similar_words" headers present (MANDATORY)
✅ **Batch Processing**: Organized folder structure with progress tracking
✅ **Consolidated Results**: Single comprehensive output file

### Performance Requirements
✅ **Processing Time**: Completed in reasonable time (~5 minutes)
✅ **Memory Efficiency**: No memory overflow during processing
✅ **Progress Visibility**: Real-time updates and checkpoint saves
✅ **Error Resilience**: Graceful handling of edge cases

### Quality Requirements
✅ **Accuracy**: High precision in identifying confusing word pairs
✅ **Completeness**: All relevant similarities identified
✅ **Consistency**: Reliable results across multiple runs
✅ **Usability**: Clear, readable output formats for end users

## Maintenance and Iteration

### Future Enhancements
- **Parameter Tuning**: Adjustable thresholds for different use cases
- **Additional Languages**: Extend to other languages beyond French
- **Performance Optimization**: Further speed improvements for larger datasets
- **Rule Expansion**: Additional cognitive rules for specialized cases

### Version Control
- **Algorithm Version**: Enhanced Cognitive Rules Engine v1.0
- **Last Updated**: January 2025
- **Compatibility**: Python 3.7+, SQLite 3.x
- **Dependencies**: Standard library packages only

---

**Note**: This requirements document serves as the definitive specification for running the Enhanced French Word Similarity Analysis algorithm. All iterations should follow these requirements to ensure consistency and quality of results.
