import React, { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { WordSimilarityService, setMaxSimilarWords, SimilarWord } from '@/lib/services/word-similarity-service'

interface SimilarWordsPanelProps {
  currentWordId: number | null
  currentDeckId: string | null
  max?: number
}

export function SimilarWordsPanel({ currentWordId, currentDeckId, max = 5 }: SimilarWordsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [words, setWords] = useState<SimilarWord[]>([])
  const [scope, setScope] = useState<'deck' | 'global'>('deck')

  useEffect(() => {
    async function load() {
      if (!currentWordId || !currentDeckId) {
        setWords([])
        return
      }
      setLoading(true)
      setError(null)
      try {
        setMaxSimilarWords(max)
        // Default: query globally first
        const global = await WordSimilarityService.getSimilarWords(currentWordId, max)
        if (global && global.length > 0) {
          setWords(global)
          setScope('global')
          return
        }
        // Fallback: restrict to this deck
        const inDeck = await WordSimilarityService.getSimilarWordsInDeck(currentWordId, currentDeckId, max)
        setWords(inDeck)
        setScope('deck')
      } catch {
        setError('Failed to load similar words')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [currentWordId, currentDeckId, max])

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="text-sm sm:text-lg leading-tight">Words Similar in Spelling{scope === 'deck' ? ' (this deck)' : ''}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="text-sm text-gray-500">Loading...</div>
        )}
        {error && (
          <div className="text-sm text-red-600">{error}</div>
        )}
        {!loading && !error && words.length === 0 && (
          <div className="text-sm text-gray-500">No similar words found.</div>
        )}
        {!loading && !error && words.length > 0 && (
          <ul className="space-y-3">
            {words.map((w) => (
              <li key={w.wordId} className="p-3 border rounded-md">
                <div className="">
                  <div className="font-semibold text-gray-900 text-sm sm:text-lg break-words">{w.word}</div>
                  {w.translation && (
                    <div className="text-xs sm:text-base text-gray-700">{w.translation}</div>
                  )}
                </div>
                {(w.sentence || w.sentenceTranslation) && (
                  <div className="mt-2 text-xs sm:text-sm text-gray-700 space-y-1">
                    {w.sentence && <div className="italic break-words line-clamp-2">{w.sentence}</div>}
                    {w.sentenceTranslation && <div className="text-gray-500 break-words line-clamp-2">{w.sentenceTranslation}</div>}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}


