-- French Decks AI Content Statistics Query
-- Run this in Supabase SQL Editor to get accurate per-deck statistics

WITH french_decks AS (
  SELECT id, name, language_a_name, language_b_name
  FROM vocabulary_decks 
  WHERE language_a_name = 'French' 
    AND language_b_name = 'English'
    AND name LIKE 'French (by frequency) - Level %'
),
deck_word_counts AS (
  SELECT 
    d.id as deck_id,
    d.name as deck_name,
    COUNT(dv.vocabulary_id) as total_words
  FROM french_decks d
  LEFT JOIN deck_vocabulary dv ON d.id = dv.deck_id
  GROUP BY d.id, d.name
),
deck_ai_counts AS (
  SELECT 
    d.id as deck_id,
    d.name as deck_name,
    COUNT(DISTINCT dv.vocabulary_id) as words_with_ai,
    COUNT(DISTINCT CASE WHEN wac.status = 'ready' THEN dv.vocabulary_id END) as words_ready,
    COUNT(DISTINCT CASE WHEN wac.status = 'pending' THEN dv.vocabulary_id END) as words_pending,
    COUNT(DISTINCT CASE WHEN wac.status = 'failed' THEN dv.vocabulary_id END) as words_failed
  FROM french_decks d
  LEFT JOIN deck_vocabulary dv ON d.id = dv.deck_id
  LEFT JOIN word_ai_content wac ON dv.vocabulary_id = wac.vocabulary_id 
    AND wac.l1_language = d.language_b_name
    AND wac.module_type = 'ai_tutor_pack'
  GROUP BY d.id, d.name
)
SELECT 
  dwc.deck_name,
  dwc.total_words,
  COALESCE(dac.words_with_ai, 0) as words_with_ai,
  COALESCE(dac.words_ready, 0) as words_ready,
  COALESCE(dac.words_pending, 0) as words_pending,
  COALESCE(dac.words_failed, 0) as words_failed,
  (dwc.total_words - COALESCE(dac.words_with_ai, 0)) as words_needing_ai,
  CASE 
    WHEN dwc.total_words > 0 THEN 
      ROUND((COALESCE(dac.words_with_ai, 0)::decimal / dwc.total_words) * 100, 1)
    ELSE 0 
  END as completion_percentage
FROM deck_word_counts dwc
LEFT JOIN deck_ai_counts dac ON dwc.deck_id = dac.deck_id

UNION ALL

-- Summary totals
SELECT 
  'TOTAL' as deck_name,
  SUM(dwc.total_words) as total_words,
  SUM(COALESCE(dac.words_with_ai, 0)) as words_with_ai,
  SUM(COALESCE(dac.words_ready, 0)) as words_ready,
  SUM(COALESCE(dac.words_pending, 0)) as words_pending,
  SUM(COALESCE(dac.words_failed, 0)) as words_failed,
  SUM(dwc.total_words - COALESCE(dac.words_with_ai, 0)) as words_needing_ai,
  CASE 
    WHEN SUM(dwc.total_words) > 0 THEN 
      ROUND((SUM(COALESCE(dac.words_with_ai, 0))::decimal / SUM(dwc.total_words)) * 100, 1)
    ELSE 0 
  END as completion_percentage
FROM deck_word_counts dwc
LEFT JOIN deck_ai_counts dac ON dwc.deck_id = dac.deck_id

ORDER BY deck_name;
