import React, { useEffect, useRef, useState } from 'react';
import { RotateCcw, Pause, Play, ZoomIn, ZoomOut, Shield } from 'lucide-react';
import { FederationNode } from '../types/xdr.types';

interface FederationRingProps {
  nodes: FederationNode[];
  selectedNodeId?: string | null;
  onNodeSelect?: (nodeId: string) => void;
  showLabels?: boolean;
  syncAnimation?: boolean;
  zoomLevel?: number;
}

/**
 * FederationRing - Canvas-based circular visualization
 * Shows federation nodes in a ring topology with trust levels, sync status, and real-time indicators
 */
const FederationRing: React.FC<FederationRingProps> = ({
  nodes,
  selectedNodeId = null,
  onNodeSelect = () => {},
  showLabels = true,
  syncAnimation = true,
  zoomLevel = 1,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [rotation, setRotation] = useState(0);
  const [isAnimating, setIsAnimating] = useState(syncAnimation);
  const [currentZoom, setCurrentZoom] = useState(zoomLevel);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const animationFrameRef = useRef<number>();

  // Canvas dimensions
  const width = 800;
  const height = 600;
  const centerX = width / 2;
  const centerY = height / 2;
  const baseRadius = 150 * currentZoom;

  // Color mapping by trust level
  const getTrustColor = (trustLevel: string): string => {
    switch (trustLevel) {
      case 'full':
        return '#10b981'; // green
      case 'partial':
        return '#f59e0b'; // amber
      case 'untrusted':
        return '#ef4444'; // red
      case 'verifying':
        return '#3b82f6'; // blue
      default:
        return '#6b7280'; // gray
    }
  };

  // Color for node status
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'online':
        return '#10b981';
      case 'offline':
        return '#ef4444';
      case 'syncing':
        return '#3b82f6';
      case 'error':
        return '#dc2626';
      case 'pending':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  // Draw a single node
  const drawNode = (
    ctx: CanvasRenderingContext2D,
    node: FederationNode,
    x: number,
    y: number,
    isSelected: boolean,
    isHovered: boolean
  ) => {
    const nodeRadius = isSelected ? 20 : 16;
    const trustColor = getTrustColor(node.trustLevel);
    const statusColor = getStatusColor(node.status);

    // Node glow/halo for selected nodes
    if (isSelected) {
      ctx.fillStyle = 'rgba(59, 130, 246, 0.2)'; // blue glow
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius + 15, 0, Math.PI * 2);
      ctx.fill();
    }

    // Node glow for hovering
    if (isHovered) {
      ctx.fillStyle = 'rgba(99, 102, 241, 0.15)'; // indigo glow
      ctx.beginPath();
      ctx.arc(x, y, nodeRadius + 10, 0, Math.PI * 2);
      ctx.fill();
    }

    // Trust level circle (outer ring)
    ctx.strokeStyle = trustColor;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Node fill
    ctx.fillStyle = statusColor;
    ctx.beginPath();
    ctx.arc(x, y, nodeRadius - 2, 0, Math.PI * 2);
    ctx.fill();

    // Status indicator (small dot at top)
    if (node.status === 'syncing') {
      ctx.fillStyle = '#3b82f6';
      ctx.beginPath();
      ctx.arc(x, y - nodeRadius - 8, 5, 0, Math.PI * 2);
      ctx.fill();

      // Pulsing animation
      const pulse = Math.sin(Date.now() / 200) * 3 + 2;
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y - nodeRadius - 8, 5 + pulse, 0, Math.PI * 2);
      ctx.stroke();
    } else if (node.status === 'online') {
      ctx.fillStyle = '#10b981';
      ctx.beginPath();
      ctx.arc(x, y - nodeRadius - 8, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Leader indicator (star)
    if (node.isLeader) {
      drawLeaderStar(ctx, x, y + nodeRadius + 8, 8);
    }
  };

  // Draw leader star indicator
  const drawLeaderStar = (ctx: CanvasRenderingContext2D, cx: number, cy: number, size: number) => {
    ctx.fillStyle = '#fbbf24'; // amber
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const angle = (i * 4 * Math.PI) / 5 - Math.PI / 2;
      const x = cx + Math.cos(angle) * size;
      const y = cy + Math.sin(angle) * size;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.closePath();
    ctx.fill();
  };

  // Draw sync time label
  const drawLabel = (ctx: CanvasRenderingContext2D, node: FederationNode, x: number, y: number) => {
    if (!showLabels) return;

    const timeDiff = Date.now() - new Date(node.lastSyncTime).getTime();
    const seconds = Math.floor(timeDiff / 1000);
    let timeLabel = '';

    if (seconds < 60) {
      timeLabel = `${seconds}s ago`;
    } else if (seconds < 3600) {
      timeLabel = `${Math.floor(seconds / 60)}m ago`;
    } else {
      timeLabel = `${Math.floor(seconds / 3600)}h ago`;
    }

    // Node name
    ctx.fillStyle = '#f3f4f6'; // light gray
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(node.nodeName.substring(0, 10), x, y + 35);

    // Sync time
    ctx.fillStyle = '#d1d5db'; // medium gray
    ctx.font = '9px sans-serif';
    ctx.fillText(timeLabel, x, y + 50);

    // Response time
    ctx.fillStyle = '#9ca3af'; // darker gray
    ctx.font = '8px sans-serif';
    ctx.fillText(`${node.responseTime}ms`, x, y + 63);
  };

  // Draw connection lines between nodes
  const drawConnections = (ctx: CanvasRenderingContext2D) => {
    if (nodes.length < 2) return;

    for (let i = 0; i < nodes.length; i++) {
      const nextIndex = (i + 1) % nodes.length;
      const angle1 = (rotation + (i / nodes.length) * Math.PI * 2) % (Math.PI * 2);
      const angle2 = (rotation + (nextIndex / nodes.length) * Math.PI * 2) % (Math.PI * 2);

      const x1 = centerX + Math.cos(angle1) * baseRadius;
      const y1 = centerY + Math.sin(angle1) * baseRadius;
      const x2 = centerX + Math.cos(angle2) * baseRadius;
      const y2 = centerY + Math.sin(angle2) * baseRadius;

      const node1 = nodes[i];
      const node2 = nodes[nextIndex];

      // Line opacity based on sync status
      const opacity = node1.syncStatus === 'completed' && node2.syncStatus === 'completed' ? 0.3 : 0.15;
      ctx.strokeStyle = `rgba(107, 114, 128, ${opacity})`;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
  };

  // Draw center circle
  const drawCenter = (ctx: CanvasRenderingContext2D) => {
    const centerRadius = 40;
    const onlineCount = nodes.filter((n) => n.status === 'online').length;
    const healthPercent = Math.round((onlineCount / nodes.length) * 100);

    // Gradient circle
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, centerRadius);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.05)');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(centerX, centerY, centerRadius, 0, Math.PI * 2);
    ctx.fill();

    // Border
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.4)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(centerX, centerY, centerRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Text: network health
    ctx.fillStyle = '#f3f4f6';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Network', centerX, centerY - 12);

    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 20px sans-serif';
    ctx.fillText(`${healthPercent}%`, centerX, centerY + 10);

    ctx.fillStyle = '#9ca3af';
    ctx.font = '10px sans-serif';
    ctx.fillText(`${onlineCount}/${nodes.length} online`, centerX, centerY + 28);
  };

  // Main draw function
  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#1f2937'; // dark bg
    ctx.fillRect(0, 0, width, height);

    // Grid background
    ctx.strokeStyle = 'rgba(107, 114, 128, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < width; i += 50) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, height);
      ctx.stroke();
    }
    for (let i = 0; i < height; i += 50) {
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(width, i);
      ctx.stroke();
    }

    // Draw inner circle
    ctx.strokeStyle = 'rgba(107, 114, 128, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Draw connections
    drawConnections(ctx);

    // Draw nodes
    nodes.forEach((node, index) => {
      const angle = (rotation + (index / nodes.length) * Math.PI * 2) % (Math.PI * 2);
      const x = centerX + Math.cos(angle) * baseRadius;
      const y = centerY + Math.sin(angle) * baseRadius;

      const isSelected = node.nodeId === selectedNodeId;
      const isHovered = node.nodeId === hoveredNodeId;

      drawNode(ctx, node, x, y, isSelected, isHovered);
      drawLabel(ctx, node, x, y);
    });

    // Draw center circle
    drawCenter(ctx);
  };

  // Animation loop
  useEffect(() => {
    const animate = () => {
      if (isAnimating) {
        setRotation((prev) => (prev + 0.005) % (Math.PI * 2));
      }
      draw();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAnimating, currentZoom, showLabels, nodes, selectedNodeId, hoveredNodeId, rotation]);

  // Mouse click handler
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if click is on a node
    nodes.forEach((node, index) => {
      const angle = (rotation + (index / nodes.length) * Math.PI * 2) % (Math.PI * 2);
      const nodeX = centerX + Math.cos(angle) * baseRadius;
      const nodeY = centerY + Math.sin(angle) * baseRadius;

      const distance = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);
      if (distance < 25) {
        onNodeSelect(node.nodeId);
      }
    });
  };

  // Mouse move handler
  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let foundNode = null;
    nodes.forEach((node, index) => {
      const angle = (rotation + (index / nodes.length) * Math.PI * 2) % (Math.PI * 2);
      const nodeX = centerX + Math.cos(angle) * baseRadius;
      const nodeY = centerY + Math.sin(angle) * baseRadius;

      const distance = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);
      if (distance < 25) {
        foundNode = node.nodeId;
      }
    });

    setHoveredNodeId(foundNode);
  };

  const handleMouseLeave = () => {
    setHoveredNodeId(null);
  };

  return (
    <div className="w-full bg-gray-900 rounded-lg border border-gray-700 p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-500" />
          Federation Ring
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setIsAnimating(!isAnimating)}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 text-gray-300 transition"
            title={isAnimating ? 'Pause rotation' : 'Resume rotation'}
          >
            {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setCurrentZoom(Math.max(0.5, currentZoom - 0.2))}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 text-gray-300 transition"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentZoom(Math.min(2, currentZoom + 0.2))}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 text-gray-300 transition"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setRotation(0)}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded border border-gray-600 text-gray-300 transition"
            title="Reset view"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleCanvasClick}
        onMouseMove={handleCanvasMouseMove}
        onMouseLeave={handleMouseLeave}
        className="w-full border border-gray-700 rounded bg-gray-900 cursor-pointer"
      />

      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-gray-300">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Online</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Offline</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span>Syncing</span>
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-green-500" />
            <span>Full Trust</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-amber-500" />
            <span>Partial Trust</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full border-2 border-red-500" />
            <span>Untrusted</span>
          </div>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNodeId && nodes.find((n) => n.nodeId === selectedNodeId) && (
        <div className="mt-4 p-3 bg-gray-800 rounded border border-blue-500 text-sm">
          {nodes.map(
            (node) =>
              node.nodeId === selectedNodeId && (
                <div key={node.nodeId} className="space-y-2">
                  <div className="font-bold text-blue-400">{node.nodeName}</div>
                  <div className="grid grid-cols-2 gap-2 text-gray-300">
                    <div>Status: {node.status}</div>
                    <div>Trust: {node.trustLevel}</div>
                    <div>Region: {node.region}</div>
                    <div>Response: {node.responseTime}ms</div>
                    <div>CPU: {node.cpuUsage}%</div>
                    <div>Memory: {node.memoryUsage}MB</div>
                    <div>Models: {node.modelsContributed}</div>
                    <div>Events: {node.eventsProcessed}</div>
                  </div>
                </div>
              )
          )}
        </div>
      )}
    </div>
  );
};

export default FederationRing;
