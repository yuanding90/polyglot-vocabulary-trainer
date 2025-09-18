"use client"

import React, { useEffect, useState, useCallback } from 'react'
import { Sparkles } from 'lucide-react'

type Mnemonic = { type: string; content: string }

type Payload = {
  analysis?: {
    usage_context?: {
      nuance_register_note?: string
      collocations?: { l2_phrase: string; l1_meaning: string }[]
      examples?: { l2_sentence: string; l1_translation: string }[]
    }
    connections?: {
      nuanced_synonyms?: { l2_word: string; l1_meaning: string; distinction_note_l1?: string }[]
      antonyms?: { l2_word: string; l1_meaning: string }[]
      word_family?: { l2_word: string; type: string; l1_meaning: string }[]
      mnemonic_aid?: string
    }
    clarification?: {
      confusables?: { l2_word: string; l1_meaning: string; difference_note_l1?: string }[]
      common_mistakes?: string[]
    }
  }
  mnemonics?: Mnemonic[]
  image_brief?: {
    title?: string
  }
  image_asset?: { storage_path: string; width?: number; height?: number }
  other_meanings?: { meaning_l1: string; examples?: { l2_sentence: string; l1_translation: string }[] }[]
  deck_sense_context?: {
    l2_word?: string
    l1_translation?: string
    l2_example_sentence?: string
    l1_example_translation?: string
  }
}

export function AITutorPanel({
  vocabularyId,
  l1Language,
  l2Language,
  visible,
}: {
  vocabularyId: number
  l1Language: string
  l2Language: string
  visible: boolean
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [payload, setPayload] = useState<Payload | null>(null)
  // IMAGE: disabled for now. Keep code commented for later re‑enable.
  // const [imageUrl, setImageUrl] = useState<string | null>(null)
  // const [imageAttempted, setImageAttempted] = useState(false)

  // Reset internal state when the vocabulary changes
  useEffect(() => {
    setLoading(false)
    setError(null)
    setPayload(null)
    // IMAGE: disabled
    // setImageUrl(null)
    // setImageAttempted(false)
  }, [vocabularyId])

  const fetchOrGenerate = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Try fetch (cache hit)
      const q = new URLSearchParams({
        vocabularyId: String(vocabularyId),
        l1Language,
        promptVersion: 'ai-tutor-v1',
      })
      const r = await fetch(`/api/ai-tutor/fetch?${q.toString()}`)
      if (r.ok) {
        const j = await r.json()
        if (j.status === 'ready' && j.payload) {
          setPayload(j.payload as Payload)
          setLoading(false)
          return
        }
      }

      // Cache miss → generate
      const gen = await fetch(`/api/ai-tutor/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
          // Send both languages explicitly so the server formats fields correctly
          body: JSON.stringify({ vocabularyId, l1Language, l2Language }),
      })
      if (!gen.ok) {
        const txt = await gen.text()
        throw new Error(txt || 'Generate failed')
      }

      // Poll fetch until ready
      const poll = async () => {
        for (let i = 0; i < 15; i++) {
          const fr = await fetch(`/api/ai-tutor/fetch?${q.toString()}`)
          if (fr.ok) {
            const jj = await fr.json()
            if (jj.status === 'ready' && jj.payload) {
              setPayload(jj.payload as Payload)
              return
            }
          }
          await new Promise((res) => setTimeout(res, 1500))
        }
        throw new Error('Timed out waiting for AI-Tutor content')
      }

      await poll()
      setLoading(false)
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Failed to load AI-Tutor content'
      setError(message)
      setLoading(false)
    }
  }, [vocabularyId, l1Language, l2Language])

  useEffect(() => {
    if (!visible) return
    if (payload) return
    fetchOrGenerate()
  }, [visible, fetchOrGenerate, payload])

  // Resolve image URL if needed
  // IMAGE: disabled
  // useEffect(() => { /* resolve signed URL */ }, [payload?.image_asset?.storage_path])

  // If payload exists but image missing, allow one automatic attempt to generate image
  // IMAGE: disabled
  // useEffect(() => { /* auto image backfill */ }, [visible, payload, vocabularyId, l1Language])

  if (!visible) return null

  return (
    <div className="mt-8 sm:mt-12 border-t pt-6 sm:pt-8">
      <div className="flex items-center justify-center gap-2">
        <Sparkles className="h-5 w-5 text-violet-500" />
        <h3 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
          AI Tutor Notes
        </h3>
      </div>
      <div className="mt-2 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
      {loading && (
        <p className="text-sm text-slate-500 mt-2">
          Fetching AI‑Tutor insights. This may take ~10–20 seconds on first run…
        </p>
      )}
      {error && (
        <div className="mt-2 text-sm text-red-600">
          <p>{error}</p>
          <button
            className="mt-2 inline-flex items-center rounded bg-slate-800 px-3 py-1 text-white text-sm"
            onClick={() => fetchOrGenerate()}
          >Retry</button>
        </div>
      )}
      {payload && (
        <div className="space-y-4 mt-3">
          {/* 1) Mnemonics */}
          {payload.mnemonics?.length ? (
            <details className="bg-slate-50 p-3 rounded" open>
              <summary className="font-medium cursor-pointer">Mnemonics</summary>
              <ul className="list-disc ml-5 mt-2 text-base space-y-1">
                {payload.mnemonics.map((m, i) => (
                  <li key={i}><span className="font-semibold capitalize">{m.type.replace('_', ' ')}:</span> {m.content}</li>
                ))}
              </ul>
            </details>
          ) : null}

          {/* 2) Analysis (all analysis content incl. connections and clarification) */}
          {payload.analysis && (
            <details className="bg-slate-50 p-3 rounded" open>
              <summary className="font-medium cursor-pointer">Analysis</summary>
              <div className="mt-2 space-y-3">
                {/* Usage context */}
                {payload.analysis.usage_context?.nuance_register_note && (
                  <p className="text-base text-slate-600">{payload.analysis.usage_context.nuance_register_note}</p>
                )}
                {payload.analysis.usage_context?.collocations?.length ? (
                  <div>
                    <h4 className="text-sm font-semibold">Collocations</h4>
                    <ul className="list-disc ml-5 text-base">
                      {payload.analysis.usage_context.collocations.map((c, i) => (
                        <li key={i}>
                          <span className="font-medium">{c.l2_phrase}</span> – {c.l1_meaning}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {payload.analysis.usage_context?.examples?.length ? (
                  <div>
                    <h4 className="text-sm font-semibold">Examples</h4>
                    <div className="space-y-1">
                      {payload.analysis.usage_context.examples.map((ex, i) => (
                        <div key={i} className="border-l-2 border-blue-200 pl-2">
                          <p className="italic text-base">{ex.l2_sentence}</p>
                          <p className="text-sm text-slate-500">{ex.l1_translation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* Connections */}
                {(payload.analysis.connections?.nuanced_synonyms?.length ||
                  payload.analysis.connections?.antonyms?.length ||
                  payload.analysis.connections?.word_family?.length ||
                  payload.analysis.connections?.mnemonic_aid) ? (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold">Connections</h4>
                    {payload.analysis.connections?.nuanced_synonyms?.length ? (
                      <div>
                        <h5 className="text-sm font-medium">Nuanced synonyms</h5>
                    <ul className="list-disc ml-5 text-base">
                          {payload.analysis.connections.nuanced_synonyms.map((s, i) => (
                            <li key={i}>
                              <span className="font-medium">{s.l2_word}</span> – {s.l1_meaning}
                          {s.distinction_note_l1 ? (
                            <div className="text-sm text-slate-500">{s.distinction_note_l1}</div>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {payload.analysis.connections?.antonyms?.length ? (
                      <div>
                        <h5 className="text-sm font-medium">Antonyms</h5>
                    <ul className="list-disc ml-5 text-base">
                          {payload.analysis.connections.antonyms.map((a, i) => (
                            <li key={i}><span className="font-medium">{a.l2_word}</span> – {a.l1_meaning}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {payload.analysis.connections?.word_family?.length ? (
                      <div>
                        <h5 className="text-sm font-medium">Word family</h5>
                    <ul className="list-disc ml-5 text-base">
                          {payload.analysis.connections.word_family.map((w, i) => (
                            <li key={i}><span className="font-medium">{w.l2_word}</span> ({w.type}) – {w.l1_meaning}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {payload.analysis.connections?.mnemonic_aid ? (
                      <div>
                        <h5 className="text-sm font-medium">Mnemonic aid</h5>
                    <p className="text-base">{payload.analysis.connections.mnemonic_aid}</p>
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {/* Clarification */}
                {(payload.analysis.clarification?.confusables?.length || payload.analysis.clarification?.common_mistakes?.length) ? (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold">Clarification</h4>
                    {payload.analysis.clarification?.confusables?.length ? (
                      <div>
                        <h5 className="text-sm font-medium">Confusables</h5>
                    <ul className="list-disc ml-5 text-base">
                          {payload.analysis.clarification.confusables.map((c, i) => (
                            <li key={i}>
                              <span className="font-medium">{c.l2_word}</span> – {c.l1_meaning}
                          {c.difference_note_l1 ? (
                            <div className="text-sm text-slate-500">{c.difference_note_l1}</div>
                              ) : null}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {payload.analysis.clarification?.common_mistakes?.length ? (
                      <div>
                        <h5 className="text-sm font-medium">Common mistakes</h5>
                    <ul className="list-disc ml-5 text-base">
                          {payload.analysis.clarification.common_mistakes.map((m, i) => (
                            <li key={i}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </details>
          )}

          {/* 3) Other meanings (with examples) */}
          {payload.other_meanings?.length ? (
            <details className="bg-slate-50 p-3 rounded">
              <summary className="font-medium cursor-pointer">Other meanings</summary>
              <div className="mt-2 space-y-2">
                {payload.other_meanings.map((om, i) => (
                  <div key={i} className="text-base">
                    <div className="font-medium">{om.meaning_l1}</div>
                    {om.examples?.length ? (
                      <ul className="list-disc ml-5 mt-1 space-y-1">
                        {om.examples.map((ex, j) => (
                          <li key={j}>
                            <div className="italic text-base">{ex.l2_sentence}</div>
                            <div className="text-sm text-slate-500">{ex.l1_translation}</div>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ))}
              </div>
            </details>
          ) : null}

          {/* IMAGE: rendering disabled for now (kept for later re‑enable) */}
          {/* <div className="mt-2"> ... </div> */}
        </div>
      )}
    </div>
  )
}


