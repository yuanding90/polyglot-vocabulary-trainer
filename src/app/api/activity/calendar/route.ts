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

function formatDateUtc(d: Date) {
  return d.toISOString().slice(0, 10)
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const userId = searchParams.get('userId') || ''
    const fromStr = searchParams.get('from') || ''
    const toStr = searchParams.get('to') || ''

    if (!userId || !fromStr || !toStr) {
      return NextResponse.json({ error: 'userId, from, to are required' }, { status: 400 })
    }

    const supabase = getAdminSupabase()

    const { data, error } = await supabase
      .from('daily_summary')
      .select('date, review_count, discovery_count')
      .eq('user_id', userId)
      .gte('date', fromStr)
      .lte('date', toStr)

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    const fromDate = new Date(fromStr + 'T00:00:00.000Z')
    const toDate = new Date(toStr + 'T00:00:00.000Z')
    const byDate = new Map<string, { review: number; discovery: number }>()
    for (const row of data || []) {
      const r = (row as any).review_count || 0
      const d = (row as any).discovery_count || 0
      byDate.set((row as any).date, { review: r, discovery: d })
    }

    const series: { date: string; total: number; review: number; discovery: number }[] = []
    for (let dt = new Date(fromDate); dt <= toDate; dt.setUTCDate(dt.getUTCDate() + 1)) {
      const key = formatDateUtc(dt)
      const counts = byDate.get(key) || { review: 0, discovery: 0 }
      series.push({ date: key, total: counts.review + counts.discovery, review: counts.review, discovery: counts.discovery })
    }

    return NextResponse.json({ series })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


