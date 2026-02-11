/// <reference types="vite/client" />

import { useState, useMemo } from 'react'
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'
import type { CausalGraph as CausalGraphType, CausalNode } from '../types/ced.types'

export interface CausalGraphProps {
  graph: CausalGraphType
  onNodeClick?: (nodeId: string) => void
  className?: string
  highlightedNodes?: string[]
  highlightedEdges?: Array<{ source: string; target: string }>
}

/**
 * CausalGraph Component
 *
 * Visualizes causal chains (A→B→C) showing how attack steps propagate.
 * Uses SVG with hierarchical layout for interactive node selection and highlighting.
 * Color-coded by severity level with zoom and pan controls.
 */
export function CausalGraphComponent({
  graph,
  onNodeClick,
  className = '',
  highlightedNodes = [],
  highlightedEdges = [],
}: CausalGraphProps) {
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Calculate node positions using hierarchical layout
  const nodePositions = useMemo(() => {
    const positions: Record<string, { x: number; y: number }> = {}

    // Topological sort to determine layers
    const inDegree: Record<string, number> = {}
    const layers: string[][] = []

    graph.nodes.forEach((n) => {
      inDegree[n.id] = 0
    })

    graph.edges.forEach((e) => {
      inDegree[e.target] = (inDegree[e.target] || 0) + 1
    })

    // BFS to assign layers
    const queue: string[] = graph.nodes.filter((n) => inDegree[n.id] === 0).map((n) => n.id)
    const visited = new Set<string>()

    while (queue.length > 0) {
      const layer: string[] = []
      const nextQueue: string[] = []

      for (const nodeId of queue) {
        if (!visited.has(nodeId)) {
          visited.add(nodeId)
          layer.push(nodeId)

          graph.edges.forEach((e) => {
            if (e.source === nodeId) {
              inDegree[e.target]--
              if (inDegree[e.target] === 0 && !visited.has(e.target)) {
                nextQueue.push(e.target)
              }
            }
          })
        }
      }

      if (layer.length > 0) {
        layers.push(layer)
      }
      queue.length = 0
      queue.push(...nextQueue)
    }

    // Assign positions based on layers
    const layerHeight = 120
    const nodeSpacing = 150

    layers.forEach((layer, layerIndex) => {
      const totalWidth = (layer.length - 1) * nodeSpacing
      const startX = -totalWidth / 2

      layer.forEach((nodeId, nodeIndex) => {
        positions[nodeId] = {
          x: startX + nodeIndex * nodeSpacing,
          y: layerIndex * layerHeight,
        }
      })
    })

    return positions
  }, [graph])

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleZoom = (factor: number) => {
    setZoom((prev) => Math.max(0.1, Math.min(3, prev * factor)))
  }

  const handleReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedNode(null)
  }

  // SVG dimensions
  const svgWidth = 800
  const svgHeight = 600
  const centerX = svgWidth / 2
  const centerY = svgHeight / 2

  const isEdgeHighlighted = (source: string, target: string) => {
    return highlightedEdges.some((e) => e.source === source && e.target === target)
  }

  const nodeColor = (node: CausalNode) => {
    const severityColors: Record<string, string> = {
      critical: '#dc2626',
      high: '#ea580c',
      medium: '#eab308',
      low: '#3b82f6',
    }
    return severityColors[node.severity] || '#6b7280'
  }

  return (
    <div className={`flex flex-col h-full bg-white rounded-lg border border-slate-200 ${className}`}>
      {/* Controls */}
      <div className="flex items-center gap-2 p-4 border-b border-slate-200 bg-slate-50">
        <button
          onClick={() => handleZoom(1.2)}
          className="p-2 hover:bg-white rounded transition-colors"
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4 text-slate-600" />
        </button>
        <button
          onClick={() => handleZoom(0.8)}
          className="p-2 hover:bg-white rounded transition-colors"
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4 text-slate-600" />
        </button>
        <div className="flex-1" />
        <span className="text-xs text-slate-500">{Math.round(zoom * 100)}%</span>
        <button
          onClick={handleReset}
          className="p-2 hover:bg-white rounded transition-colors"
          title="Reset view"
        >
          <RotateCcw className="w-4 h-4 text-slate-600" />
        </button>
      </div>

  {/* Graph container */}
  <div className="relative flex-1 overflow-hidden bg-gradient-to-br from-slate-50 to-slate-100">
        <svg
          width={svgWidth}
          height={svgHeight}
          className="w-full h-full"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#6b7280" />
            </marker>
            <marker
              id="arrowhead-highlight"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
            </marker>
          </defs>

          <g transform={`translate(${centerX + pan.x}, ${centerY + pan.y}) scale(${zoom})`}>
            {/* Edges */}
            {graph.edges.map((edge) => {
              const sourcePos = nodePositions[edge.source]
              const targetPos = nodePositions[edge.target]

              if (!sourcePos || !targetPos) return null

              const isHighlighted = isEdgeHighlighted(edge.source, edge.target)

              return (
                <g key={`${edge.source}-${edge.target}`}>
                  <line
                    x1={sourcePos.x}
                    y1={sourcePos.y}
                    x2={targetPos.x}
                    y2={targetPos.y}
                    stroke={isHighlighted ? '#3b82f6' : '#cbd5e1'}
                    strokeWidth={isHighlighted ? 3 : 2}
                    opacity={isHighlighted ? 1 : 0.6}
                    markerEnd={isHighlighted ? 'url(#arrowhead-highlight)' : 'url(#arrowhead)'}
                  />
                  {/* Edge label */}
                  <text
                    x={(sourcePos.x + targetPos.x) / 2}
                    y={(sourcePos.y + targetPos.y) / 2 - 8}
                    fontSize="11"
                    fill="#64748b"
                    textAnchor="middle"
                    opacity={0.7}
                  >
                    {edge.type}
                  </text>
                </g>
              )
            })}

            {/* Nodes */}
            {graph.nodes.map((node) => {
              const pos = nodePositions[node.id]
              if (!pos) return null

              const isHighlighted = highlightedNodes.includes(node.id)
              const isSelected = selectedNode === node.id

              return (
                <g key={node.id}>
                  {/* Node circle */}
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isSelected ? 32 : 28}
                    fill={nodeColor(node)}
                    stroke={isHighlighted ? '#3b82f6' : isSelected ? '#1e40af' : 'white'}
                    strokeWidth={isHighlighted || isSelected ? 3 : 2}
                    opacity={0.9}
                    className="cursor-pointer transition-all"
                    onClick={() => {
                      setSelectedNode(node.id)
                      onNodeClick?.(node.id)
                    }}
                  />

                  {/* Node label */}
                  <text
                    x={pos.x}
                    y={pos.y}
                    fontSize="12"
                    fill="white"
                    fontWeight="bold"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    pointerEvents="none"
                  >
                    {node.label.slice(0, 3)}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white p-3 rounded border border-slate-200 shadow-sm text-xs">
          <div className="font-semibold text-slate-700 mb-2">Severity</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#dc2626' }} />
              <span className="text-slate-600">Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ea580c' }} />
              <span className="text-slate-600">High</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#eab308' }} />
              <span className="text-slate-600">Medium</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }} />
              <span className="text-slate-600">Low</span>
            </div>
          </div>
        </div>
      </div>

      {/* Selected node details */}
      {selectedNode && graph.nodes.find((n) => n.id === selectedNode) && (
        <div className="p-4 border-t border-slate-200 bg-slate-50">
          {(() => {
            const node = graph.nodes.find((n) => n.id === selectedNode)!
            return (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-slate-900">{node.label}</h4>
                  <span className="text-xs font-medium px-2 py-1 rounded" style={{
                    backgroundColor: nodeColor(node) + '20',
                    color: nodeColor(node),
                  }}>
                    {Math.round(node.probability * 100)}%
                  </span>
                </div>
                <p className="text-sm text-slate-600">{node.description}</p>
                {node.indicators && node.indicators.length > 0 && (
                  <div className="text-xs">
                    <span className="font-medium text-slate-700">Indicators:</span>
                    <div className="text-slate-600">{node.indicators.join(', ')}</div>
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}

export default CausalGraphComponent
