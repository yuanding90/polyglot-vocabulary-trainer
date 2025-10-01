"use client"
import React from 'react'

type Day = { date: string; total: number }

export function ActivityHeatmap({ series }: { series: Day[] }) {
  // Arrange into weeks (columns) and days (rows Mon-Sun)
  // Build initial map from API (assumed UTC date strings)
  const byDateRaw = new Map(series.map(d => [d.date, d.total]))
  // Use dates as provided by API; no shifting heuristics
  const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`)
  const toLocalIso = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  const byDate = byDateRaw
  const dates = series.map(d => new Date(d.date + 'T00:00:00Z'))
  if (dates.length === 0) return null

  // Build continuous set from min to max (LOCAL dates)
  // Determine desired lookback: 11 weeks mobile, 24 weeks desktop (fill empties if API shorter)
  const isMobile = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(max-width: 640px)').matches
  const desiredWeeks = isMobile ? 11 : 24
  const desiredDays = desiredWeeks * 7
  const todayLocal = new Date()
  const end = new Date(todayLocal.getFullYear(), todayLocal.getMonth(), todayLocal.getDate())
  const start = new Date(end)
  start.setDate(start.getDate() - (desiredDays - 1))
  const days: { date: string; total: number; weekday: number; }[] = []
  // Extend to end of current week (Sunday) so the grid shows a complete final week
  const endWeekday = (end.getDay() + 6) % 7 // Mon=0..Sun=6
  const daysToSunday = 6 - endWeekday
  const loopEnd = new Date(end)
  loopEnd.setDate(loopEnd.getDate() + daysToSunday)
  for (let dt = new Date(start); dt <= loopEnd; dt.setDate(dt.getDate() + 1)) {
    const iso = toLocalIso(dt)
    const total = byDate.get(iso) || 0
    // weekday: 0..6 (Mon..Sun) using getUTCDay (0=Sun). Normalize to Mon=0..Sun=6
    const sun0 = dt.getDay() // 0..6 Sun..Sat in local time
    const weekday = (sun0 + 6) % 7
    days.push({ date: iso, total, weekday })
  }

  // Group into weeks and track week start dates (Monday)
  const weeks: { date: string; total: number }[][] = []
  const weekStarts: string[] = []
  let week: { date: string; total: number }[] = Array(7).fill(null).map(() => ({ date: '', total: 0 }))
  let weekHasAny = false
  for (const d of days) {
    if (d.weekday === 0 && weekHasAny) {
      // push previous week
      weeks.push(week)
      // record start date of week (Monday is index 0)
      const startDate = week[0]?.date || ''
      weekStarts.push(startDate)
      // reset
      week = Array(7).fill(null).map(() => ({ date: '', total: 0 }))
      weekHasAny = false
    }
    week[d.weekday] = { date: d.date, total: d.total }
    weekHasAny = true
  }
  // push final week
  weeks.push(week)
  weekStarts.push(week[0]?.date || '')

  const getColor = (n: number) => {
    if (n === 0) return 'bg-gray-200'
    if (n <= 2) return 'bg-green-100'
    if (n <= 6) return 'bg-green-300'
    if (n <= 12) return 'bg-green-500'
    return 'bg-green-700'
  }

  // Month labels (top) and day labels (left)
  const monthLabelFor = (iso: string) => {
    if (!iso) return ''
    // Parse as local day to avoid UTC month drift
    const d = new Date(iso + 'T00:00:00')
    return d.toLocaleString(undefined, { month: 'short' })
  }
  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="w-full">
      <div className="overflow-x-auto pb-2">
        <div className="md:flex md:flex-col md:items-center">
          {/* Top Month Labels (aligned to grid by adding a spacer matching the day label column) */}
          <div className="flex items-center gap-2 mb-1 md:justify-center">
            {/* Spacer equal to day label column width */}
            <div className="flex-shrink-0 w-8 sm:w-10 mr-2" />
            {weeks.map((col, i) => {
              // Label months only where the week contains the 1st of a month (GitHub-style)
              const firstOfMonth = col.find(c => c.date && new Date(c.date + 'T00:00:00').getDate() === 1)
              const label = firstOfMonth
                ? monthLabelFor(firstOfMonth.date)
                : (i === 0 ? monthLabelFor(weekStarts[0]) : '')
              return (
                <div key={i} className="w-4 sm:w-5 lg:w-6 text-[10px] text-gray-500 text-center">
                  {label}
                </div>
              )
            })}
          </div>
          <div className="flex items-start gap-2 md:justify-center">
            {/* Day labels (always show; compact on mobile). Show only Mon/Wed/Fri/Sun. */}
            <div className="flex flex-col gap-1 text-[10px] text-gray-500 mr-2">
              {dayLabels.map((dl, i) => {
                const show = i === 0 || i === 2 || i === 4 || i === 6 // Mon, Wed, Fri, Sun
                return (
                  <div key={i} className="h-4 sm:h-5 lg:h-6 flex items-center">
                    {/* Mobile: single-letter labels */}
                    <span className="block sm:hidden">{show ? dl.charAt(0) : ''}</span>
                    {/* sm+: three-letter labels */}
                    <span className="hidden sm:block">{show ? dl : ''}</span>
                  </div>
                )
              })}
            </div>
            {/* Weeks */}
            <div className="flex items-start gap-2">
              {weeks.map((col, i) => (
                <div key={i} className="flex flex-col gap-1">
                  {col.map((cell, r) => (
                    <div key={r} className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 rounded-sm">
                    <div
                      className={`w-full h-full rounded-sm ${getColor(cell.total)} border border-gray-200 ${cell.date === toLocalIso(end) ? 'ring-2 ring-blue-500' : ''}`}
                        title={`${cell.date || ''}: ${cell.total} actions`}
                        aria-label={`${cell.date || ''}: ${cell.total} actions`}
                      />
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-2 text-xs text-gray-500 mt-2">
        <span>Less</span>
        <div className="w-3 h-3 rounded-sm bg-gray-200 border" />
        <div className="w-3 h-3 rounded-sm bg-green-100 border" />
        <div className="w-3 h-3 rounded-sm bg-green-300 border" />
        <div className="w-3 h-3 rounded-sm bg-green-500 border" />
        <div className="w-3 h-3 rounded-sm bg-green-700 border" />
        <span>More</span>
      </div>
    </div>
  )
}


