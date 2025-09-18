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

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const path = searchParams.get('path') || ''
    const expires = Number(searchParams.get('expires') || '3600') // default 1h
    if (!path) return NextResponse.json({ url: null })

    const supabase = getAdminSupabase()
    const { data, error } = await supabase
      .storage
      .from('ai_tutor_images')
      .createSignedUrl(path, expires)

    if (error) return NextResponse.json({ url: null })
    return NextResponse.json({ url: data?.signedUrl || null })
  } catch {
    return NextResponse.json({ url: null })
  }
}


