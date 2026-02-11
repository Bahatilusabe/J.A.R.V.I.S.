import { useState, useCallback, useMemo } from 'react'
import { Play, Pause, RotateCcw, FastForward } from 'lucide-react'

interface TimeSliderProps {
  startTime: Date
  endTime: Date
  currentTime: Date
  onTimeChange: (time: Date) => void
  isAnimating?: boolean
  onAnimationToggle?: (isAnimating: boolean) => void
  step?: number // milliseconds between steps
  speed?: 0.5 | 1 | 2 // playback speed multiplier
  onSpeedChange?: (speed: 0.5 | 1 | 2) => void
  className?: string
}

/**
 * TimeSlider Component
 *
 * Interactive timeline slider for temporal graph navigation.
 * Allows scrubbing through attack predictions over time with optional animation playback.
 * Features date display, speed controls, and keyboard shortcuts.
 */
export default function TimeSlider({
  startTime,
  endTime,
  currentTime,
  onTimeChange,
  isAnimating = false,
  onAnimationToggle,
  step = 3600000, // 1 hour default
  speed = 1,
  onSpeedChange,
  className = '',
}: TimeSliderProps) {
  const [localSpeed, setLocalSpeed] = useState<0.5 | 1 | 2>(speed)

  // Calculate percentage position on slider
  const percentage = useMemo(() => {
    const totalMs = endTime.getTime() - startTime.getTime()
    const currentMs = currentTime.getTime() - startTime.getTime()
    return Math.min(100, Math.max(0, (currentMs / totalMs) * 100))
  }, [startTime, endTime, currentTime])

  // Format time display
  const formatTime = (date: Date): string => {
    return date.toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  // Handle slider input
  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const totalMs = endTime.getTime() - startTime.getTime()
      const newMs = (parseFloat(e.target.value) / 100) * totalMs
      onTimeChange(new Date(startTime.getTime() + newMs))
    },
    [startTime, endTime, onTimeChange]
  )

  // Handle playback toggle
  const handlePlayPause = useCallback(() => {
    onAnimationToggle?.(!isAnimating)
  }, [isAnimating, onAnimationToggle])

  // Handle speed change
  const handleSpeedChange = useCallback((newSpeed: 0.5 | 1 | 2) => {
    setLocalSpeed(newSpeed)
    onSpeedChange?.(newSpeed)
  }, [onSpeedChange])

  // Handle reset
  const handleReset = useCallback(() => {
    onTimeChange(startTime)
  }, [startTime, onTimeChange])

  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case ' ':
          e.preventDefault()
          handlePlayPause()
          break
        case 'ArrowRight':
          onTimeChange(new Date(currentTime.getTime() + step * localSpeed))
          break
        case 'ArrowLeft':
          onTimeChange(new Date(Math.max(startTime.getTime(), currentTime.getTime() - step * localSpeed)))
          break
        case '0':
          handleReset()
          break
        default:
          break
      }
    },
    [currentTime, startTime, step, localSpeed, handlePlayPause, handleReset, onTimeChange]
  )

  return (
    <div className={`w-full space-y-4 rounded-lg bg-slate-800 p-4 border border-slate-700 ${className}`}>
      {/* Header with title and time display */}
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold text-cyan-400">Timeline Navigation</div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <div className="flex gap-2">
            <span className="text-gray-500">Start:</span>
            <span className="font-mono text-gray-300">{formatTime(startTime)}</span>
          </div>
          <div className="w-px h-4 bg-slate-700" />
          <div className="flex gap-2">
            <span className="text-cyan-400 font-semibold">{formatTime(currentTime)}</span>
          </div>
          <div className="w-px h-4 bg-slate-700" />
          <div className="flex gap-2">
            <span className="text-gray-500">End:</span>
            <span className="font-mono text-gray-300">{formatTime(endTime)}</span>
          </div>
        </div>
      </div>

      {/* Slider track */}
      <div className="relative pt-2">
        {/* Time markers */}
        <div className="absolute top-0 left-0 right-0 flex justify-between px-1 text-xs text-gray-600 pointer-events-none">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>

        {/* Slider input */}
        <input
          type="range"
          min="0"
          max="100"
          value={percentage}
          onChange={handleSliderChange}
          onKeyDown={handleKeyDown}
          title="Drag to seek through time (arrow keys: ←→, space: play/pause, 0: reset)"
          className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />

        {/* Progress indicator */}
        { }
        <div
          className="absolute top-2 left-0 h-2 bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-lg pointer-events-none transition-all duration-100"
          style={{ width: `${percentage}%` } as React.CSSProperties}
        />
      </div>

      {/* Controls row */}
      <div className="flex items-center justify-between">
        {/* Playback controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            title="Reset to start (Press 0)"
            className="p-2 hover:bg-slate-700 rounded transition-colors"
          >
            <RotateCcw size={16} className="text-gray-400 hover:text-cyan-400" />
          </button>
          <button
            onClick={handlePlayPause}
            title={isAnimating ? 'Pause (Press Space)' : 'Play (Press Space)'}
            className="p-2 hover:bg-slate-700 rounded transition-colors"
          >
            {isAnimating ? (
              <Pause size={18} className="text-green-400" />
            ) : (
              <Play size={18} className="text-gray-400 hover:text-cyan-400" />
            )}
          </button>

          {/* Speed selector */}
          <div className="flex items-center gap-1 ml-2 pl-2 border-l border-slate-700">
            {[0.5, 1, 2].map((s) => (
              <button
                key={s}
                onClick={() => handleSpeedChange(s as 0.5 | 1 | 2)}
                className={`px-2 py-1 text-xs font-mono rounded transition-colors ${
                  localSpeed === s
                    ? 'bg-cyan-600 text-white'
                    : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Legend and info */}
        <div className="flex items-center gap-3 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <FastForward size={12} />
            <span>Keyboard: Space=play, ←→=seek, 0=reset</span>
          </div>
        </div>
      </div>

      {/* Time step indicator */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-700 text-xs text-gray-500">
        <span>Step: {(step / 1000 / 60).toFixed(0)}min</span>
        <span>Progress: {percentage.toFixed(1)}%</span>
      </div>
    </div>
  )
}
