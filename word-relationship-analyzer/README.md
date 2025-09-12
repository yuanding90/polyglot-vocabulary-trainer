# Word Relationship Analyzer

This subfolder contains algorithms and tools for analyzing vocabulary decks to identify words that are similar in spelling and could be confusing for learners.

## Purpose

The goal is to help learners understand potential spelling confusion and improve their vocabulary retention by:

1. **Identifying Similar Words**: Find words that are similar in spelling, pronunciation, or meaning
2. **Assessing Confusion Risk**: Calculate the likelihood that learners will confuse these words
3. **Providing Learning Insights**: Show learners which words might be confusing and why

## Features (Planned)

### Spelling Similarities
- Edit distance analysis (Levenshtein distance)
- Common substring detection
- Character transposition detection
- Prefix/suffix similarity

### Pronunciation Similarities
- Phonetic matching algorithms
- Homophone detection
- Near-homophone identification
- Language-specific pronunciation rules

### Visual Similarities
- Confusable Unicode character detection
- Similar-looking letter identification
- Font-dependent visual confusion

### Confusion Risk Assessment
- Multi-factor risk calculation
- Word frequency consideration
- Language-specific factors
- Learner difficulty prediction

## Files

- `word_similarity_algorithm.py` - Main algorithm implementation
- `README.md` - This documentation file

## Usage

```python
from word_similarity_algorithm import WordSimilarityAnalyzer

# Initialize analyzer
analyzer = WordSimilarityAnalyzer()

# Load vocabulary from deck
analyzer.load_vocabulary_from_deck(deck_id=1)

# Find similar words
spelling_similarities = analyzer.find_spelling_similarities()
pronunciation_similarities = analyzer.find_pronunciation_similarities()
visual_similarities = analyzer.find_visual_similarities()

# Generate report
report = analyzer.generate_similarity_report()
```

## Integration with Main App

This analyzer will eventually integrate with the main vocabulary trainer app to:

1. **Show Similar Words**: Display confusing word pairs during study sessions
2. **Enhanced Learning**: Provide additional context about potential confusion
3. **Progress Tracking**: Monitor which similar words cause the most difficulty
4. **Adaptive Learning**: Adjust study frequency based on confusion patterns

## Development Status

🚧 **In Development** - This is a placeholder implementation. The actual algorithms need to be implemented.

## Next Steps

1. Implement database connection to load vocabulary words
2. Develop spelling similarity algorithms
3. Add pronunciation similarity detection
4. Create visual similarity analysis
5. Build confusion risk assessment
6. Integrate with main application
