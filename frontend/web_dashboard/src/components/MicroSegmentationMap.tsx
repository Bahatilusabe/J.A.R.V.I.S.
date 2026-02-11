import React, { useRef, useEffect, useState, useCallback } from 'react'
import { Lock, Unlock } from 'lucide-react'
import { MicroSegmentNode, TrafficFlow, SegmentationZone } from '../types/tds.types'

interface MicroSegmentationMapProps {
  nodes: MicroSegmentNode[]
  flows: TrafficFlow[]
  zones: SegmentationZone[]
  onSelectNode?: (node: MicroSegmentNode) => void
  onIsolateEndpoint?: (nodeId: string) => void
}

export const MicroSegmentationMap: React.FC<MicroSegmentationMapProps> = ({
  nodes,
  flows,
  zones,
  onSelectNode,
  onIsolateEndpoint,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [selectedNode, setSelectedNode] = useState<MicroSegmentNode | null>(null)
  const [animationFrame, setAnimationFrame] = useState<number>()

  // Trust level color mapping
  const getTrustColor = (level: string): string => {
    switch (level) {
      case 'high':
        return 'rgb(34, 197, 94)' // Green
      case 'medium':
        return 'rgb(234, 179, 8)' // Yellow
      case 'low':
        return 'rgb(249, 115, 22)' // Orange
      case 'untrusted':
        return 'rgb(239, 68, 68)' // Red
      default:
        return 'rgb(100, 116, 139)' // Slate
    }
  }

  const getNodeRadius = (node: MicroSegmentNode): number => {
    switch (node.type) {
      case 'server':
        return 20
      case 'gateway':
        return 25
      case 'database':
        return 18
      case 'iot':
        return 14
      case 'external':
        return 20
      default:
        return 16
    }
  }

  // Auto-layout nodes in zones
  const layoutNodes = useCallback(() => {
    const zoneMap = new Map<string, MicroSegmentNode[]>()
    nodes.forEach((node) => {
      if (!zoneMap.has(node.zone)) {
        zoneMap.set(node.zone, [])
      }
      zoneMap.get(node.zone)!.push(node)
    })

    const positioned = [...nodes]
    let yOffset = 60

    zoneMap.forEach((zoneNodes, _zoneId) => {
      const xStart = 80
      const xStep = 150
      zoneNodes.forEach((node, index) => {
        node.position = {
          x: xStart + index * xStep,
          y: yOffset,
        }
      })
      yOffset += 140
    })

    return positioned
  }, [nodes])

  // Draw canvas
  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const positionedNodes = layoutNodes()

    // Clear canvas
    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw grid
    ctx.strokeStyle = 'rgba(75, 85, 99, 0.1)'
    ctx.lineWidth = 1
    for (let i = 0; i < canvas.width; i += 50) {
      ctx.beginPath()
      ctx.moveTo(i, 0)
      ctx.lineTo(i, canvas.height)
      ctx.stroke()
    }

    // Draw zones as colored regions
    const zoneMap = new Map<string, MicroSegmentNode[]>()
    positionedNodes.forEach((node) => {
      if (!zoneMap.has(node.zone)) {
        zoneMap.set(node.zone, [])
      }
      zoneMap.get(node.zone)!.push(node)
    })

    let zoneY = 50
    zoneMap.forEach((zoneNodes, zoneId) => {
      const zone = zones.find((z) => z.zoneId === zoneId)
      if (!zone) return

      const zoneColor = getTrustColor(zone.trustLevel)
      ctx.fillStyle = zoneColor + '20'
      ctx.strokeStyle = zoneColor + '60'
      ctx.lineWidth = 2

      const zoneHeight = 120
      ctx.strokeRect(40, zoneY, canvas.width - 80, zoneHeight)

      // Zone label
      ctx.fillStyle = zoneColor
      ctx.font = 'bold 12px sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(zone.name, 50, zoneY + 20)
      ctx.font = '10px sans-serif'
      ctx.fillStyle = 'rgba(200, 200, 200, 0.7)'
      ctx.fillText(`${zoneNodes.length} nodes`, 50, zoneY + 35)

      zoneY += 140
    })

    // Draw flows (connections between nodes)
    flows.forEach((flow) => {
      const srcNode = positionedNodes.find((n) => n.nodeId === flow.source)
      const dstNode = positionedNodes.find((n) => n.nodeId === flow.destination)

      if (srcNode?.position && dstNode?.position) {
        const isAllowed = flow.isAllowed && !flow.isBlocked

        ctx.strokeStyle = isAllowed
          ? `rgba(100, 200, 100, ${0.3 + flow.riskScore * 0.4})`
          : 'rgba(255, 100, 100, 0.7)'
        ctx.lineWidth = 1 + flow.packetsPerSec * 0.01

        // Dashed for blocked
        if (flow.isBlocked) {
          ctx.setLineDash([5, 5])
        }

        ctx.beginPath()
        ctx.moveTo(srcNode.position.x, srcNode.position.y)
        ctx.lineTo(dstNode.position.x, dstNode.position.y)
        ctx.stroke()
        ctx.setLineDash([])

        // Arrow for direction
        const angle = Math.atan2(
          dstNode.position.y - srcNode.position.y,
          dstNode.position.x - srcNode.position.x
        )
        const arrowX = srcNode.position.x + (dstNode.position.x - srcNode.position.x) * 0.6
        const arrowY = srcNode.position.y + (dstNode.position.y - srcNode.position.y) * 0.6

        ctx.fillStyle = flow.isBlocked ? 'rgba(255, 100, 100, 0.8)' : 'rgba(100, 200, 100, 0.6)'
        ctx.save()
        ctx.translate(arrowX, arrowY)
        ctx.rotate(angle)
        ctx.fillRect(0, -3, 8, 6)
        ctx.restore()
      }
    })

    // Draw nodes
    positionedNodes.forEach((node) => {
      if (!node.position) return

      const radius = getNodeRadius(node)
      const trustColor = getTrustColor(node.trustLevel)

      // Shadow
      ctx.fillStyle = 'rgba(0, 0, 0, 0.3)'
      ctx.beginPath()
      ctx.arc(node.position.x + 2, node.position.y + 2, radius + 2, 0, Math.PI * 2)
      ctx.fill()

      // Node circle
      ctx.fillStyle = trustColor
      ctx.beginPath()
      ctx.arc(node.position.x, node.position.y, radius, 0, Math.PI * 2)
      ctx.fill()

      // Border
      ctx.strokeStyle = trustColor
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.arc(node.position.x, node.position.y, radius, 0, Math.PI * 2)
      ctx.stroke()

      // Isolation indicator
      if (node.isIsolated) {
        ctx.strokeStyle = 'rgba(255, 100, 100, 0.9)'
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.arc(node.position.x, node.position.y, radius + 8, 0, Math.PI * 2)
        ctx.stroke()
      }

      // Threat indicator
      if (node.threatIndicators.length > 0) {
        ctx.fillStyle = 'rgba(255, 200, 0, 0.9)'
        ctx.fillRect(node.position.x + radius - 6, node.position.y - radius + 2, 12, 12)
        ctx.fillStyle = '#000'
        ctx.font = 'bold 8px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText('!', node.position.x + radius, node.position.y - radius + 8)
      }

      // Label
      ctx.fillStyle = '#fff'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(node.name.substring(0, 12), node.position.x, node.position.y + radius + 8)
    })

    // Stats panel
    const statsX = 10
    const statsY = 10

    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
    ctx.fillRect(statsX, statsY, 200, 100)
    ctx.strokeStyle = 'rgba(100, 150, 255, 0.5)'
    ctx.lineWidth = 1
    ctx.strokeRect(statsX, statsY, 200, 100)

    ctx.fillStyle = 'rgba(200, 220, 255, 0.9)'
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'left'
    ctx.fillText('Network Topology', statsX + 10, statsY + 12)

    ctx.font = '10px monospace'
    ctx.fillStyle = 'rgba(150, 180, 255, 0.8)'
    ctx.fillText(`Nodes: ${nodes.length}`, statsX + 10, statsY + 30)
    ctx.fillText(`Flows: ${flows.length}`, statsX + 10, statsY + 43)
    ctx.fillText(`Blocked: ${flows.filter((f) => f.isBlocked).length}`, statsX + 10, statsY + 56)
    ctx.fillText(
      `Isolated: ${nodes.filter((n) => n.isIsolated).length}`,
      statsX + 10,
      statsY + 69
    )
    ctx.fillText(
      `Threats: ${nodes.filter((n) => n.threatIndicators.length > 0).length}`,
      statsX + 10,
      statsY + 82
    )
  }, [layoutNodes, flows, zones, nodes])

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    const animate = () => {
      draw()
      setAnimationFrame(requestAnimationFrame(animate))
    }

    animate()

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame)
      }
    }
  }, [nodes, flows, zones, animationFrame, draw])

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const clickX = event.clientX - rect.left
    const clickY = event.clientY - rect.top

    // Find clicked node
    const positionedNodes = layoutNodes()
    for (const node of positionedNodes) {
      if (!node.position) continue

      const radius = getNodeRadius(node)
      const dist = Math.sqrt((node.position.x - clickX) ** 2 + (node.position.y - clickY) ** 2)

      if (dist <= radius + 5) {
        setSelectedNode(node)
        onSelectNode?.(node)
        break
      }
    }
  }

  return (
    <div className="relative w-full h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-green-500/20 flex flex-col">
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        className="w-full h-full cursor-pointer block"
      />

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-slate-900/80 border border-slate-700 rounded p-3 text-xs text-slate-300">
        <div className="font-semibold mb-2 text-white">Trust Levels</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span>Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500" />
            <span>Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Untrusted</span>
          </div>
        </div>
      </div>

      {/* Selected node details */}
      {selectedNode && (
        <div className="absolute top-4 right-4 bg-slate-900/90 border border-blue-500/50 rounded p-4 w-80 text-sm">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-white">{selectedNode.name}</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 text-slate-300">
            <div className="flex justify-between">
              <span>Type:</span>
              <span className="text-white">{selectedNode.type}</span>
            </div>
            <div className="flex justify-between">
              <span>IP:</span>
              <span className="text-white font-mono">{selectedNode.ipAddress}</span>
            </div>
            <div className="flex justify-between">
              <span>Zone:</span>
              <span className="text-white">{selectedNode.zone}</span>
            </div>
            <div className="flex justify-between">
              <span>Trust:</span>
              <span className="text-white capitalize">{selectedNode.trustLevel}</span>
            </div>
            <div className="flex justify-between">
              <span>Status:</span>
              <span className="text-white flex items-center gap-1">
                {selectedNode.isIsolated ? (
                  <>
                    <Lock size={14} className="text-red-400" />
                    Isolated
                  </>
                ) : (
                  <>
                    <Unlock size={14} className="text-green-400" />
                    Connected
                  </>
                )}
              </span>
            </div>

            <div className="pt-3 border-t border-slate-700 flex gap-2">
              {!selectedNode.isIsolated && (
                <button
                  onClick={() => onIsolateEndpoint?.(selectedNode.nodeId)}
                  className="flex-1 px-3 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-300 rounded text-xs font-medium transition"
                >
                  Isolate
                </button>
              )}
              <button
                onClick={() => setSelectedNode(null)}
                className="flex-1 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
