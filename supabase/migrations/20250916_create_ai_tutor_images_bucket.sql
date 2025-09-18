-- Create private storage bucket for AI-Tutor images
-- Idempotent: creates bucket only if it does not exist

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id = 'ai_tutor_images'
  ) THEN
    PERFORM storage.create_bucket('ai_tutor_images', public => false);
  END IF;
END $$;

COMMENT ON SCHEMA storage IS 'Supabase Storage schema for file buckets and objects';
COMMENT ON TABLE storage.objects IS 'Storage objects; RLS enforced. ai_tutor_images kept private; access via signed URLs.';


