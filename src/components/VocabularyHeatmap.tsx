'use client'

import React, { useEffect, useRef, useState } from 'react'

interface VocabularyHeatmapData {
  wordId: number
  word: string
  frequencyRank: number
  masteryLevel: 'new' | 'learning' | 'reviewing' | 'mastered' | 'graduated' | 'leech' | 'unknown'
  confidenceScore: number
  lastReviewed?: string
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
    unknown: '#E5E7EB',    // Light grey for new/unknown
    new: '#E5E7EB',        // Light grey for new words
    learning: '#F97316',   // Orange for learning (short intervals)
    reviewing: '#EAB308',  // Yellow for reviewing (medium intervals)
    mastered: '#22C55E',   // Green for mastered (long intervals)
    graduated: '#3B82F6',  // Blue for graduated (very long intervals)
    leech: '#EF4444'       // Red for leeches
  }

  // Calculate optimal layout for dense rectangular heatmap (15,000 words)
  const calculateLayout = (containerWidth: number, containerHeight: number = 400) => {
    const padding = 10  // Reduced padding for more space
    const availableWidth = containerWidth - (padding * 2)
    const availableHeight = containerHeight - (padding * 2)
    
    const totalWords = data.length
    
    // Start with maximum pixel size and work down to fit all words
    let pixelSize = 8  // Maximum pixel size
    let cols, rows
    
    // Find the largest pixel size that fits all words in available space
    do {
      cols = Math.floor(availableWidth / pixelSize)
      rows = Math.ceil(totalWords / cols)
      
      // Check if this fits in available height
      if (rows * pixelSize <= availableHeight) {
        break
      }
      
      pixelSize--
    } while (pixelSize > 1)
    
    // Ensure minimum pixel size for visibility
    pixelSize = Math.max(pixelSize, 1)
    
    // Recalculate with final pixel size
    cols = Math.floor(availableWidth / pixelSize)
    rows = Math.ceil(totalWords / cols)
    
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
    canvas.width = layout.width
    canvas.height = layout.height
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
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
  }, [data, dimensions])

  if (!data.length) {
    return (
      <div className={`p-4 text-center text-gray-500 ${className}`}>
        No vocabulary data available
      </div>
    )
  }

  const layout = calculateLayout(dimensions.width, dimensions.height)
  const totalWords = data.length
  const masteredWords = data.filter(w => w.masteryLevel === 'mastered' || w.masteryLevel === 'graduated').length
  const masteryPercentage = Math.round((masteredWords / totalWords) * 100)

  return (
    <div className={`w-full ${className}`}>
      {/* Header with stats */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">French Vocabulary Mastery</h3>
          <p className="text-sm text-gray-600">
            {masteredWords.toLocaleString()} of {totalWords.toLocaleString()} words mastered ({masteryPercentage}%)
          </p>
        </div>
        
        {/* Legend */}
        <div className="flex flex-wrap gap-3 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.unknown }}></div>
            <span>Unknown</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.learning }}></div>
            <span>Learning</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.reviewing }}></div>
            <span>Reviewing</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.mastered }}></div>
            <span>Mastered</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.graduated }}></div>
            <span>Graduated</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: colors.leech }}></div>
            <span>Leech</span>
          </div>
        </div>
      </div>

      {/* Canvas container */}
      <div 
        ref={containerRef}
        className="w-full overflow-auto border border-gray-200 rounded-lg bg-white"
        style={{ height: '600px' }}
      >
        <canvas
          ref={canvasRef}
          className="block"
          style={{ 
            width: `${Math.min(layout.width, dimensions.width - 40)}px`,
            height: `${layout.height}px`
          }}
        />
      </div>
      
      {/* Grid info */}
      <div className="mt-2 flex justify-between text-xs text-gray-500">
        <span>Grid: {layout.cols} × {layout.rows}</span>
        <span>{layout.totalWords} words</span>
        <span>Pixel: {layout.pixelSize}px</span>
      </div>
      
      {/* Frequency indicator */}
      <div className="mt-1 flex justify-between text-xs text-gray-400">
        <span>Most Common (Top-Left)</span>
        <span>→</span>
        <span>Least Common (Bottom-Right)</span>
      </div>
    </div>
  )
}

export default VocabularyHeatmap
