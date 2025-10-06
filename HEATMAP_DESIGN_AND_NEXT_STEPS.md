## Vocabulary Heatmap: Design and Next Steps

### Objective
- Render a dense, rectangular, frequency-ordered heatmap of ~15,000 French words (left-to-right, then top-to-bottom), colored by the logged-in user’s mastery status.
- Frequency must come from `french_lexique_words.frequency_rank` via `french_vocabulary_lexique_mapping`.
- Words without progress default to grey.

### Data Sources
- `vocabulary_decks` → deck IDs for 16 French decks.
- `deck_vocabulary` → vocabulary IDs in those decks.
- `french_vocabulary_lexique_mapping` → `vocabulary_id` → `french_lexique_words.frequency_rank`.
- `user_progress` → per-user per-word (deck-scoped) progress.

### API Flow (current)
1. Verify JWT; create service role client.
2. Fetch all 16 French deck IDs by name.
3. Collect and de-duplicate all vocabulary IDs from those decks.
4. Fetch mapping rows: `vocabulary_id`, nested `french_lexique_words.frequency_rank`; coerce to number and keep the smallest rank if duplicates.
5. Fetch `user_progress` for the user filtered by French deck IDs; fallback to all if zero rows; in-memory intersect with vocabulary IDs.
6. Merge progress per word across decks: leech (again_count ≥ 4) dominates; otherwise choose the highest interval.
7. Determine mastery level from merged progress:
   - leech: again_count ≥ 4
   - learning: interval < 7
   - strengthening: 7 ≤ interval < 21
   - consolidating: 21 ≤ interval < 60
   - mastered: interval ≥ 60
   - unknown: no progress
8. Transform payload: `{ wordId, frequencyRank, masteryLevel }`; sort by `frequencyRank` ascending.
9. Return to client.

### Frontend (current)
- Canvas layout auto-fits width/height; computes cols/rows/pixelSize to fill container.
- Sorts data (defensive) by `frequencyRank` ascending; paints left-to-right, top-to-bottom.
- Colors: grey (unknown), orange (learning), yellow (reviewing/strengthening), green (mastered), blue (graduated), red (leech).

### Known Risks / Why ordering may look off
1. Unmapped words (no Lexique rank) currently get `Number.MAX_SAFE_INTEGER` and fall to the bottom/right; if mapping coverage is low, colored pixels may drift.
2. Mixing rank strings and numbers causes lexicographic issues; fixed by coercion to number.
3. If user progress exists on words outside the 16 French decks, fallback can introduce unrelated colors; mitigated by intersecting with vocabulary IDs.
4. If rank coverage is partial across decks, high-frequency studied words could be missing ranks and be sorted after mapped ones.

### Diagnostics to add
- API logs:
  - Deck count, vocabulary count
  - Mapping coverage: `mapped/total`, first 5 `(wordId, rank)`
  - Progress coverage after merge: unique words with progress intersecting vocabulary
- Optional JSON debug endpoint param `?debug=1` to include a small sample in response for verification.

### Next Steps
1. Add mapping coverage diagnostics and return a `coverage` field in API response.
2. Enforce intersection: ensure only vocabulary IDs from the 16 decks are colored.
3. Add deck-order fallback for unmapped words (French 01 → French 16 order) to approximate frequency when rank missing.
4. Run a one-time SQL to measure mapping coverage across all 16 decks; backfill/fix mappings if coverage < 98%.
5. Verify top-left concentration: log first 20 items with `frequencyRank` and `masteryLevel` to confirm ordering.

### Acceptance Criteria
- Heatmap’s top-left quadrant shows the highest concentration of colored pixels for users with substantial progress.
- `wordsWithProgress` equals unique merged progress words intersected with the 16-deck vocabulary set.
- Mapping coverage reported; unmapped words do not pollute top-left ordering.

### Rollout
- Implement diagnostics (small, isolated change), test locally.
- Validate with your account; confirm top-left colors.
- If mapping coverage is low, run backfill for mappings, then re-validate.


