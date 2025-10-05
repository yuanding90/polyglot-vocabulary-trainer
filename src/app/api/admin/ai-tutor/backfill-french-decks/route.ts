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

type WordInfo = { word_id: number; deck_id: number; deck_name: string }

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

    // 1) Get French deck IDs (French 01 to French 16, excluding Batch 4)
    // For testing: start with just French 01
    const frenchDeckNames = [
      "12. French 01"
      // "13. French 02", "14. French 03", "15. French 04",
      // "16. French 05", "17. French 06", "18. French 07", "19. French 08",
      // "20. French 09", "21. French 10", "22. French 11", "23. French 12",
      // "24. French 13", "25. French 14", "26. French 15", "27. French 16"
    ]

    const { data: decks, error: decksErr } = await supabase
      .from('vocabulary_decks')
      .select('id, name, language_a_name, language_b_name')
      .in('name', frenchDeckNames)

    if (decksErr) {
      return NextResponse.json({ error: decksErr.message }, { status: 500 })
    }

    if (!decks || decks.length === 0) {
      return NextResponse.json({ error: 'No French decks found' }, { status: 404 })
    }

    const deckIds = decks.map(d => d.id)
    console.log(`🇫🇷 Found ${decks.length} French decks to process`)

    // 2) Get all vocabulary from French decks
    const { data: deckVocab, error: vocabErr } = await supabase
      .from('deck_vocabulary')
      .select('vocabulary_id, deck_id')
      .in('deck_id', deckIds)

    if (vocabErr) {
      return NextResponse.json({ error: vocabErr.message }, { status: 500 })
    }

    if (!deckVocab || deckVocab.length === 0) {
      return NextResponse.json({ error: 'No vocabulary found in French decks' }, { status: 404 })
    }

    // 3) Create deck lookup map
    const deckById = new Map<string, { name: string; language_a_name: string; language_b_name: string }>()
    for (const d of decks) {
      deckById.set(d.id, { name: d.name, language_a_name: d.language_a_name, language_b_name: d.language_b_name })
    }

    // 4) Get unique word IDs and check for existing AI content
    const uniqueWordIds = Array.from(new Set(deckVocab.map(dv => dv.vocabulary_id)))
    console.log(`📚 Found ${uniqueWordIds.length} unique words across all French decks`)

    // Check which words already have AI content
    const { data: existingAI, error: aiErr } = await supabase
      .from('word_ai_content')
      .select('vocabulary_id')
      .in('vocabulary_id', uniqueWordIds)
      .eq('module_type', 'ai_tutor_pack')
      .eq('status', 'ready')
      .eq('is_latest', true)

    if (aiErr) {
      return NextResponse.json({ error: aiErr.message }, { status: 500 })
    }

    const existingAIWordIds = new Set((existingAI || []).map(item => item.vocabulary_id))
    const wordsNeedingAI = uniqueWordIds.filter(id => !existingAIWordIds.has(id))
    
    // For testing: limit to first 5 words
    const testWords = wordsNeedingAI.slice(0, 5)
    console.log(`🧪 TEST MODE: Processing only first ${testWords.length} words instead of all ${wordsNeedingAI.length}`)
    
    console.log(`✅ ${existingAIWordIds.size} words already have AI content`)
    console.log(`🔄 ${wordsNeedingAI.length} words need AI content`)

    if (wordsNeedingAI.length === 0) {
      return NextResponse.json({ 
        totalWords: uniqueWordIds.length,
        alreadyHaveAI: existingAIWordIds.size,
        needsAI: 0,
        attempted: 0,
        ready: 0,
        pending: 0,
        errors: 0,
        dryRun 
      })
    }

    // 5) Process words that need AI content
    const origin = new URL(req.url).origin
    const MODULE_TYPE = 'ai_tutor_pack'

    let attempted = 0
    let ready = 0
    let pending = 0
    let errors = 0

    async function processWord(wordId: number) {
      // Find which deck this word belongs to (for language info)
      const wordDeckEntry = deckVocab?.find(dv => dv.vocabulary_id === wordId)
      if (!wordDeckEntry) {
        errors++
        return
      }

      const deck = deckById.get(wordDeckEntry.deck_id)
      if (!deck) {
        errors++
        return
      }

      // Skip if pending exists
      const { data: existingPending } = await supabase
        .from('word_ai_content')
        .select('id')
        .eq('vocabulary_id', wordId)
        .eq('l1_language', deck.language_b_name)
        .eq('module_type', MODULE_TYPE)
        .eq('status', 'pending')
        .limit(1)

      if (existingPending && existingPending.length > 0) {
        console.log(`⏳ Word ${wordId}: Already has pending AI content`)
        pending++
        return
      }

      if (dryRun) {
        attempted++
        return
      }

      attempted++
      try {
        console.log(`🚀 Word ${wordId}: Calling AI generation API...`)
        const r = await fetch(`${origin}/api/ai-tutor/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vocabularyId: wordId,
            l1Language: deck.language_b_name, // English
            l2Language: deck.language_a_name, // French
          }),
        })
        const jj = await r.json().catch(() => ({}))
        
        if (r.ok && jj?.status === 'ready') {
          console.log(`✅ Word ${wordId}: AI content generated successfully`)
          ready++
        } else if (r.status === 202 || jj?.status === 'pending') {
          console.log(`⏳ Word ${wordId}: AI content queued for generation`)
          pending++
        } else {
          console.log(`❌ Word ${wordId}: AI generation failed - Status: ${r.status}, Response:`, jj)
          errors++
        }
      } catch (e) {
        console.log(`❌ Word ${wordId}: AI generation error:`, e)
        errors++
      }
    }

    // Process with controlled concurrency
    const concurrency = 3
    let idx = 0
    let processedCount = 0
    const totalWords = testWords.length
    
    console.log(`🚀 Starting backfill for ${totalWords} words with concurrency ${concurrency}`)
    
    const workers = Array.from({ length: concurrency }).map(async () => {
      while (idx < testWords.length) {
        const current = idx++
        const wordId = testWords[current]
        
        console.log(`📝 Processing word ${current + 1}/${totalWords} (ID: ${wordId})`)
        
        await processWord(wordId)
        
        processedCount++
        const progress = ((processedCount / totalWords) * 100).toFixed(1)
        const remaining = totalWords - processedCount
        const estimatedTimeRemaining = remaining * 15 // rough estimate of 15 seconds per word
        
        console.log(`✅ Progress: ${processedCount}/${totalWords} (${progress}%) | Remaining: ${remaining} words | Est. time: ${Math.round(estimatedTimeRemaining / 60)}min`)
      }
    })
    await Promise.all(workers)

    return NextResponse.json({
      totalWords: uniqueWordIds.length,
      alreadyHaveAI: existingAIWordIds.size,
      needsAI: wordsNeedingAI.length,
      attempted,
      ready,
      pending,
      errors,
      dryRun,
      frenchDecks: decks.map(d => ({ id: d.id, name: d.name }))
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
