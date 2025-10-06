import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

export async function GET(request: NextRequest) {
  try {
    console.log('🔥 API: Starting vocabulary heatmap request - THIS SHOULD APPEAR IN SERVER LOGS')
    
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

    // Simplified approach: Get all French vocabulary from 16 French decks
    console.log('API: Fetching all French vocabulary from 16 decks...')
    
    const frenchDeckNames = [
      '12. French 01', '13. French 02', '14. French 03', '15. French 04',
      '16. French 05', '17. French 06', '18. French 07', '19. French 08',
      '20. French 09', '21. French 10', '22. French 11', '23. French 12',
      '24. French 13', '25. French 14', '26. French 15', '27. French 16'
    ]
    
    // First get French deck IDs
    const { data: frenchDecks, error: deckError } = await supabaseAdmin
      .from('vocabulary_decks')
      .select('id, name')
      .in('name', frenchDeckNames)
    
    if (deckError || !frenchDecks || frenchDecks.length === 0) {
      console.error('API: Failed to fetch French deck IDs:', deckError)
      return NextResponse.json({ error: 'Failed to fetch French decks' }, { status: 500 })
    }
    
    const frenchDeckIds = frenchDecks.map(d => d.id)
    console.log('API: Found French deck IDs:', frenchDeckIds.length, 'decks')
    console.log('API: Deck names:', frenchDecks.map(d => d.name))
    
    // Loop through each French deck individually to avoid 1000 limit
    console.log('API: Fetching vocabulary from each French deck individually...')
    let allVocabIds: number[] = []
    
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
    let heatmapData: any[] = []
    const batchSize = 1000
    
    for (let i = 0; i < vocabularyIds.length; i += batchSize) {
      const batch = vocabularyIds.slice(i, i + batchSize)
      try {
        const { data: batchData, error: batchError } = await supabaseAdmin
          .from('vocabulary')
          .select(`
            id,
            language_a_word
          `)
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

    // Fetch user progress data (only for words that have actual progress)
    console.log('API: Fetching user progress for', vocabularyIds.length, 'words...')
    console.log('API: Using user ID:', userId)
    console.log('API: Sample vocabulary IDs:', vocabularyIds.slice(0, 5))
    console.log('API: French deck IDs being processed:', frenchDeckIds)
    
    let userProgressData = []
    try {
      const { data: progressResult, error: progressError } = await supabaseAdmin
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
        .in('deck_id', frenchDeckIds) // Only get progress from French decks

      console.log('API: User progress query result:', {
        dataLength: progressResult?.length || 0,
        error: progressError,
        hasError: !!progressError
      })

      if (progressError) {
        console.log('API: User progress query failed:', progressError.message)
        console.log('API: Full error:', progressError)
        userProgressData = []
      } else {
        let usedFallback = false
        let result = progressResult || []
        if (!result || result.length === 0) {
          console.log('API: Zero progress rows with French deck filter; retrying without deck filter...')
          const { data: fallbackResult, error: fallbackError } = await supabaseAdmin
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
            // No deck filter and no word_id filter as a last resort to detect any progress

          if (fallbackError) {
            console.log('API: Fallback user progress query failed:', fallbackError.message)
          } else {
            usedFallback = true
            result = fallbackResult || []
          }
        }

        userProgressData = result
        console.log('API: User progress fetched:', userProgressData.length, 'words with progress', usedFallback ? '(fallback used)' : '')
        if (userProgressData.length > 0) {
          console.log('API: Sample progress record:', userProgressData[0])
          console.log('API: Progress mastery levels:', userProgressData.map(p => ({
            word_id: p.word_id,
            deck_id: p.deck_id,
            interval: p.interval,
            repetitions: p.repetitions,
            again_count: p.again_count
          })).slice(0, 3))
          
          // Show which French decks have progress
          const decksWithProgress = [...new Set(userProgressData.map(p => p.deck_id))]
          console.log('API: French decks with progress:', decksWithProgress)
        } else {
          console.log('API: No user progress found for user:', userId)
        }
      }
    } catch (error) {
      console.log('API: User progress query failed with exception:', error)
      userProgressData = []
    }

    // Merge per-word progress across all French decks:
    // - If any record is a leech (again_count >= 4), prefer the highest again_count
    // - Otherwise, choose the record with the highest interval
    const LEECH_THRESHOLD = 4
    const progressLookup = new Map<number, { interval: number; again_count: number; repetitions: number }>()
    for (const p of userProgressData as any[]) {
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

      // Determine mastery level based on user progress (using correct SRS logic)
      let masteryLevel: 'new' | 'learning' | 'reviewing' | 'mastered' | 'graduated' | 'leech' | 'unknown' = 'unknown'

      if (userProgress) {
        const LEECH_THRESHOLD = 4 // Align with SRS.LEECH_THRESHOLD from codebase
        
        // Check if it's a leech first
        if (userProgress.again_count >= LEECH_THRESHOLD) {
          masteryLevel = 'leech'
        } else if (userProgress.interval < 7) {
          masteryLevel = 'learning'
        } else if (userProgress.interval < 21) {
          masteryLevel = 'reviewing'
        } else if (userProgress.interval < 60) {
          masteryLevel = 'mastered'
        } else {
          masteryLevel = 'graduated'
        }
      }

      const mappedRank = frequencyByWordId.get(item.id)
      const frequencyRank = typeof mappedRank === 'number' ? mappedRank : Number.MAX_SAFE_INTEGER

      return {
        wordId: item.id,
        word: item.language_a_word,
        frequencyRank,
        masteryLevel,
        confidenceScore: userProgress ? 1 : 0, // 1 if has progress, 0 if unknown
        lastReviewed: null
      }
    })

    // Sort by frequency rank ascending so the grid matches frequency order
    transformedData.sort((a, b) => a.frequencyRank - b.frequencyRank)

    console.log('API: Transformed data summary:')
    console.log('  - Total words:', transformedData.length)
    console.log('  - Words with progress:', progressLookup.size)
    console.log('  - Words without progress (Unknown):', transformedData.length - progressLookup.size)

    // Diagnostics: mapping coverage and top-n sample
    const mappedCount = transformedData.filter(item => Number.isFinite(item.frequencyRank) && item.frequencyRank < Number.MAX_SAFE_INTEGER).length
    const unmappedCount = transformedData.length - mappedCount
    const sampleTop20 = transformedData.slice(0, 20).map(item => ({
      wordId: item.wordId,
      frequencyRank: item.frequencyRank,
      masteryLevel: item.masteryLevel
    }))
    console.log('  - Mapping coverage:', { mappedCount, unmappedCount })
    console.log('  - Sample top-20 (rank/mastery):', sampleTop20)

    return NextResponse.json({
      data: transformedData,
      totalWords: transformedData.length,
      mappedWords: transformedData.filter(item => item.confidenceScore > 0).length,
      unmappedWords: transformedData.filter(item => item.confidenceScore === 0).length,
      diagnostics: {
        deckCount: frenchDeckIds.length,
        vocabularyCount: vocabularyIds.length,
        mapping: { mappedCount, unmappedCount },
        progressMergedCount: progressLookup.size,
        sampleTop20
      }
    })

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