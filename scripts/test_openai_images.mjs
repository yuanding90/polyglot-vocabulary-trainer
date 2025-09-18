import { config } from 'dotenv'
import OpenAI from 'openai'

// Load env from .env.local (fallback to process.env if already set)
config({ path: '.env.local' })

async function main() {
  const apiKey = process.env.OPENAI_API_KEY
  const org = process.env.OPENAI_ORG_ID
  const project = process.env.OPENAI_PROJECT

  if (!apiKey) {
    console.error('OPENAI_API_KEY missing')
    process.exit(1)
  }

  const openai = new OpenAI({ apiKey, organization: org, project })

  try {
    const res = await openai.images.generate({
      model: 'gpt-image-1',
      prompt: 'flat illustration of a book',
      size: '1024x1024',
    })
    const url = res?.data?.[0]?.url || ''
    console.log(JSON.stringify({ ok: !!url, url }))
  } catch (e) {
    const msg = e?.message || String(e)
    const status = e?.status
    console.error(JSON.stringify({ ok: false, status, error: msg }))
    process.exit(2)
  }
}

main()


