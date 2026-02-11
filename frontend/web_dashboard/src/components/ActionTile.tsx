import React, { useState } from 'react'

export type ActionTileVariant = 'neutral' | 'active' | 'disabled' | 'confirm' | 'success' | 'error'

interface ActionTileProps {
  title: string
  description: string
  icon: React.ReactNode
  variant?: ActionTileVariant
  onClick?: () => void
  onConfirm?: () => Promise<void>
  isLoading?: boolean
  badge?: string
  badgeColor?: string
  className?: string
}

/**
 * Action Tile Component
 * Renders interactive action buttons with multiple states
 * Supports confirmation modals and async operations
 */
export const ActionTile: React.FC<ActionTileProps> = ({
  title,
  description,
  icon,
  variant = 'neutral',
  onClick,
  onConfirm,
  isLoading = false,
  badge,
  badgeColor = 'bg-blue-600',
  className = '',
}) => {
  const [showConfirm, setShowConfirm] = useState(false)
  const [confirming, setConfirming] = useState(false)

  const handleClick = () => {
    if (onConfirm) {
      setShowConfirm(true)
    } else if (onClick) {
      onClick()
    }
  }

  const handleConfirm = async () => {
    if (onConfirm) {
      setConfirming(true)
      try {
        await onConfirm()
        setShowConfirm(false)
      } finally {
        setConfirming(false)
      }
    }
  }

  // Determine styling based on variant
  const variantStyles = {
    neutral: 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-100',
    active: 'bg-blue-900/50 hover:bg-blue-800/50 border-blue-500 text-blue-100',
    disabled: 'bg-slate-900 border-slate-700 text-slate-500 cursor-not-allowed',
    confirm: 'bg-yellow-900/50 hover:bg-yellow-800/50 border-yellow-500 text-yellow-100',
    success: 'bg-green-900/50 hover:bg-green-800/50 border-green-500 text-green-100',
    error: 'bg-red-900/50 hover:bg-red-800/50 border-red-500 text-red-100',
  }

  const isDisabled = variant === 'disabled' || isLoading

  return (
    <>
      <button
        onClick={handleClick}
        disabled={isDisabled}
        className={`relative p-4 rounded-lg border transition-all duration-200 ${variantStyles[variant]} ${
          isDisabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        } ${className}`}
      >
        {/* Badge */}
        {badge && (
          <div
            className={`absolute top-2 right-2 ${badgeColor} text-white text-xs font-bold px-2 py-1 rounded-full`}
          >
            {badge}
          </div>
        )}

        {/* Icon */}
        <div className="text-2xl mb-2 opacity-80">{icon}</div>

        {/* Content */}
        <div className="text-left">
          <h3 className="font-semibold text-sm mb-1">{title}</h3>
          <p className="text-xs opacity-70 line-clamp-2">{description}</p>
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <div className="absolute bottom-2 right-2">
            <div className="animate-spin">
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
            </div>
          </div>
        )}
      </button>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 rounded-lg">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm mx-4 shadow-2xl">
            <h2 className="text-lg font-bold text-slate-100 mb-2">Confirm Action</h2>
            <p className="text-slate-300 mb-6">{description}</p>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                disabled={confirming}
                className="px-4 py-2 rounded border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={confirming}
                className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 flex items-center gap-2 transition-all"
              >
                {confirming && (
                  <div className="animate-spin">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  </div>
                )}
                {confirming ? 'Processing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
