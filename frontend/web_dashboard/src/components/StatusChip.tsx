import { useMemo } from 'react'
import { SystemMode } from '../services/system-status.service'

interface StatusChipProps {
  mode: SystemMode
  threatLevel?: 'critical' | 'high' | 'medium' | 'low' | 'none'
  animated?: boolean
  className?: string
  onClick?: () => void
}

/**
 * Global Status Chip Component
 * Displays current system operational mode with visual feedback
 * Modes: Conscious, Predictive, Self-Healing, Under Attack
 */
export function StatusChip({
  mode,
  threatLevel = 'none',
  animated = true,
  className = '',
  onClick,
}: StatusChipProps) {
  const { bgColor, textColor, borderColor, icon, label, pulse } = useMemo(() => {
    // Critical threat overrides mode display
    if (threatLevel === 'critical') {
      return {
        bgColor: 'bg-red-900/30',
        textColor: 'text-red-400',
        borderColor: 'border-red-500/50',
        icon: '⚠️',
        label: 'CRITICAL',
        pulse: true,
      }
    }

    switch (mode) {
      case 'conscious':
        return {
          bgColor: 'bg-blue-900/30',
          textColor: 'text-blue-400',
          borderColor: 'border-blue-500/50',
          icon: '🧠',
          label: 'Conscious',
          pulse: false,
        }
      case 'predictive':
        return {
          bgColor: 'bg-cyan-900/30',
          textColor: 'text-cyan-400',
          borderColor: 'border-cyan-500/50',
          icon: '🔮',
          label: 'Predictive',
          pulse: animated,
        }
      case 'self_healing':
        return {
          bgColor: 'bg-green-900/30',
          textColor: 'text-green-400',
          borderColor: 'border-green-500/50',
          icon: '🔄',
          label: 'Self-Healing',
          pulse: animated,
        }
      case 'under_attack':
        return {
          bgColor: 'bg-orange-900/30',
          textColor: 'text-orange-400',
          borderColor: 'border-orange-500/50',
          icon: '🛡️',
          label: 'Under Attack',
          pulse: true,
        }
      default:
        return {
          bgColor: 'bg-gray-900/30',
          textColor: 'text-gray-400',
          borderColor: 'border-gray-500/50',
          icon: '○',
          label: 'Unknown',
          pulse: false,
        }
    }
  }, [mode, threatLevel, animated])

  const animationClass = pulse && animated ? 'animate-pulse' : ''

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${bgColor} ${textColor} ${borderColor} ${animationClass} hover:opacity-80 transition-opacity ${className}`}
      title={`System Status: ${label} (Threat: ${threatLevel})`}
    >
      <span className="text-sm font-semibold">{icon}</span>
      <span className="text-xs font-medium tracking-wider">{label.toUpperCase()}</span>
      {pulse && (
        <span className={`ml-1 w-2 h-2 rounded-full ${textColor.replace('text-', 'bg-')} ${animationClass}`} />
      )}
    </button>
  )
}

export default StatusChip
