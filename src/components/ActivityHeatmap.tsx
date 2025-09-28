"use client"
import React from 'react'

type Day = { date: string; total: number }

export function ActivityHeatmap({ series }: { series: Day[] }) {
  // Arrange into weeks (columns) and days (rows Mon-Sun)
  const byDate = new Map(series.map(d => [d.date, d.total]))
  const dates = series.map(d => new Date(d.date + 'T00:00:00Z'))
  if (dates.length === 0) return null

  // Build continuous set from min to max
  const start = new Date(dates[0])
  const end = new Date(dates[dates.length - 1])
  const days: { date: string; total: number; weekday: number; }[] = []
  for (let dt = new Date(start); dt <= end; dt.setUTCDate(dt.getUTCDate() + 1)) {
    const iso = dt.toISOString().slice(0,10)
    const total = byDate.get(iso) || 0
    // weekday: 0..6 (Mon..Sun) using getUTCDay (0=Sun). Normalize to Mon=0..Sun=6
    const sun0 = dt.getUTCDay() // 0..6 Sun..Sat
    const weekday = (sun0 + 6) % 7
    days.push({ date: iso, total, weekday })
  }

  // Group into weeks
  const weeks: { date: string; total: number }[][] = []
  let week: { date: string; total: number }[] = Array(7).fill(null).map(() => ({ date: '', total: 0 }))
  let dayIdx = 0
  for (const d of days) {
    if (d.weekday === 0 && dayIdx !== 0) {
      weeks.push(week)
      week = Array(7).fill(null).map(() => ({ date: '', total: 0 }))
    }
    week[d.weekday] = { date: d.date, total: d.total }
    dayIdx++
  }
  weeks.push(week)

  const getColor = (n: number) => {
    if (n === 0) return 'bg-gray-200'
    if (n <= 2) return 'bg-green-100'
    if (n <= 6) return 'bg-green-300'
    if (n <= 12) return 'bg-green-500'
    return 'bg-green-700'
  }

  return (
    <div className="w-full">
      <div className="flex items-start gap-2 overflow-x-auto pb-2">
        {/* Weeks */}
        {weeks.map((col, i) => (
          <div key={i} className="flex flex-col gap-1">
            {col.map((cell, r) => (
              <div key={r} className="w-3 h-3 sm:w-3.5 sm:h-3.5 rounded-sm">
                <div
                  className={`w-full h-full rounded-sm ${getColor(cell.total)} border border-gray-200`}
                  title={`${cell.date || ''}: ${cell.total} actions`}
                  aria-label={`${cell.date || ''}: ${cell.total} actions`}
                />
              </div>
            ))}
          </div>
        ))}
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


