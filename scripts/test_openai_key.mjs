import dotenv from 'dotenv'
dotenv.config({ path: '.env.local' })

import OpenAI from 'openai'

async function main() {
  const apiKey = process.env.OPENAI_API_KEY
  const organization = process.env.OPENAI_ORG_ID
  const project = process.env.OPENAI_PROJECT

  if (!apiKey) {
    console.error('OPENAI_API_KEY missing')
    process.exit(1)
  }

  const client = new OpenAI({ apiKey, organization, project })

  try {
    // Lightweight auth check: list models
    const models = await client.models.list()
    console.log(`Auth OK. Models available: ${models.data?.length ?? 0}`)
  } catch (e) {
    console.error('Auth check failed (models.list):', e?.response?.data || e?.message || e)
    process.exit(1)
  }

  try {
    const resp = await client.chat.completions.create({
      model: 'gpt-4.1-nano',
      messages: [{ role: 'user', content: 'Reply with: OK' }],
      temperature: 0,
    })
    const text = resp.choices?.[0]?.message?.content || ''
    console.log('Chat OK:', text)
  } catch (e) {
    console.error('Chat completion failed:', e?.response?.data || e?.message || e)
    process.exit(1)
  }

  // Optional: image smoke test (commented to save cost)
  // try {
  //   const img = await client.images.generate({
  //     model: 'gpt-image-1',
  //     prompt: 'a small red dot on a white background',
  //     size: '256x256',
  //   })
  //   console.log('Image OK: received', img.data?.length || 0, 'image(s)')
  // } catch (e) {
  //   console.error('Image generation failed:', e?.response?.data || e?.message || e)
  //   process.exit(1)
  // }
}

main()


