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
  // yyyy-mm-dd
  return d.toISOString().slice(0, 10)
}

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url)
    const userId = searchParams.get('userId') || ''
    const daysParam = searchParams.get('days')
    const days = Math.max(1, Math.min(365, Number(daysParam) || 30))

    if (!userId) {
      return NextResponse.json({ error: 'userId is required' }, { status: 400 })
    }

    const supabase = getAdminSupabase()

    const today = new Date()
    const toDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()))
    const fromDate = new Date(toDate)
    fromDate.setUTCDate(fromDate.getUTCDate() - (days - 1))

    const fromStr = formatDateUtc(fromDate)
    const toStr = formatDateUtc(toDate)

    const { data, error } = await supabase
      .from('daily_summary')
      .select('date, reviews_done, new_words_learned')
      .eq('user_id', userId)
      .gte('date', fromStr)
      .lte('date', toStr)

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Build dense series map
    const byDate = new Map<string, { review: number; discovery: number }>()
    for (const row of data || []) {
      const r = (row as any).reviews_done || 0
      const d = (row as any).new_words_learned || 0
      byDate.set((row as any).date, { review: r, discovery: d })
    }

    const series: { date: string; total: number; review: number; discovery: number }[] = []
    let last7 = 0
    let last30 = 0
    let todayTotal = 0

    for (let i = 0; i < days; i++) {
      const cur = new Date(fromDate)
      cur.setUTCDate(fromDate.getUTCDate() + i)
      const key = formatDateUtc(cur)
      const counts = byDate.get(key) || { review: 0, discovery: 0 }
      const total = counts.review + counts.discovery
      series.push({ date: key, total, review: counts.review, discovery: counts.discovery })
      if (i >= days - 7) last7 += total
      last30 += total
      if (key === formatDateUtc(toDate)) todayTotal = total
    }

    // Compute streak (consecutive days with total > 0 ending at today)
    let streak = 0
    for (let i = series.length - 1; i >= 0; i--) {
      if (series[i].total > 0) streak++
      else break
    }

    return NextResponse.json({
      today: todayTotal,
      last7Days: last7,
      last30Days: last30,
      streak,
      series,
    })
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : 'Unexpected error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}


