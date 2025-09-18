import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

type FetchQuery = {
  vocabularyId?: string
  l1Language?: string
  promptVersion?: string
}

const MODULE_TYPE = 'ai_tutor_pack'
const DEFAULT_PROMPT_VERSION = 'ai-tutor-v1'

function getAdminSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceKey) {
    throw new Error('Server misconfigured: missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  }
  return createClient(url, serviceKey, { auth: { persistSession: false } })
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const q: FetchQuery = {
      vocabularyId: searchParams.get('vocabularyId') || undefined,
      l1Language: searchParams.get('l1Language') || undefined,
      promptVersion: searchParams.get('promptVersion') || undefined,
    }

    if (!q.vocabularyId || !q.l1Language) {
      return NextResponse.json({ error: 'vocabularyId and l1Language are required' }, { status: 400 })
    }

    const promptVersion = q.promptVersion || DEFAULT_PROMPT_VERSION
    const supabase = getAdminSupabase()

    // Try cache hit for ready content with current promptVersion
    const { data: readyRows, error: readyErr } = await supabase
      .from('word_ai_content')
      .select('payload,status')
      .eq('vocabulary_id', Number(q.vocabularyId))
      .eq('l1_language', q.l1Language)
      .eq('module_type', MODULE_TYPE)
      .eq('is_latest', true)
      .eq('status', 'ready')
      .eq('prompt_version', promptVersion)
      .limit(1)

    if (readyErr) {
      return NextResponse.json({ error: readyErr.message }, { status: 500 })
    }

    if (readyRows && readyRows.length > 0) {
      return NextResponse.json({ status: 'ready', payload: readyRows[0].payload })
    }

    // If a pending job exists, report pending
    const { data: pendingRows, error: pendingErr } = await supabase
      .from('word_ai_content')
      .select('status')
      .eq('vocabulary_id', Number(q.vocabularyId))
      .eq('l1_language', q.l1Language)
      .eq('module_type', MODULE_TYPE)
      .eq('status', 'pending')
      .limit(1)

    if (pendingErr) {
      return NextResponse.json({ error: pendingErr.message }, { status: 500 })
    }

    if (pendingRows && pendingRows.length > 0) {
      return NextResponse.json({ status: 'pending' })
    }

    return NextResponse.json({ status: 'miss' }, { status: 404 })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


