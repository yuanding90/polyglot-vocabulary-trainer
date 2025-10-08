import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

export async function GET(request: NextRequest) {
  try {
    console.log('🔥 API: Starting vocabulary heatmap request - THIS SHOULD APPEAR IN SERVER LOGS')
    // Compact response toggle
    const url = new URL(request.url)
    const isCompact = url.searchParams.get('compact') === '1'
    
    // Create a service role client for server-side operations
    const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey)
    
    // Get the authorization header
    const authHeader = request.headers.get('authorization')
    console.log('API: Auth header present:', !!authHeader)
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('API: No valid authorization token')
      return NextResponse.json({ error: 'No authorization token' }, { status: 401 })
    }
    
    const token = authHeader.split(' ')[1]
    console.log('API: Token extracted, length:', token.length)
    
    // Verify the JWT token and get user
    const { data: { user }, error: userError } = await supabaseAdmin.auth.getUser(token)
    if (userError || !user) {
      console.log('API: User verification failed:', userError?.message)
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
    }
    
    console.log('API: User verified:', user.id)
    const userId = user.id

    // Fetch all French decks by language and new naming pattern first
    console.log('API: Fetching French decks by language and pattern...')
    let frenchDecks: Array<{ id: string; name: string }>|null = null
    {
      const { data: byPattern, error: byPatternErr } = await supabaseAdmin
        .from('vocabulary_decks')
        .select('id, name')
        .eq('language_a_name', 'French')
        .eq('language_b_name', 'English')
        .ilike('name', 'French (by frequency) - Level %')
      if (byPatternErr) {
        console.error('API: Error fetching French decks by pattern:', byPatternErr)
      } else if (byPattern && byPattern.length > 0) {
        frenchDecks = byPattern
      }
    }

    // Fallback to legacy hard-coded names if new names aren't present yet
    if (!frenchDecks || frenchDecks.length === 0) {
      console.log('API: Falling back to legacy French deck names list')
      const legacyNames = [
        '12. French 01', '13. French 02', '14. French 03', '15. French 04',
        '16. French 05', '17. French 06', '18. French 07', '19. French 08',
        '20. French 09', '21. French 10', '22. French 11', '23. French 12',
        '24. French 13', '25. French 14', '26. French 15', '27. French 16'
      ]
      const { data: byLegacy, error: byLegacyErr } = await supabaseAdmin
        .from('vocabulary_decks')
        .select('id, name')
        .in('name', legacyNames)
      if (byLegacyErr) {
        console.error('API: Error fetching legacy French deck names:', byLegacyErr)
      } else {
        frenchDecks = byLegacy || []
      }
    }

    if (!frenchDecks || frenchDecks.length === 0) {
      console.error('API: No French decks found by pattern or legacy names')
      return NextResponse.json({ error: 'Failed to fetch French decks' }, { status: 500 })
    }

    const frenchDeckIds = frenchDecks.map(d => d.id)
    console.log('API: Found French deck IDs:', frenchDeckIds.length, 'decks')
    console.log('API: Deck names:', frenchDecks.map(d => d.name))
    
    // Loop through each French deck individually to avoid 1000 limit
    console.log('API: Fetching vocabulary from each French deck individually...')
    const allVocabIds: number[] = []
    
    for (const deckId of frenchDeckIds) {
      try {
        const { data: deckVocab, error: deckError } = await supabaseAdmin
          .from('deck_vocabulary')
          .select('vocabulary_id')
          .eq('deck_id', deckId)
        
        if (deckError) {
          console.error(`API: Error fetching vocabulary from deck ${deckId}:`, deckError)
          continue
        }
        
        if (deckVocab && deckVocab.length > 0) {
          const deckVocabIds = deckVocab.map(v => v.vocabulary_id)
          allVocabIds.push(...deckVocabIds)
          console.log(`API: Deck ${deckId}: ${deckVocabIds.length} vocabulary entries`)
        }
      } catch (error) {
        console.error(`API: Error processing deck ${deckId}:`, error)
        continue
      }
    }
    
    // Get unique vocabulary IDs
    const vocabularyIds = [...new Set(allVocabIds)]
    console.log('API: Total vocabulary entries across all decks:', allVocabIds.length)
    console.log('API: Unique vocabulary IDs:', vocabularyIds.length)
    console.log('API: First 5 vocabulary IDs:', vocabularyIds.slice(0, 5))
    console.log('API: Last 5 vocabulary IDs:', vocabularyIds.slice(-5))

    if (vocabularyIds.length === 0) {
      console.log('API: No vocabulary data found')
      return NextResponse.json({ data: [], totalWords: 0, mappedWords: 0, unmappedWords: 0 })
    }

    // Fetch vocabulary data in batches to avoid 1000 limit
    console.log('API: Fetching vocabulary data for', vocabularyIds.length, 'words in batches...')
    const heatmapData: { id: number }[] = []
    const batchSize = 1000
    
    for (let i = 0; i < vocabularyIds.length; i += batchSize) {
      const batch = vocabularyIds.slice(i, i + batchSize)
      try {
        const { data: batchData, error: batchError } = await supabaseAdmin
          .from('vocabulary')
          .select('id')
          .in('id', batch)
        
        if (batchError) {
          console.error(`API: Error fetching vocabulary batch ${i}-${i + batchSize}:`, batchError)
          continue
        }
        
        if (batchData && batchData.length > 0) {
          heatmapData.push(...batchData)
          console.log(`API: Batch ${i}-${i + batchSize}: ${batchData.length} vocabulary records`)
        }
      } catch (error) {
        console.error(`API: Error processing vocabulary batch ${i}-${i + batchSize}:`, error)
        continue
      }
    }

    console.log('API: Total vocabulary data fetched:', heatmapData.length, 'records')

    // Fetch Lexique frequency mapping for ordering (frequencyRank)
    console.log('API: Fetching Lexique frequency mapping for vocabulary IDs...')
    const frequencyByWordId = new Map<number, number>()
    try {
      // Step 1: fetch mapping rows in batches to avoid payload limits
      const mapRows: Array<{ vocabulary_id: number; french_lexique_word_id: number }> = []
      {
        const batchSize = 1000
        for (let i = 0; i < vocabularyIds.length; i += batchSize) {
          const batch = vocabularyIds.slice(i, i + batchSize)
          const { data: mapBatch, error: mapErr } = await supabaseAdmin
            .from('french_vocabulary_lexique_mapping')
            .select('vocabulary_id, french_lexique_word_id')
            .in('vocabulary_id', batch)

          if (mapErr) {
            console.error(`API: Error fetching mapping batch ${i}-${i + batchSize}:`, mapErr)
            continue
          }
          if (mapBatch && mapBatch.length > 0) mapRows.push(...mapBatch)
        }
      }
      console.log('API: Mapping rows fetched:', mapRows.length)

      if (mapRows.length > 0) {
        // Step 2: fetch lexique ranks for referenced lexique IDs
        const lexiqueIds = [...new Set(mapRows.map(r => r.french_lexique_word_id))]
        console.log('API: Unique lexique IDs to fetch:', lexiqueIds.length)

        const rankByLexId = new Map<number, number>()
        {
          const batchSize = 1000
          for (let i = 0; i < lexiqueIds.length; i += batchSize) {
            const batch = lexiqueIds.slice(i, i + batchSize)
            const { data: lexBatch, error: lexErr } = await supabaseAdmin
              .from('french_lexique_words')
              .select('id, frequency_rank')
              .in('id', batch)

            if (lexErr) {
              console.error(`API: Error fetching lexique batch ${i}-${i + batchSize}:`, lexErr)
              continue
            }
            for (const row of lexBatch || []) {
              const rankNum = typeof row.frequency_rank === 'number' ? row.frequency_rank : Number(row.frequency_rank)
              if (Number.isFinite(rankNum)) {
                rankByLexId.set(row.id, rankNum)
              }
            }
          }
        }
        console.log('API: Lexique ranks fetched:', rankByLexId.size)

        // Step 3: assign best (smallest) rank per vocabulary_id
        let assigned = 0
        for (const m of mapRows) {
          const rank = rankByLexId.get(m.french_lexique_word_id)
          if (rank !== undefined) {
            const existing = frequencyByWordId.get(m.vocabulary_id)
            if (existing === undefined || rank < existing) {
              frequencyByWordId.set(m.vocabulary_id, rank)
              assigned++
            }
          }
        }
        console.log('API: Frequency ranks assigned to vocabulary:', assigned)
      } else {
        console.log('API: No mapping rows found for provided vocabulary IDs')
      }
    } catch (error) {
      console.error('API: Exception while fetching frequency mappings:', error)
    }

    // Fetch user progress data (paginate to avoid 1000-row cap) and filter by heatmap vocabulary IDs
    console.log('API: Fetching user progress (paginated) for user:', userId, 'and', vocabularyIds.length, 'lexicon words')
    type ProgressRow = { word_id: number; deck_id: string | number; interval: number; repetitions: number; again_count: number; next_review_date?: string }
    let userProgressData: ProgressRow[] = []
    try {
      const vocabularyIdSet = new Set<number>(vocabularyIds)
      const pageSize = 1000
      let from = 0
      let totalFetched = 0
      while (true) {
        const { data: progressBatch, error: batchErr } = await supabaseAdmin
          .from('user_progress')
          .select(`
            word_id,
            deck_id,
            interval,
            repetitions,
            again_count,
            next_review_date
          `)
          .eq('user_id', userId)
          .order('word_id', { ascending: true })
          .range(from, from + pageSize - 1)

        if (batchErr) {
          console.log(`API: User progress page error at offset ${from}:`, batchErr.message)
          break
        }
        const rows = (progressBatch || []) as ProgressRow[]
        totalFetched += rows.length
        // Keep only progress for words we will render in the heatmap
        for (const r of rows) {
          if (vocabularyIdSet.has(r.word_id)) userProgressData.push(r)
        }
        if (rows.length < pageSize) break
        from += pageSize
      }
      console.log('API: User progress fetched (paginated):', userProgressData.length, 'rows for heatmap; total fetched:', totalFetched)
      if (userProgressData.length > 0) {
        console.log('API: Sample progress row:', userProgressData[0])
      } else {
        console.log('API: No user progress rows intersect heatmap vocabulary for user:', userId)
      }
    } catch (error) {
      console.log('API: Exception while paginating user progress:', error)
      userProgressData = []
    }

    // Merge per-word progress across all French decks:
    // - If any record is a leech (again_count >= 4), prefer the highest again_count
    // - Otherwise, choose the record with the highest interval
    const LEECH_THRESHOLD = 4
    const progressLookup = new Map<number, { interval: number; again_count: number; repetitions: number }>()
    for (const p of userProgressData) {
      const prev = progressLookup.get(p.word_id)
      if (!prev) {
        progressLookup.set(p.word_id, { interval: p.interval || 0, again_count: p.again_count || 0, repetitions: p.repetitions || 0 })
      } else {
        const prevIsLeech = (prev.again_count || 0) >= LEECH_THRESHOLD
        const curIsLeech = (p.again_count || 0) >= LEECH_THRESHOLD
        if (curIsLeech && (!prevIsLeech || (p.again_count || 0) > (prev.again_count || 0))) {
          progressLookup.set(p.word_id, { interval: p.interval || 0, again_count: p.again_count || 0, repetitions: p.repetitions || 0 })
        } else if (!curIsLeech && !prevIsLeech && (p.interval || 0) > (prev.interval || 0)) {
          progressLookup.set(p.word_id, { interval: p.interval || 0, again_count: p.again_count || 0, repetitions: p.repetitions || 0 })
        }
      }
    }
    console.log('API: Unique words with progress after merge:', progressLookup.size)

    // Transform data for the heatmap component
    const transformedData = heatmapData.map((item) => {
      const userProgress = progressLookup.get(item.id)

      // Determine mastery level based on user progress (aligned with dashboard metrics)
      let masteryLevel: 'learning' | 'strengthening' | 'consolidating' | 'mastered' | 'leech' | 'unknown' = 'unknown'

      if (userProgress) {
        const LEECH_THRESHOLD = 4 // Align with SRS.LEECH_THRESHOLD from codebase
        
        // Check if it's a leech first
        if (userProgress.again_count >= LEECH_THRESHOLD) {
          masteryLevel = 'leech'
        } else if (userProgress.interval < 7) {
          masteryLevel = 'learning'
        } else if (userProgress.interval < 21) {
          masteryLevel = 'strengthening'
        } else if (userProgress.interval < 60) {
          masteryLevel = 'consolidating'
        } else {
          masteryLevel = 'mastered'
        }
      }

      const mappedRank = frequencyByWordId.get(item.id)
      const frequencyRank = typeof mappedRank === 'number' ? mappedRank : Number.MAX_SAFE_INTEGER

      return { wordId: item.id, frequencyRank, masteryLevel }
    })

    // Sort by frequency rank ascending so the grid matches frequency order
    transformedData.sort((a, b) => a.frequencyRank - b.frequencyRank)

    console.log('API: Transformed data summary:')
    console.log('  - Total words:', transformedData.length)
    console.log('  - Words with progress:', progressLookup.size)
    console.log('  - Words without progress (Unknown):', transformedData.length - progressLookup.size)

    // Compact mode: return base64 bytes + counts
    if (isCompact) {
      transformedData.sort((a, b) => a.frequencyRank - b.frequencyRank)
      const toCode = (m: string) => (m === 'learning' ? 1 : m === 'strengthening' ? 2 : m === 'consolidating' ? 3 : m === 'mastered' ? 4 : m === 'leech' ? 5 : 0)
      const bytes = new Uint8Array(transformedData.length)
      const counts = { unseen: 0, learning: 0, strengthening: 0, consolidating: 0, mastered: 0, leech: 0 }
      for (let i = 0; i < transformedData.length; i++) {
        const code = toCode(transformedData[i].masteryLevel)
        bytes[i] = code
        if (code === 0) counts.unseen++
        else if (code === 1) counts.learning++
        else if (code === 2) counts.strengthening++
        else if (code === 3) counts.consolidating++
        else if (code === 4) counts.mastered++
        else if (code === 5) counts.leech++
      }
      const base64 = Buffer.from(bytes).toString('base64')
      return NextResponse.json({ compact: true, bytes: base64, totalWords: transformedData.length, counts })
    }

    return NextResponse.json({ data: transformedData, totalWords: transformedData.length, mappedWords: progressLookup.size, unmappedWords: transformedData.length - progressLookup.size })

  } catch (error) {
    console.error('Error in vocabulary heatmap API:', error)
    console.error('Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined
    })
    return NextResponse.json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}