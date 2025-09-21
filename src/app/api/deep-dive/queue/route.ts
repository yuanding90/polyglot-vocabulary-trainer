import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export const runtime = 'nodejs'

type Category = 'leeches' | 'learning' | 'strengthening' | 'consolidating'

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
    const deckId = Number(searchParams.get('deckId') || '')
    const category = (searchParams.get('category') || '') as Category
    const userId = searchParams.get('userId') || ''

    if (!deckId || !category || !userId) {
      return NextResponse.json({ error: 'deckId, category, and userId are required' }, { status: 400 })
    }
    if (!['leeches','learning','strengthening','consolidating'].includes(category)) {
      return NextResponse.json({ error: 'invalid category' }, { status: 400 })
    }

    const supabase = getAdminSupabase()

    // Get deck languages
    const { data: deck, error: deckErr } = await supabase
      .from('vocabulary_decks')
      .select('id, language_a_name, language_b_name')
      .eq('id', deckId)
      .single()
    if (deckErr || !deck) {
      return NextResponse.json({ error: deckErr?.message || 'Deck not found' }, { status: 404 })
    }

    // Get vocabulary ids in deck
    const { data: deckVocab, error: dvErr } = await supabase
      .from('deck_vocabulary')
      .select('vocabulary_id')
      .eq('deck_id', deckId)
    if (dvErr) return NextResponse.json({ error: dvErr.message }, { status: 500 })
    const vocabIds = (deckVocab || []).map((v: { vocabulary_id: number }) => v.vocabulary_id)
    if (vocabIds.length === 0) return NextResponse.json({ queue: [] })

    // Get progress for user in this deck
    const { data: progress, error: pErr } = await supabase
      .from('user_progress')
      .select('word_id, interval, again_count')
      .eq('user_id', userId)
      .eq('deck_id', deckId)
      .in('word_id', vocabIds)
    if (pErr) return NextResponse.json({ error: pErr.message }, { status: 500 })
    const progressByWord = new Map<number, { interval: number; again_count: number }>()
    for (const row of progress || []) progressByWord.set(row.word_id, { interval: row.interval, again_count: row.again_count })

    // Category selection
    const selected: number[] = []
    for (const id of vocabIds) {
      const p = progressByWord.get(id)
      if (!p) continue
      const again = p.again_count || 0
      const interval = p.interval || 0
      const isLeech = again >= 3
      const isLearning = again < 3 && interval < 7
      const isStrength = again < 3 && interval >= 7 && interval < 21
      const isConsol = again < 3 && interval >= 21 && interval < 60
      if (
        (category === 'leeches' && isLeech) ||
        (category === 'learning' && isLearning) ||
        (category === 'strengthening' && isStrength) ||
        (category === 'consolidating' && isConsol)
      ) {
        selected.push(id)
      }
    }
    if (selected.length === 0) return NextResponse.json({ queue: [] })

    // Filter for AI availability
    const { data: aiRows, error: aiErr } = await supabase
      .from('word_ai_content')
      .select('vocabulary_id')
      .in('vocabulary_id', selected)
      .eq('l1_language', deck.language_b_name)
      .eq('module_type', 'ai_tutor_pack')
      .eq('is_latest', true)
      .eq('status', 'ready')
    if (aiErr) return NextResponse.json({ error: aiErr.message }, { status: 500 })
    const aiSet = new Set<number>((aiRows || []).map((r: { vocabulary_id: number }) => r.vocabulary_id))
    const withAI = selected.filter(id => aiSet.has(id))
    if (withAI.length === 0) return NextResponse.json({ queue: [] })

    // Get viewed set for prioritization
    const { data: viewed, error: vErr } = await supabase
      .from('deep_dive_progress')
      .select('vocabulary_id, last_viewed_at')
      .eq('user_id', userId)
      .eq('deck_id', deckId)
      .eq('category', category)
      .in('vocabulary_id', withAI)
    if (vErr) return NextResponse.json({ error: vErr.message }, { status: 500 })
    const viewedSet = new Set<number>((viewed || []).map((r: { vocabulary_id: number }) => r.vocabulary_id))

    const unseen = withAI.filter(id => !viewedSet.has(id))
    const seen = (viewed || [])
      .map((r: { vocabulary_id: number; last_viewed_at: string }) => r)
      .sort((a, b) => new Date(a.last_viewed_at).getTime() - new Date(b.last_viewed_at).getTime())
      .map(r => r.vocabulary_id)

    // Shuffle unseen lightly for variety
    for (let i = unseen.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[unseen[i], unseen[j]] = [unseen[j], unseen[i]]
    }

    const queue = [...unseen, ...seen]
    return NextResponse.json({ queue })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


