import React, { useEffect, useRef, useState } from 'react'
import { Mic, Square } from 'lucide-react'

interface MicRingProps {
  isRecording: boolean
  audioLevel: number // 0-1
  onStartRecording: () => void
  onStopRecording: () => void
  waveformData?: number[]
  frequency?: number
}

/**
 * MicRing Component
 * Displays live waveform visualization with recording indicator
 * - Animated mic button with active recording state
 * - Real-time frequency spectrum visualization
 * - Audio level indicator (dB-style animated ring)
 * - Recording duration timer
 */
export const MicRing: React.FC<MicRingProps> = ({
  isRecording,
  audioLevel,
  onStartRecording,
  onStopRecording,
  waveformData = [],
  frequency = 0,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [recordingTime, setRecordingTime] = useState<number>(0)

  // Timer for recording duration
  useEffect(() => {
    if (!isRecording) {
      setRecordingTime(0)
      return
    }

    const interval = setInterval(() => {
      setRecordingTime((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [isRecording])

  // Draw waveform on canvas
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const centerY = height / 2

    // Clear canvas
    ctx.fillStyle = '#0f172a'
    ctx.fillRect(0, 0, width, height)

    if (waveformData.length > 0) {
      // Draw waveform
      ctx.strokeStyle = '#0ea5e9'
      ctx.lineWidth = 2
      ctx.beginPath()

      const sliceWidth = (width * 1.0) / waveformData.length
      let x = 0

      waveformData.forEach((value, i) => {
        const y = centerY - (value / 255) * (height / 2)
        if (i === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
        x += sliceWidth
      })

      ctx.lineTo(width, centerY)
      ctx.stroke()

      // Draw center line
      ctx.strokeStyle = 'rgba(15, 23, 42, 0.5)'
      ctx.beginPath()
      ctx.moveTo(0, centerY)
      ctx.lineTo(width, centerY)
      ctx.stroke()
    } else if (isRecording) {
      // Draw animated baseline when no data
      ctx.strokeStyle = 'rgba(14, 165, 233, 0.5)'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(0, centerY)
      ctx.lineTo(width, centerY)
      ctx.stroke()
    }
  }, [waveformData, isRecording])

  // Format time as MM:SS
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Calculate audio level percentage (0-100)
  const levelPercent = Math.min(audioLevel * 100, 100)

  return (
    <div className="flex flex-col items-center gap-6 p-6 bg-gradient-to-b from-slate-800 to-slate-900 rounded-lg border border-slate-700">
      {/* Waveform Display */}
      <div className="w-full">
        <canvas
          ref={canvasRef}
          width={300}
          height={100}
          className="w-full border border-slate-700 rounded bg-slate-950"
        />
      </div>

      {/* Audio Level Ring */}
      <div className="relative w-32 h-32 flex items-center justify-center">
        {/* Background ring */}
        <svg
          className="absolute w-full h-full"
          viewBox="0 0 128 128"
          style={{ transform: 'rotate(-90deg)' }}
        >
          {/* Background circle */}
          <circle
            cx="64"
            cy="64"
            r="56"
            fill="none"
            stroke="rgba(71, 85, 105, 0.3)"
            strokeWidth="8"
          />

          {/* Audio level arc */}
          <circle
            cx="64"
            cy="64"
            r="56"
            fill="none"
            stroke={`url(#levelGradient)`}
            strokeWidth="8"
            strokeDasharray={`${(levelPercent / 100) * 351.86} 351.86`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.2s ease' }}
          />

          {/* Gradient definition */}
          <defs>
            <linearGradient id="levelGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              {levelPercent < 30 && (
                <>
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </>
              )}
              {levelPercent >= 30 && levelPercent < 60 && (
                <>
                  <stop offset="0%" stopColor="#eab308" />
                  <stop offset="100%" stopColor="#f97316" />
                </>
              )}
              {levelPercent >= 60 && levelPercent < 80 && (
                <>
                  <stop offset="0%" stopColor="#f97316" />
                  <stop offset="100%" stopColor="#ef4444" />
                </>
              )}
              {levelPercent >= 80 && (
                <>
                  <stop offset="0%" stopColor="#dc2626" />
                  <stop offset="100%" stopColor="#991b1b" />
                </>
              )}
            </linearGradient>
          </defs>
        </svg>

        {/* Center button */}
        <button
          onClick={isRecording ? onStopRecording : onStartRecording}
          className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center font-semibold text-white transition-all duration-200 ${
            isRecording
              ? 'bg-gradient-to-br from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 shadow-lg shadow-red-500/50'
              : 'bg-gradient-to-br from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg shadow-blue-500/30'
          } ${isRecording ? 'animate-pulse' : ''}`}
          title={isRecording ? 'Stop recording (Click or voice command)' : 'Start recording'}
        >
          {isRecording ? (
            <Square size={32} className="fill-white" />
          ) : (
            <Mic size={32} />
          )}
        </button>

        {/* Level percentage in center */}
        <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
          <div className="text-2xl font-bold text-white">{Math.round(levelPercent)}%</div>
          {isRecording && (
            <div className="text-xs text-gray-300 mt-1">{formatTime(recordingTime)}</div>
          )}
        </div>
      </div>

      {/* Status indicator */}
      <div className="flex items-center gap-2">
        {isRecording ? (
          <>
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-300">
              Recording {frequency && `• ${frequency} Hz`}
            </span>
          </>
        ) : (
          <>
            <div className="w-2 h-2 bg-gray-500 rounded-full" />
            <span className="text-sm text-gray-400">Ready to record</span>
          </>
        )}
      </div>

      {/* Audio level debug info */}
      <div className="w-full text-xs text-gray-500 text-center">
        <div>Audio Level: {(audioLevel * 100).toFixed(1)}%</div>
        <div>Waveform Samples: {waveformData.length}</div>
      </div>
    </div>
  )
}
