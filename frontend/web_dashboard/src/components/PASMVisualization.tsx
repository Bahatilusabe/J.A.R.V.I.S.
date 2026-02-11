import { useEffect, useRef } from 'react'

export interface AttackChain {
  id?: string
  nodes: string[]
  probability?: number
  label?: string
}

interface PASMVisualizationProps {
  chains: AttackChain[]
  className?: string
}

export default function PASMVisualization({ chains, className = '' }: PASMVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Resize canvas to match display size
    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = Math.max(canvas.offsetHeight || 0, 300)
    }
    resize()

    let animationFrameId = 0
    let time = 0

    const draw = () => {
      // subtle trailing background for motion
      ctx.fillStyle = 'rgba(2,6,23, 0.04)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      const centerX = canvas.width / 2
      const centerY = canvas.height / 2
      const maxRadius = Math.min(canvas.width, canvas.height) / 2.5

      chains.forEach((chain, idx) => {
        const angle = (idx / Math.max(chains.length, 1)) * Math.PI * 2
        const nodeCount = Math.max(chain.nodes.length, 1)

        // Path stroke
        ctx.strokeStyle = `hsl(${180 + idx * 28}, 85%, ${50 + Math.sin(time * 0.02) * 8}%)`
        ctx.lineWidth = 2
        ctx.globalAlpha = 0.7
        ctx.beginPath()

        for (let i = 0; i < nodeCount; i++) {
          const r = (maxRadius * i) / Math.max(nodeCount - 1, 1)
          const x = centerX + Math.cos(angle) * r
          const y = centerY + Math.sin(angle) * r

          if (i === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }

        ctx.stroke()
        ctx.globalAlpha = 1

        // Nodes
        for (let i = 0; i < nodeCount; i++) {
          const r = (maxRadius * i) / Math.max(nodeCount - 1, 1)
          const x = centerX + Math.cos(angle) * r
          const y = centerY + Math.sin(angle) * r

          const nodeRadius = 6
          // glow
          ctx.fillStyle = `hsla(${180 + idx * 28}, 85%, ${55 + Math.sin(time * 0.03 + i) * 10}%, 0.28)`
          ctx.beginPath()
          ctx.arc(x, y, nodeRadius * 3, 0, Math.PI * 2)
          ctx.fill()

          // core
          ctx.fillStyle = `hsl(${180 + idx * 28}, 85%, 60%)`
          ctx.beginPath()
          ctx.arc(x, y, nodeRadius, 0, Math.PI * 2)
          ctx.fill()
        }

        // Probability label
        ctx.fillStyle = `hsl(${180 + idx * 28}, 85%, 70%)`
        ctx.font = "11px monospace"
        ctx.globalAlpha = 0.9
        const labelX = centerX + Math.cos(angle) * (maxRadius + 26)
        const labelY = centerY + Math.sin(angle) * (maxRadius + 26)
        ctx.fillText(`${Math.round((chain.probability || 0) * 100)}%`, labelX, labelY)
      })

      // center label
      ctx.fillStyle = 'rgba(0,232,255,0.85)'
      ctx.font = "bold 14px sans-serif"
      ctx.textAlign = 'center'
      ctx.fillText('PASM Graph', canvas.width / 2, canvas.height / 2 + 6)

      time++
      animationFrameId = requestAnimationFrame(draw)
    }

    draw()

    const onResize = () => resize()
    window.addEventListener('resize', onResize)

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', onResize)
    }
  }, [chains])

  return (
    <div className={`bg-slate-800 p-3 rounded-lg ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-semibold text-cyan-400">Temporal Attack Graph (PASM)</div>
        <div className="text-xs text-slate-400">Real-time predictions</div>
      </div>
  <canvas ref={canvasRef} className="w-full rounded-md border border-slate-700 min-h-[300px]" />
    </div>
  )
}
