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
    const levelMinParam = url.searchParams.get('levelMin')
    const levelMaxParam = url.searchParams.get('levelMax')
    const levelMin = levelMinParam ? parseInt(levelMinParam, 10) : null
    const levelMax = levelMaxParam ? parseInt(levelMaxParam, 10) : null
    const supabase = getAdminSupabase()

    // 1) Get French deck IDs by language and new naming pattern; fallback to legacy names
    let decks: Array<{ id: string; name: string; language_a_name: string; language_b_name: string }> | null = null
    {
      const { data: byPattern, error: byPatternErr } = await supabase
        .from('vocabulary_decks')
        .select('id, name, language_a_name, language_b_name')
        .eq('language_a_name', 'French')
        .eq('language_b_name', 'English')
        .ilike('name', 'French (by frequency) - Level %')
      if (!byPatternErr && byPattern && byPattern.length > 0) {
        decks = byPattern
      }
    }

    if (!decks || decks.length === 0) {
      const legacyNames = [
        '12. French 01', '13. French 02', '14. French 03', '15. French 04',
        '16. French 05', '17. French 06', '18. French 07', '19. French 08',
        '20. French 09', '21. French 10', '22. French 11', '23. French 12',
        '24. French 13', '25. French 14', '26. French 15', '27. French 16'
      ]
      const { data: byLegacy, error: decksErr } = await supabase
        .from('vocabulary_decks')
        .select('id, name, language_a_name, language_b_name')
        .in('name', legacyNames)
      if (decksErr) {
        return NextResponse.json({ error: decksErr.message }, { status: 500 })
      }
      decks = byLegacy || []
    }

    // Optional level filter for names like "French (by frequency) - Level N" or legacy "French 0N"
    const levelFromName = (name: string | null | undefined): number | null => {
      const s = name || ''
      let m = s.match(/French \(by frequency\) - Level\s*(\d+)/i)
      if (m) return parseInt(m[1], 10)
      m = s.match(/French\s*0?(\d{1,2})\b/i)
      if (m) return parseInt(m[1], 10)
      return null
    }
    if (decks && (levelMin !== null || levelMax !== null)) {
      const before = decks.length
      decks = decks.filter(d => {
        const lvl = levelFromName(d.name)
        if (lvl === null) return false
        if (levelMin !== null && lvl < levelMin) return false
        if (levelMax !== null && lvl > levelMax) return false
        return true
      })
      console.log(`Filtered decks by level range [${levelMin ?? '-'}, ${levelMax ?? '-'}]: ${before} -> ${decks.length}`)
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

    // 4) Process each deck individually to find words needing AI content
    const wordsNeedingAI: Array<{ wordId: number; deckId: string; deckName: string }> = []
    const existingAIWordIds = new Set()
    
    console.log(`📚 Processing ${decks.length} French decks individually`)
    
    // Check each deck individually for existing AI content
    for (const deck of decks) {
      const { data: deckWords } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', deck.id)
      
      if (deckWords && deckWords.length > 0) {
        const deckWordIds = deckWords.map(dw => dw.vocabulary_id)
        console.log(`🔍 Deck ${deck.name}: Found ${deckWordIds.length} words`)
        
        const { data: existingAI } = await supabase
          .from('word_ai_content')
          .select('vocabulary_id')
          .in('vocabulary_id', deckWordIds)
          .eq('module_type', 'ai_tutor_pack')
          .eq('l1_language', deck.language_b_name)
          .eq('status', 'ready')
          .eq('is_latest', true)
        
        const existingForDeck = new Set((existingAI || []).map(item => item.vocabulary_id))
        const wordsNeedingForDeck = deckWordIds.filter(id => !existingForDeck.has(id))
        
        console.log(`✅ Deck ${deck.name}: ${existingForDeck.size} words have AI content, ${wordsNeedingForDeck.length} need AI content`)
        
        // Add words that need AI content for this deck
        wordsNeedingForDeck.forEach(wordId => {
          wordsNeedingAI.push({ wordId, deckId: deck.id, deckName: deck.name })
          existingAIWordIds.add(wordId)
        })
      }
    }
    
    // Use all words that need AI content
    const testWords = wordsNeedingAI
    
    console.log(`✅ ${existingAIWordIds.size} words already have AI content`)
    console.log(`🔄 ${wordsNeedingAI.length} words need AI content`)

    if (wordsNeedingAI.length === 0) {
      return NextResponse.json({ 
        totalWords: existingAIWordIds.size,
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

    async function processWord(wordId: number, deckId: string) {
      const deck = deckById.get(deckId)
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
        const wordData = testWords[current]
        
        console.log(`📝 Processing word ${current + 1}/${totalWords} (ID: ${wordData.wordId}, Deck: ${wordData.deckName})`)
        
        await processWord(wordData.wordId, wordData.deckId)
        
        processedCount++
        const progress = ((processedCount / totalWords) * 100).toFixed(1)
        const remaining = totalWords - processedCount
        const estimatedTimeRemaining = remaining * 15 // rough estimate of 15 seconds per word
        
        console.log(`✅ Progress: ${processedCount}/${totalWords} (${progress}%) | Remaining: ${remaining} words | Est. time: ${Math.round(estimatedTimeRemaining / 60)}min`)
      }
    })
    await Promise.all(workers)

    // Calculate per-deck statistics
    const deckStats = await Promise.all(decks.map(async (deck) => {
      const { data: deckWords } = await supabase
        .from('deck_vocabulary')
        .select('vocabulary_id')
        .eq('deck_id', deck.id)
      
      const deckWordIds = (deckWords || []).map(dw => dw.vocabulary_id)
      const deckWordsWithAI = deckWordIds.filter(id => existingAIWordIds.has(id))
      
      return {
        id: deck.id,
        name: deck.name,
        totalWords: deckWordIds.length,
        wordsWithAI: deckWordsWithAI.length,
        wordsNeedingAI: deckWordIds.length - deckWordsWithAI.length,
        completionPercentage: deckWordIds.length > 0 ? Math.round((deckWordsWithAI.length / deckWordIds.length) * 100) : 0
      }
    }))

    return NextResponse.json({
      totalWords: existingAIWordIds.size + wordsNeedingAI.length,
      alreadyHaveAI: existingAIWordIds.size,
      needsAI: wordsNeedingAI.length,
      attempted,
      ready,
      pending,
      errors,
      dryRun,
      overallCompletionPercentage: Math.round((existingAIWordIds.size / (existingAIWordIds.size + wordsNeedingAI.length)) * 100),
      frenchDecks: deckStats
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
