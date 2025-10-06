import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

function getAdminSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceKey) {
    throw new Error('Server misconfigured: missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  }
  return createClient(url, serviceKey, { auth: { persistSession: false } })
}

type Pair = { word_id: number; deck_id: number }

export async function POST(req: Request) {
  try {
    const token = req.headers.get('x-backfill-token') || ''
    const expected = process.env.AI_TUTOR_ADMIN_TOKEN || ''
    if (!expected || token !== expected) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const url = new URL(req.url)
    const dryRun = url.searchParams.get('dryRun') === 'true'
    const supabase = getAdminSupabase()

    // 1) Collect unique (word_id, deck_id) pairs where again_count >= 3
    const pageSize = 1000
    let from = 0
    const uniquePairs = new Set<string>()
    const pairs: Pair[] = []

    while (true) {
      const { data, error } = await supabase
        .from('user_progress')
        .select('word_id, deck_id, again_count')
        .gte('again_count', 3)
        .range(from, from + pageSize - 1)

      if (error) {
        return NextResponse.json({ error: error.message }, { status: 500 })
      }
      if (!data || data.length === 0) break

      for (const row of data as Array<{ word_id: number; deck_id: number; again_count: number }>) {
        const key = `${row.word_id}:${row.deck_id}`
        if (!uniquePairs.has(key)) {
          uniquePairs.add(key)
          pairs.push({ word_id: row.word_id, deck_id: row.deck_id })
        }
      }

      if (data.length < pageSize) break
      from += pageSize
    }

    if (pairs.length === 0) {
      return NextResponse.json({ scanned: 0, toProcess: 0, skipped: 0, attempted: 0, ready: 0, pending: 0, errors: 0 })
    }

    // 2) Load deck language names for all deck_ids
    const deckIds = Array.from(new Set(pairs.map(p => p.deck_id)))
    const { data: decks, error: decksErr } = await supabase
      .from('vocabulary_decks')
      .select('id, language_a_name, language_b_name')
      .in('id', deckIds)

    if (decksErr) {
      return NextResponse.json({ error: decksErr.message }, { status: 500 })
    }
    const deckById = new Map<number, { language_a_name: string; language_b_name: string }>()
    for (const d of (decks || []) as Array<{ id: number; language_a_name: string; language_b_name: string }>) {
      deckById.set(d.id, { language_a_name: d.language_a_name, language_b_name: d.language_b_name })
    }

    // 3) Process pairs with small concurrency
    const origin = new URL(req.url).origin
    const MODULE_TYPE = 'ai_tutor_pack'
    const DEFAULT_PROMPT_VERSION = 'ai-tutor-v1'

    let skipped = 0
    let attempted = 0
    let ready = 0
    let pending = 0
    let errors = 0

    async function processPair(p: Pair) {
      const deck = deckById.get(p.deck_id)
      if (!deck) {
        skipped++
        return
      }

      // Skip if already READY for this L1
      const { data: existingReady, error: existErr } = await supabase
        .from('word_ai_content')
        .select('id')
        .eq('vocabulary_id', p.word_id)
        .eq('l1_language', deck.language_b_name)
        .eq('module_type', MODULE_TYPE)
        .eq('is_latest', true)
        .eq('status', 'ready')
        .eq('prompt_version', DEFAULT_PROMPT_VERSION)
        .limit(1)

      if (!existErr && existingReady && existingReady.length > 0) {
        skipped++
        return
      }

      if (dryRun) {
        attempted++
        return
      }

      // If pending exists, count pending and skip duplicate generation
      const { data: existingPending } = await supabase
        .from('word_ai_content')
        .select('id')
        .eq('vocabulary_id', p.word_id)
        .eq('l1_language', deck.language_b_name)
        .eq('module_type', MODULE_TYPE)
        .eq('status', 'pending')
        .limit(1)

      if (existingPending && existingPending.length > 0) {
        pending++
        return
      }

      attempted++
      try {
        const r = await fetch(`${origin}/api/ai-tutor/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vocabularyId: p.word_id,
            l1Language: deck.language_b_name,
            l2Language: deck.language_a_name,
          }),
        })
        const jj = await r.json().catch(() => ({}))
        if (r.ok && jj?.status === 'ready') {
          ready++
        } else if (r.status === 202 || jj?.status === 'pending') {
          pending++
        } else {
          errors++
        }
      } catch {
        errors++
      }
    }

    const concurrency = 3
    let idx = 0
    const workers = Array.from({ length: concurrency }).map(async () => {
      while (idx < pairs.length) {
        const current = idx++
        await processPair(pairs[current])
      }
    })
    await Promise.all(workers)

    return NextResponse.json({
      scanned: uniquePairs.size,
      toProcess: pairs.length,
      skipped,
      attempted,
      ready,
      pending,
      errors,
      dryRun,
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


