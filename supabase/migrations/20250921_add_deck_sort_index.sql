-- Add a dedicated sorting column to keep display names clean while preserving order
BEGIN;

ALTER TABLE public.vocabulary_decks
  ADD COLUMN IF NOT EXISTS sort_index INTEGER;

-- Backfill sort_index from any leading numeric prefix like "05." or "12-"
-- Examples matched: "05. Foo", "12- Bar", with optional whitespace
UPDATE public.vocabulary_decks
SET sort_index = NULLIF(substring(name FROM '^\s*(\d+)[\.|\-]\s*'), '')::int
WHERE sort_index IS NULL;

-- Optional: index to make ordering efficient
CREATE INDEX IF NOT EXISTS idx_vocabulary_decks_sort_index ON public.vocabulary_decks(sort_index);

COMMIT;


