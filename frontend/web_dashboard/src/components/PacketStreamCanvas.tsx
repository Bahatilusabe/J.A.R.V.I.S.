import React, { useEffect, useRef, useCallback } from 'react'
import { AlertTriangle, Zap } from 'lucide-react'
import { Particle, PacketStreamData } from '../types/tds.types'

interface PacketStreamCanvasProps {
  packets: PacketStreamData[]
  blockingRate: number
  anomalyRate: number
  isActive: boolean
  onPacketClick?: (packet: PacketStreamData) => void
}

export const PacketStreamCanvas: React.FC<PacketStreamCanvasProps> = ({
  packets,
  blockingRate,
  anomalyRate,
  isActive,
  onPacketClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const srcClustersRef = useRef<Map<string, { x: number; y: number; count: number }>>(new Map())
  const dstClustersRef = useRef<Map<string, { x: number; y: number; count: number }>>(new Map())
  const animationIdRef = useRef<number>()

  // Risk color mapping: 0 = green, 0.5 = yellow, 1 = red
  const getRiskColor = (riskScore: number): [number, number, number, number] => {
    const clamped = Math.max(0, Math.min(1, riskScore))

    if (clamped < 0.3) {
      // Green zone
      const ratio = clamped / 0.3
      return [0, 255 * (1 - ratio * 0.5), 0, 200]
    } else if (clamped < 0.7) {
      // Yellow zone
      const ratio = (clamped - 0.3) / 0.4
      return [255, 200 - ratio * 100, 0, 220]
    } else {
      // Red zone
      const ratio = (clamped - 0.7) / 0.3
      return [255, 50 * (1 - ratio), 0, 240]
    }
  }

  // Initialize clusters from packet sources/destinations
  const updateClusters = useCallback(() => {
    srcClustersRef.current.clear()
    dstClustersRef.current.clear()

    packets.forEach((packet) => {
      const srcHash = hashIp(packet.source)
      const dstHash = hashIp(packet.destination)

      // Distribute sources on left side
      if (!srcClustersRef.current.has(packet.source)) {
        srcClustersRef.current.set(packet.source, {
          x: 100 + Math.sin(srcHash) * 150,
          y: 100 + Math.cos(srcHash * 1.3) * 200,
          count: 0,
        })
      }
      const srcCluster = srcClustersRef.current.get(packet.source)!
      srcCluster.count++

      // Distribute destinations on right side
      if (!dstClustersRef.current.has(packet.destination)) {
        dstClustersRef.current.set(packet.destination, {
          x: 900 + Math.sin(dstHash) * 150,
          y: 100 + Math.cos(dstHash * 1.3) * 200,
          count: 0,
        })
      }
      const dstCluster = dstClustersRef.current.get(packet.destination)!
      dstCluster.count++
    })
  }, [packets])

  // Create particles from new packets
  const createParticles = useCallback(() => {
    packets.slice(-10).forEach((packet) => {
      const srcCluster = srcClustersRef.current.get(packet.source)
      const dstCluster = dstClustersRef.current.get(packet.destination)

      if (srcCluster && dstCluster) {
        const startX = srcCluster.x + (Math.random() - 0.5) * 40
        const startY = srcCluster.y + (Math.random() - 0.5) * 40
        const endX = dstCluster.x + (Math.random() - 0.5) * 40
        const endY = dstCluster.y + (Math.random() - 0.5) * 40

        const dx = endX - startX
        const dy = endY - startY
        const distance = Math.sqrt(dx * dx + dy * dy)
        const velocity = distance / 30 // Reach destination in 30 frames

        const color = getRiskColor(packet.riskScore)

        particlesRef.current.push({
          id: packet.packetId,
          x: startX,
          y: startY,
          vx: (dx / distance) * velocity,
          vy: (dy / distance) * velocity,
          size: 3 + packet.riskScore * 2,
          color,
          lifespan: 40,
          maxLifespan: 40,
          riskScore: packet.riskScore,
        })
      }
    })
  }, [packets])

  // Update and render particles
  const updateParticles = useCallback(() => {
    // Remove dead particles
    particlesRef.current = particlesRef.current.filter((p) => p.lifespan > 0)

    // Update particle positions and lifespans
    particlesRef.current.forEach((particle) => {
      particle.x += particle.vx
      particle.y += particle.vy
      particle.lifespan--

      // Fade out in last 10 frames
      if (particle.lifespan < 10) {
        particle.color[3] = (particle.color[3] * particle.lifespan) / 10
      }
    })
  }, [])

  // Draw canvas
  const draw = useCallback(
    (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => {
      // Clear canvas with dark background
      ctx.fillStyle = 'rgba(17, 24, 39, 0.95)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw grid
      ctx.strokeStyle = 'rgba(75, 85, 99, 0.2)'
      ctx.lineWidth = 1
      for (let i = 0; i < canvas.width; i += 100) {
        ctx.beginPath()
        ctx.moveTo(i, 0)
        ctx.lineTo(i, canvas.height)
        ctx.stroke()
      }
      for (let i = 0; i < canvas.height; i += 100) {
        ctx.beginPath()
        ctx.moveTo(0, i)
        ctx.lineTo(canvas.width, i)
        ctx.stroke()
      }

      // Draw source clusters (left side)
      srcClustersRef.current.forEach((cluster, ip) => {
        ctx.fillStyle = 'rgba(59, 130, 246, 0.3)'
        ctx.beginPath()
        ctx.arc(cluster.x, cluster.y, 50, 0, Math.PI * 2)
        ctx.fill()

        // Cluster label
        ctx.fillStyle = 'rgba(100, 150, 255, 0.8)'
        ctx.font = '11px monospace'
        ctx.textAlign = 'center'
        ctx.fillText(ip.substring(0, 8), cluster.x, cluster.y - 65)
        ctx.fillText(`(${cluster.count})`, cluster.x, cluster.y - 53)

        // Center point
        ctx.fillStyle = 'rgba(100, 150, 255, 1)'
        ctx.beginPath()
        ctx.arc(cluster.x, cluster.y, 3, 0, Math.PI * 2)
        ctx.fill()
      })

      // Draw destination clusters (right side)
      dstClustersRef.current.forEach((cluster, ip) => {
        ctx.fillStyle = 'rgba(168, 85, 247, 0.3)'
        ctx.beginPath()
        ctx.arc(cluster.x, cluster.y, 50, 0, Math.PI * 2)
        ctx.fill()

        // Cluster label
        ctx.fillStyle = 'rgba(200, 120, 255, 0.8)'
        ctx.font = '11px monospace'
        ctx.textAlign = 'center'
        ctx.fillText(ip.substring(0, 8), cluster.x, cluster.y - 65)
        ctx.fillText(`(${cluster.count})`, cluster.x, cluster.y - 53)

        // Center point
        ctx.fillStyle = 'rgba(200, 120, 255, 1)'
        ctx.beginPath()
        ctx.arc(cluster.x, cluster.y, 3, 0, Math.PI * 2)
        ctx.fill()
      })

      // Draw particles
      particlesRef.current.forEach((particle) => {
        const [r, g, b, a] = particle.color
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a / 255})`
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
        ctx.fill()

        // Glow effect for high-risk packets
        if (particle.riskScore > 0.7) {
          ctx.strokeStyle = `rgba(255, 100, 0, ${(a / 255) * 0.5})`
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.arc(particle.x, particle.y, particle.size + 3, 0, Math.PI * 2)
          ctx.stroke()
        }
      })

      // Draw stats panel (top right)
      const statsX = canvas.width - 200
      const statsY = 10

      ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
      ctx.fillRect(statsX, statsY, 190, 90)
      ctx.strokeStyle = 'rgba(100, 150, 255, 0.5)'
      ctx.lineWidth = 1
      ctx.strokeRect(statsX, statsY, 190, 90)

      ctx.fillStyle = 'rgba(200, 220, 255, 0.9)'
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText('Packet Stream', statsX + 8, statsY + 18)

      ctx.font = '11px monospace'
      ctx.fillStyle = 'rgba(150, 180, 255, 0.8)'
      ctx.fillText(`Packets: ${packets.length}`, statsX + 8, statsY + 35)
      ctx.fillText(`Active: ${particlesRef.current.length}`, statsX + 8, statsY + 48)

      // Blocking rate
      ctx.fillText('Blocking Rate:', statsX + 8, statsY + 63)
      ctx.fillStyle = blockingRate > 0.1 ? 'rgba(255, 100, 0, 0.9)' : 'rgba(100, 255, 100, 0.9)'
      ctx.fillText(`${(blockingRate * 100).toFixed(1)}%`, statsX + 95, statsY + 63)

      // Anomaly rate
      ctx.fillStyle = 'rgba(150, 180, 255, 0.8)'
      ctx.fillText('Anomaly Rate:', statsX + 8, statsY + 77)
      ctx.fillStyle = anomalyRate > 0.05 ? 'rgba(255, 200, 0, 0.9)' : 'rgba(100, 255, 100, 0.9)'
      ctx.fillText(`${(anomalyRate * 100).toFixed(1)}%`, statsX + 95, statsY + 77)
    },
    [packets, blockingRate, anomalyRate]
  )

  // Animation loop
  const animate = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      animationIdRef.current = requestAnimationFrame(animate)
      return
    }

    const ctx = canvas.getContext('2d')
    if (!ctx) {
      animationIdRef.current = requestAnimationFrame(animate)
      return
    }

    updateParticles()
    draw(canvas, ctx)

    animationIdRef.current = requestAnimationFrame(animate)
  }, [updateParticles, draw])

  // Initialize canvas and start animation
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    updateClusters()
    createParticles()
    animate()

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current)
      }
    }
  }, [updateClusters, createParticles, animate])

  // Update clusters and create particles when packets change
  useEffect(() => {
    if (isActive) {
      updateClusters()
      createParticles()
    }
  }, [packets, isActive, updateClusters, createParticles])

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onPacketClick) return

    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const clickX = event.clientX - rect.left
    const clickY = event.clientY - rect.top

    // Find particle near click
    const clickedParticle = particlesRef.current.find((p) => {
      const dist = Math.sqrt((p.x - clickX) ** 2 + (p.y - clickY) ** 2)
      return dist < p.size + 5
    })

    if (clickedParticle) {
      // Find corresponding packet
      const packet = packets.find((p) => p.packetId === clickedParticle.id)
      if (packet) {
        onPacketClick(packet)
      }
    }
  }

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg overflow-hidden border border-blue-500/20">
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        className="w-full h-full cursor-crosshair block"
      />

      {/* Status indicators overlay */}
      <div className="absolute top-4 left-4 space-y-2">
        {blockingRate > 0.1 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-500/20 border border-orange-500/50 rounded text-orange-300 text-xs font-medium">
            <AlertTriangle size={14} />
            High Block Rate
          </div>
        )}

        {anomalyRate > 0.05 && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/20 border border-yellow-500/50 rounded text-yellow-300 text-xs font-medium">
            <Zap size={14} />
            Anomalies Detected
          </div>
        )}

        {!isActive && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-600/40 border border-slate-500/50 rounded text-slate-300 text-xs font-medium">
            Streaming Paused
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex gap-4 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
          <span>Safe</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          <span>Suspicious</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <span>Malicious</span>
        </div>
      </div>
    </div>
  )
}

// Helper: Hash IP address to deterministic number
function hashIp(ip: string): number {
  return ip.split('.').reduce((hash, octet) => {
    return ((hash << 5) - hash + parseInt(octet, 10)) | 0
  }, 0)
}
