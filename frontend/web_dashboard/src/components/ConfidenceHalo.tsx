import { useMemo } from 'react'

interface ConfidenceHaloProps {
  confidence: number       // 0-1 scale
  risk: number            // 0-1 scale
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  label?: string
  className?: string
}

/**
 * ConfidenceHalo Component
 *
 * Visual indicator for model prediction confidence using concentric rings.
 * Inner rings represent high confidence (saturated colors), outer rings represent low confidence (faded).
 * Color intensity reflects risk level (bright red for high risk, pale green for low risk).
 *
 * Used in PASM graph nodes to show uncertainty in attack predictions.
 */
export default function ConfidenceHalo({
  confidence,
  risk,
  size = 'md',
  animated = true,
  label,
  className = '',
}: ConfidenceHaloProps) {
  // Determine base size dimensions
  const sizeMap = {
    sm: { container: 'w-12 h-12', ring: 4, gap: 1 },
    md: { container: 'w-16 h-16', ring: 5, gap: 2 },
    lg: { container: 'w-24 h-24', ring: 6, gap: 2 },
  }

  const dims = sizeMap[size]

  // Color based on risk level
  const getRiskColor = useMemo((): string => {
    if (risk > 0.75) return 'border-red-600'        // Critical
    if (risk > 0.5) return 'border-orange-600'      // High
    if (risk > 0.25) return 'border-yellow-600'     // Medium
    return 'border-green-600'                        // Low
  }, [risk])

  // Generate ring elements
  const rings = useMemo(() => {
    const maxRings = dims.ring
    return Array.from({ length: maxRings }).map((_, i) => {
      const baseOpacity = 0.9 - (i / maxRings) * 0.6 // 0.9 to 0.3
      const opacity = baseOpacity * confidence
      const scale = 1 - (i / maxRings) * 0.7 // 1.0 to 0.3
      const delay = i * 100 // Stagger animation

      return (
         
        <div
          key={i}
          className={`absolute inset-0 rounded-full border-2 ${getRiskColor} transition-opacity duration-500 ${
            animated ? 'animate-pulse' : ''
          }`}
          style={{
            opacity: Math.max(0.1, opacity),
            transform: `scale(${scale})`,
            animationDelay: animated ? `${delay}ms` : '0ms',
          } as React.CSSProperties}
        />
      )
    })
  }, [dims.ring, confidence, getRiskColor, animated])

  // Core center indicator
  const coreColor = useMemo(() => {
    if (risk > 0.75) return 'bg-red-600'
    if (risk > 0.5) return 'bg-orange-600'
    if (risk > 0.25) return 'bg-yellow-600'
    return 'bg-green-600'
  }, [risk])

  return (
    <div className={`${className}`}>
      {/* Halo container */}
      <div className={`relative ${dims.container} mx-auto`}>
        {/* Rings */}
        {rings}

        {/* Center core */}
        { }
        <div
          className={`absolute inset-0 flex items-center justify-center rounded-full ${coreColor} shadow-lg transition-all duration-300`}
          style={{
            opacity: Math.max(0.6, confidence * 0.9),
          } as React.CSSProperties}
        >
          {/* Inner glow */}
          <div className="absolute inset-1 rounded-full bg-white/10 blur-sm" />

          {/* Percentage text (only for md/lg sizes) */}
          {size !== 'sm' && (
            <div className="relative z-10 text-center">
              <div className="text-xs font-bold text-white">
                {Math.round(confidence * 100)}%
              </div>
              <div className="text-[0.65rem] text-gray-200">conf</div>
            </div>
          )}
        </div>
      </div>

      {/* Label below (optional) */}
      {label && (
        <div className="mt-2 text-center text-sm font-medium text-gray-300">
          {label}
        </div>
      )}

      {/* Tooltip info */}
      <div className="mt-2 text-center text-xs text-gray-400">
        <span className="inline-block px-2 py-1 rounded bg-slate-800 border border-slate-700">
          {Math.round(confidence * 100)}% confidence · {Math.round(risk * 100)}% risk
        </span>
      </div>
    </div>
  )
}
