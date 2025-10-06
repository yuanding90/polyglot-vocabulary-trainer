'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'

interface VocabularyHeatmapData {
  frequencyRank: number
  masteryLevel: 'learning' | 'strengthening' | 'consolidating' | 'mastered' | 'leech' | 'unknown'
}

interface VocabularyHeatmapProps {
  data: VocabularyHeatmapData[]
  className?: string
}

const VocabularyHeatmap: React.FC<VocabularyHeatmapProps> = ({ data, className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 580 })

  // Color scheme based on SRS mastery levels
  const colors = {
    unknown: '#E5E7EB',     // Light grey for unseen/unknown
    learning: '#8B5CF6',    // Distinct purple for learning
    strengthening: '#EAB308', // Yellow for strengthening
    consolidating: '#3B82F6', // Blue for consolidating
    mastered: '#22C55E',    // Green for mastered
    leech: '#EF4444'        // Red for leeches
  }

  // Aggregate counts per mastery category (aligns with API progress logic)
  const counts = useMemo(() => {
    const agg = {
      unseen: 0,
      learning: 0,
      strengthening: 0,
      consolidating: 0,
      mastered: 0,
      leech: 0
    }
    for (const w of data) {
      switch (w.masteryLevel) {
        case 'learning':
          agg.learning++
          break
        case 'strengthening':
          agg.strengthening++
          break
        case 'consolidating':
          agg.consolidating++
          break
        case 'mastered':
          agg.mastered++
          break
        case 'leech':
          agg.leech++
          break
        case 'unknown':
        default:
          agg.unseen++
          break
      }
    }
    return agg
  }, [data])

  // Calculate optimal layout for dense rectangular heatmap (15,000 words)
  const calculateLayout = (containerWidth: number, containerHeight: number = 400) => {
    const padding = 0
    const availableWidth = Math.max(0, containerWidth - (padding * 2))
    
    const totalWords = data.length
    
    // Start with maximum pixel size and work down to fit all words
    const pixelSize = 4  // Fixed pixel size per word (4x4)
    const cols: number = Math.max(1, Math.floor(availableWidth / pixelSize))
    const rows: number = Math.ceil(totalWords / cols)
    
    // Compute columns so right-side whitespace is < pixelSize
    const width = cols * pixelSize
    const height = rows * pixelSize
    
    return {
      cols,
      rows,
      pixelSize,
      width,
      height,
      totalWords
    }
  }

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.clientWidth
        const containerHeight = containerRef.current.clientHeight
        setDimensions({ width: containerWidth, height: containerHeight })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Draw heatmap
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !data.length) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const layout = calculateLayout(dimensions.width, dimensions.height)
    
    // Set canvas size
    // Handle device pixel ratio to avoid blurring when scaling
    const dpr = (typeof window !== 'undefined' && window.devicePixelRatio) ? window.devicePixelRatio : 1
    canvas.width = Math.floor(layout.width * dpr)
    canvas.height = Math.floor(layout.height * dpr)
    
    // Ensure crisp, square pixels without smoothing
    // @ts-expect-error - vendor flags may exist in some browsers
    ctx.imageSmoothingEnabled = false
    // @ts-expect-error - vendor flags may exist in some browsers
    if (ctx.mozImageSmoothingEnabled !== undefined) ctx.mozImageSmoothingEnabled = false
    // @ts-expect-error - vendor flags may exist in some browsers
    if (ctx.webkitImageSmoothingEnabled !== undefined) ctx.webkitImageSmoothingEnabled = false

    ctx.save()
    ctx.scale(dpr, dpr)
    // Clear canvas
    ctx.clearRect(0, 0, layout.width, layout.height)
    
    // Sort data by frequency rank (most common first)
    const sortedData = [...data].sort((a, b) => a.frequencyRank - b.frequencyRank)
    
    // Draw each word as a pixel in the grid
    sortedData.forEach((word, index) => {
      const row = Math.floor(index / layout.cols)
      const col = index % layout.cols
      
      const x = col * layout.pixelSize
      const y = row * layout.pixelSize
      
      // Only draw if within canvas bounds
      if (x < layout.width && y < layout.height) {
        // Set color based on mastery level
        ctx.fillStyle = colors[word.masteryLevel] || colors.unknown
        ctx.fillRect(x, y, layout.pixelSize, layout.pixelSize)
      }
    })
    ctx.restore()
  }, [data, dimensions])

  if (!data.length) {
    return (
      <div className={`p-4 text-center text-gray-500 ${className}`}>
        No vocabulary data available
      </div>
    )
  }

  const layout = calculateLayout(dimensions.width, dimensions.height)

  return (
    <div className={`w-full ${className}`}>
      {/* Subtitle only; section title is rendered by the dashboard container */}
      <div className="mb-4 flex flex-col gap-2">
        <div>
          <p className="text-sm text-gray-600">The full language lexicon by frequency — colors highlight where you are in your learning journey.</p>
        </div>
        
        {/* Legend with counts */}
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.unknown }}></div>
            <span>Unseen/To be discovered ({counts.unseen.toLocaleString()})</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.learning }}></div>
            <span>Learning ({counts.learning.toLocaleString()})</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.strengthening }}></div>
            <span>Strengthening ({counts.strengthening.toLocaleString()})</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.consolidating }}></div>
            <span>Consolidating ({counts.consolidating.toLocaleString()})</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.mastered }}></div>
            <span>Mastered ({counts.mastered.toLocaleString()})</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.leech }}></div>
            <span>Leech ({counts.leech.toLocaleString()})</span>
          </div>
        </div>
      </div>

      {/* Canvas container */}
      <div 
        ref={containerRef}
        className="w-full overflow-auto border border-gray-200 rounded-lg bg-white"
      >
        <canvas
          ref={canvasRef}
          className="block"
          style={{ 
            width: `${layout.width}px`,
            height: `${layout.height}px`,
            imageRendering: 'pixelated' as any
          }}
        />
      </div>
      
      {/* Footer info removed per request */}
    </div>
  )
}

export default VocabularyHeatmap
