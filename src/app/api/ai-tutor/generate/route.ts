import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import OpenAI from 'openai'

export const runtime = 'nodejs'

// IMAGE: disabled for now. Set to true to re-enable image generation later.
const ENABLE_IMAGE_GENERATION = false

type GenerateBody = {
  vocabularyId?: number
  l1Language?: string
  l2Language?: string
  includeAnalysis?: boolean
  forceImage?: boolean
}

const MODULE_TYPE = 'ai_tutor_pack'
const DEFAULT_PROMPT_VERSION = 'ai-tutor-v1'
const SCHEMA_VERSION = 'v1'

function getAdminSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY
  if (!url || !serviceKey) {
    throw new Error('Server misconfigured: missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY')
  }
  return createClient(url, serviceKey, { auth: { persistSession: false } })
}

function normalizeForHash(input: unknown) {
  return JSON.stringify(input)
}

async function sha256Base64(s: string) {
  const enc = new TextEncoder().encode(s)
  const hashBuf = await crypto.subtle.digest('SHA-256', enc)
  const bytes = Buffer.from(hashBuf)
  return bytes.toString('base64')
}

export async function POST(req: Request) {
  try {
    const body: GenerateBody = await req.json().catch(() => ({}))
    if (!body.vocabularyId || !body.l1Language) {
      return NextResponse.json({ error: 'vocabularyId and l1Language are required' }, { status: 400 })
    }

    const includeAnalysis = body.includeAnalysis ?? true
    const promptVersion = DEFAULT_PROMPT_VERSION
    const supabase = getAdminSupabase()

    // Load vocabulary details required for prompt assembly
    const { data: vocabRow, error: vocabErr } = await supabase
      .from('vocabulary')
      .select('id, language_a_word, language_b_translation, language_a_sentence, language_b_sentence')
      .eq('id', body.vocabularyId)
      .single()

    if (vocabErr || !vocabRow) {
      return NextResponse.json({ error: vocabErr?.message || 'Vocabulary not found' }, { status: 404 })
    }

    const promptInputs = {
      vocabulary_id: vocabRow.id,
      l1_language: body.l1Language,
      l2_language: body.l2Language || 'auto',
      target_word: vocabRow.language_a_word,
      translation: vocabRow.language_b_translation,
      l2_ipa: '',
      include_analysis: includeAnalysis,
      prompt_version: promptVersion,
      schema_version: SCHEMA_VERSION,
      module_type: MODULE_TYPE,
      deck_sense_context: {
        l2_word: vocabRow.language_a_word,
        l1_translation: vocabRow.language_b_translation,
        l2_example_sentence: vocabRow.language_a_sentence,
        l1_example_translation: vocabRow.language_b_sentence,
      },
    }

    const promptHash = await sha256Base64(normalizeForHash(promptInputs))

    // Idempotent insert: if pending/ready row with same hash exists, report pending
    const { data: existingRows, error: existErr } = await supabase
      .from('word_ai_content')
      .select('status, payload')
      .eq('vocabulary_id', vocabRow.id)
      .eq('l1_language', body.l1Language)
      .eq('module_type', MODULE_TYPE)
      .eq('prompt_hash', promptHash)
      .limit(1)

    if (existErr) {
      return NextResponse.json({ error: existErr.message }, { status: 500 })
    }
    if (existingRows && existingRows.length > 0) {
      type ImageAsset = { storage_path?: string }
      type PayloadShape = { image_asset?: ImageAsset; image_brief?: { prompt?: string } }
      const r = existingRows[0] as { status: string; payload?: PayloadShape }
      if (r.status === 'ready') {
        // Image backfill disabled: return cached payload as-is
        return NextResponse.json({ status: 'ready', payload: r.payload })
      }
      return NextResponse.json({ status: 'pending' })
    }

    // Insert pending row
    const { data: inserted, error: insertErr } = await supabase.from('word_ai_content').insert({
      vocabulary_id: vocabRow.id,
      l1_language: body.l1Language,
      module_type: MODULE_TYPE,
      status: 'pending',
      payload: {},
      prompt_version: promptVersion,
      schema_version: SCHEMA_VERSION,
      provider: 'openai',
      model: 'gpt-4.1-nano',
      include_analysis: includeAnalysis,
      prompt_hash: promptHash,
      is_latest: false,
    }).select('id').single()
    if (insertErr) {
      return NextResponse.json({ error: insertErr.message }, { status: 500 })
    }

    const openaiApiKey = process.env.OPENAI_API_KEY
    if (!openaiApiKey) {
      // Keep pending if key not configured
      return NextResponse.json({ status: 'pending', note: 'OPENAI_API_KEY not set' }, { status: 202 })
    }

    const openai = new OpenAI({
      apiKey: openaiApiKey,
      organization: process.env.OPENAI_ORG_ID,
      project: process.env.OPENAI_PROJECT,
    })

    // Build prompt with deck sense context and other_meanings section
    const system = 'You are an expert linguist, language tutor, and memory coach. Output ONLY a single JSON object; no extra text.'
    const includeAnalysisFlag = includeAnalysis ? 'true' : 'false'
    const userPrompt = `A learner whose base language is ${promptInputs.l1_language} is learning ${promptInputs.l2_language}.

Goal: Produce ONE JSON object containing (a) an optional lexical analysis, (b) EXACTLY three mnemonics, and (c) an image brief, and (d) a section listing other meanings not covered by the current deck sense. All explanatory notes and translations must be in ${promptInputs.l1_language}. Do NOT include any text outside the JSON.

Important constraints:
- All explanatory text, labels, and translations must be in ${promptInputs.l1_language}.
- For usage examples, the "l2_sentence" must be in ${promptInputs.l2_language}, and the corresponding "l1_translation" must be in ${promptInputs.l1_language}.

Sense anchoring (use this exact deck sense):
- l2_word: ${promptInputs.deck_sense_context.l2_word}
- l1_translation: ${promptInputs.deck_sense_context.l1_translation}
- l2_example_sentence: ${promptInputs.deck_sense_context.l2_example_sentence}
- l1_example_translation: ${promptInputs.deck_sense_context.l1_example_translation}

Inputs (Required): {L1_Language=${promptInputs.l1_language}}, {L2_Language=${promptInputs.l2_language}}, {Target_Word=${promptInputs.target_word}}, {Translation=${promptInputs.translation}}
Inputs (Optional): {L2_IPA=${promptInputs.l2_ipa}}, {include_analysis=${includeAnalysisFlag}}

Output schema (exact top-level keys in one JSON object):
{
  "analysis": {
    "usage_context": {
      "nuance_register_note": "",
      "collocations": [ { "l2_phrase": "", "l1_meaning": "" }, { "l2_phrase": "", "l1_meaning": "" }, { "l2_phrase": "", "l1_meaning": "" } ],
      "examples": [ { "l2_sentence": "", "l1_translation": "" }, { "l2_sentence": "", "l1_translation": "" }, { "l2_sentence": "", "l1_translation": "" } ]
    },
    "connections": {
      "nuanced_synonyms": [ { "l2_word": "", "l1_meaning": "", "distinction_note_l1": "" }, { "l2_word": "", "l1_meaning": "", "distinction_note_l1": "" } ],
      "antonyms": [ { "l2_word": "", "l1_meaning": "" } ],
      "word_family": [ { "l2_word": "", "type": "", "l1_meaning": "" }, { "l2_word": "", "type": "", "l1_meaning": "" } ],
      "mnemonic_aid": ""
    },
    "clarification": {
      "confusables": [ { "l2_word": "", "l1_meaning": "", "difference_note_l1": "" }, { "l2_word": "", "l1_meaning": "", "difference_note_l1": "" } ],
      "common_mistakes": [ "", "" ]
    }
  },
  "mnemonics": [
    { "type": "phonetic_link", "content": "(1–2 sentences in ${promptInputs.l1_language}.)" },
    { "type": "absurd_story", "content": "(≤2 sentences in ${promptInputs.l1_language}.)" },
    { "type": "visualization_cue", "content": "(One scene in ${promptInputs.l1_language}.)" }
  ],
  "image_brief": {
    "title": "",
    "prompt": "",
    "style": "",
    "elements": ["", "", ""],
    "composition": "",
    "lighting": "",
    "color_palette": "",
    "aspect_ratio": "1:1",
    "safety_notes": ""
  },
  "other_meanings": [
    { "meaning_l1": "", "examples": [ { "l2_sentence": "", "l1_translation": "" } ] }
  ],
  "deck_sense_context": {
    "l2_word": "${promptInputs.deck_sense_context.l2_word}",
    "l1_translation": "${promptInputs.deck_sense_context.l1_translation}",
    "l2_example_sentence": "${promptInputs.deck_sense_context.l2_example_sentence}",
    "l1_example_translation": "${promptInputs.deck_sense_context.l1_example_translation}"
  }
}

Behavior:
- If include_analysis = false, set "analysis" to {} but still fill mnemonics and image_brief.
- All text must be in ${promptInputs.l1_language}.
`

    // Prefer structured JSON output. If unsupported, fall back to plain completion.
    let chat
    try {
      chat = await openai.chat.completions.create({
        model: 'gpt-4.1-nano',
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: userPrompt },
        ],
        temperature: 0.8,
        // Let the model return JSON; we sanitize below
      })
    } catch (e: unknown) {
      // Retry without response_format if not supported
      chat = await openai.chat.completions.create({
        model: 'gpt-4.1-nano',
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: userPrompt },
        ],
        temperature: 0.4,
      })
    }

    let textContent = chat.choices?.[0]?.message?.content || ''
    // Try to extract JSON block if any extra text sneaks in
    const fenceMatch = textContent.match(/```json[\s\S]*?```/i) || textContent.match(/```[\s\S]*?```/)
    if (fenceMatch) {
      textContent = fenceMatch[0].replace(/```json/i, '').replace(/```/g, '').trim()
    } else {
      const jsonMatch = textContent.match(/(\{[\s\S]*\})/)
      if (jsonMatch) textContent = jsonMatch[1]
    }

    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(textContent) as Record<string, unknown>
    } catch (e: unknown) {
      // Mark failed if cannot parse
      await supabase
        .from('word_ai_content')
        .update({ status: 'failed', updated_at: new Date().toISOString() })
        .eq('vocabulary_id', vocabRow.id)
        .eq('l1_language', body.l1Language)
        .eq('module_type', MODULE_TYPE)
        .eq('prompt_hash', promptHash)
      return NextResponse.json({ status: 'failed', error: 'Invalid JSON from model' }, { status: 500 })
    }

    // IMAGE: generation disabled. Keep storagePath null and skip any OpenAI image calls.
    const storagePath: string | null = null

    // Merge payload
    const payload = {
      ...parsed,
      deck_sense_context: promptInputs.deck_sense_context,
      image_asset: storagePath ? { storage_path: storagePath, width: 1024, height: 1024 } : undefined,
    }

    // Flip previous latest off FIRST to satisfy uq_word_ai_latest, then mark this one latest
    await supabase
      .from('word_ai_content')
      .update({ is_latest: false, updated_at: new Date().toISOString() })
      .eq('vocabulary_id', vocabRow.id)
      .eq('l1_language', body.l1Language)
      .eq('module_type', MODULE_TYPE)

    const { data: updatedRow, error: updErr } = await supabase
      .from('word_ai_content')
      .update({
        status: 'ready',
        payload,
        is_latest: true,
        provider: 'openai',
        model: 'gpt-4.1-nano',
        prompt_version: promptVersion,
        updated_at: new Date().toISOString(),
      })
      .eq('vocabulary_id', vocabRow.id)
      .eq('l1_language', body.l1Language)
      .eq('module_type', MODULE_TYPE)
      .eq('prompt_hash', promptHash)
      .select('id')
      .single()

    if (updErr || !updatedRow) {
      const msg = updErr?.message || ''
      const isDup = (updErr as { code?: string } | null)?.code === '23505' || msg.includes('uq_word_ai_latest') || msg.includes('duplicate key value')
      if (isDup) {
        // Another request won the race. Return the current latest row as ready.
        const { data: latestRows } = await supabase
          .from('word_ai_content')
          .select('payload')
          .eq('vocabulary_id', vocabRow.id)
          .eq('l1_language', body.l1Language)
          .eq('module_type', MODULE_TYPE)
          .eq('is_latest', true)
          .limit(1)
        if (latestRows && latestRows.length > 0) {
          return NextResponse.json({ status: 'ready', payload: (latestRows[0] as { payload: unknown }).payload })
        }
      }
      return NextResponse.json({ status: 'failed', error: updErr?.message || 'Update failed' }, { status: 500 })
    }

    // No-op: already flipped others prior to marking this one latest

    return NextResponse.json({ status: 'ready', payload })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


