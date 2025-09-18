-- word_ai_content (JSONB Solution 1)
-- Idempotent, additive migration for AI-Tutor content storage

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_tables WHERE schemaname='public' AND tablename='word_ai_content'
  ) THEN
    CREATE TABLE public.word_ai_content (
      id BIGSERIAL PRIMARY KEY,
      vocabulary_id INTEGER NOT NULL REFERENCES public.vocabulary(id) ON DELETE CASCADE,
      l1_language TEXT NOT NULL,
      module_type TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'ready', -- 'pending' | 'ready' | 'failed'
      payload JSONB NOT NULL,
      prompt_version TEXT NOT NULL,
      schema_version TEXT NOT NULL DEFAULT 'v1',
      provider TEXT NOT NULL,
      model TEXT NOT NULL,
      include_analysis BOOLEAN NOT NULL DEFAULT TRUE,
      prompt_hash TEXT NOT NULL,
      is_latest BOOLEAN NOT NULL DEFAULT TRUE,
      moderation_status TEXT NOT NULL DEFAULT 'approved', -- 'approved'|'flagged'|'hidden'
      created_by UUID REFERENCES auth.users(id),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      CONSTRAINT uq_word_ai_idem UNIQUE (vocabulary_id, l1_language, module_type, prompt_hash),
      CONSTRAINT uq_word_ai_latest UNIQUE (vocabulary_id, l1_language, module_type, is_latest) DEFERRABLE INITIALLY DEFERRED
    );
  END IF;
END $$;

-- indexes
CREATE INDEX IF NOT EXISTS idx_ai_content_vocab ON public.word_ai_content(vocabulary_id);
CREATE INDEX IF NOT EXISTS idx_ai_content_vocab_type ON public.word_ai_content(vocabulary_id, module_type) WHERE is_latest AND status='ready';
CREATE INDEX IF NOT EXISTS idx_ai_content_status ON public.word_ai_content(status);
CREATE INDEX IF NOT EXISTS idx_ai_content_payload_gin ON public.word_ai_content USING GIN (payload jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_ai_content_cache_key ON public.word_ai_content (vocabulary_id, l1_language, module_type, prompt_version) WHERE is_latest AND status='ready';

-- RLS policies
ALTER TABLE public.word_ai_content ENABLE ROW LEVEL SECURITY;

-- Read policy: allow authenticated users and service role
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='word_ai_content' AND policyname='ai_content_read'
  ) THEN
    CREATE POLICY ai_content_read ON public.word_ai_content
      FOR SELECT
      USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
  END IF;
END $$;

-- Write policy: service role only
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='word_ai_content' AND policyname='ai_content_write'
  ) THEN
    CREATE POLICY ai_content_write ON public.word_ai_content
      FOR ALL
      TO service_role
      USING (true)
      WITH CHECK (true);
  END IF;
END $$;

COMMENT ON TABLE public.word_ai_content IS 'AI-generated word content (JSONB) with versioning and cache-aside support.';


