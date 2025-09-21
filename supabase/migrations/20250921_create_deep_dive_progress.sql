-- Create deep_dive_progress table (idempotent)
CREATE TABLE IF NOT EXISTS public.deep_dive_progress (
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  deck_id INTEGER NOT NULL REFERENCES public.vocabulary_decks(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK (category IN ('leeches','learning','strengthening','consolidating')),
  vocabulary_id INTEGER NOT NULL REFERENCES public.vocabulary(id) ON DELETE CASCADE,
  last_viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, deck_id, category, vocabulary_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ddp_user_deck_cat ON public.deep_dive_progress(user_id, deck_id, category);
CREATE INDEX IF NOT EXISTS idx_ddp_deck_cat ON public.deep_dive_progress(deck_id, category);

-- Enable RLS
ALTER TABLE public.deep_dive_progress ENABLE ROW LEVEL SECURITY;

-- Policies
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='deep_dive_progress' AND policyname='ddp_select_own'
  ) THEN
    CREATE POLICY ddp_select_own ON public.deep_dive_progress
      FOR SELECT USING (auth.uid() = user_id OR auth.role() = 'service_role');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='deep_dive_progress' AND policyname='ddp_insert_own'
  ) THEN
    CREATE POLICY ddp_insert_own ON public.deep_dive_progress
      FOR INSERT WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='deep_dive_progress' AND policyname='ddp_update_own'
  ) THEN
    CREATE POLICY ddp_update_own ON public.deep_dive_progress
      FOR UPDATE USING (auth.uid() = user_id OR auth.role() = 'service_role')
      WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');
  END IF;
END $$;

COMMENT ON TABLE public.deep_dive_progress IS 'Tracks which words a user has viewed in Deep Dive by deck and category';


