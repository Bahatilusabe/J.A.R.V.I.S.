import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX } from 'lucide-react';
import type { Agent, AgentMap, SimulationMetrics } from '@/types/self_healing.types';

interface SimulationCanvasProps {
  agents: AgentMap;
  metrics: SimulationMetrics;
  isRunning: boolean;
  onPlayPause: (playing: boolean) => void;
  onReset: () => void;
  selectedAgentId?: string;
  onAgentSelect: (agentId: string) => void;
}

interface CanvasState {
  rotation: number;
  zoom: number;
  panX: number;
  panY: number;
  rewardPulses: Array<{ x: number; y: number; intensity: number; timestamp: number }>;
}

export const SimulationCanvas: React.FC<SimulationCanvasProps> = ({
  agents,
  metrics,
  isRunning,
  onPlayPause,
  onReset,
  selectedAgentId,
  onAgentSelect,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, setState] = useState<CanvasState>({
    rotation: 0,
    zoom: 1,
    panX: 0,
    panY: 0,
    rewardPulses: [],
  });
  const [soundEnabled, setSoundEnabled] = useState(false);
  const animationFrameRef = useRef<number>();

  // Canvas dimensions
  const CANVAS_WIDTH = 800;
  const CANVAS_HEIGHT = 600;
  const GRID_SIZE = 50;

  // Agent rendering
  const getAgentColor = (agent: Agent): string => {
    if (agent.status === 'compromised') return '#ef4444'; // red
    if (agent.status === 'recovering') return '#f59e0b'; // amber
    if (agent.status === 'disabled') return '#6b7280'; // gray
    
    if (agent.type === 'attacker') {
      return agent.strategy === 'aggressive' ? '#dc2626' : '#f97316';
    } else {
      return agent.strategy === 'aggressive' ? '#10b981' : '#0ea5e9';
    }
  };

  // Draw grid
  const drawGrid = (ctx: CanvasRenderingContext2D) => {
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 0.5;

    for (let x = 0; x <= CANVAS_WIDTH; x += GRID_SIZE * state.zoom) {
      ctx.beginPath();
      ctx.moveTo(x + state.panX, 0);
      ctx.lineTo(x + state.panX, CANVAS_HEIGHT);
      ctx.stroke();
    }

    for (let y = 0; y <= CANVAS_HEIGHT; y += GRID_SIZE * state.zoom) {
      ctx.beginPath();
      ctx.moveTo(0, y + state.panY);
      ctx.lineTo(CANVAS_WIDTH, y + state.panY);
      ctx.stroke();
    }
  };

  // Draw agent
  const drawAgent = (ctx: CanvasRenderingContext2D, agent: Agent) => {
    const x = agent.x * state.zoom + state.panX;
    const y = agent.y * state.zoom + state.panY;
    const radius = agent.type === 'attacker' ? 8 : 10;

    // Agent circle
    ctx.fillStyle = getAgentColor(agent);
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Selection indicator
    if (agent.id === selectedAgentId) {
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Energy indicator (arc)
    const energyAngle = (agent.energy / 100) * Math.PI * 2;
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, radius + 2, 0, energyAngle);
    ctx.stroke();

    // Status indicator
    if (agent.status === 'recovering') {
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.arc(x, y, radius + 6, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Target line
    if (agent.targetId) {
      const targetAgent = [...agents.attackers, ...agents.defenders].find(
        (a) => a.id === agent.targetId
      );
      if (targetAgent) {
        const targetX = targetAgent.x * state.zoom + state.panX;
        const targetY = targetAgent.y * state.zoom + state.panY;
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(targetX, targetY);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  };

  // Draw reward pulses
  const drawRewardPulses = (ctx: CanvasRenderingContext2D) => {
    const now = Date.now();
    const newPulses: CanvasState['rewardPulses'] = [];

    for (const pulse of state.rewardPulses) {
      const age = now - pulse.timestamp;
      if (age < 1000) {
        const opacity = 1 - age / 1000;
        const radius = (age / 1000) * 30;

        ctx.strokeStyle = `rgba(34, 197, 94, ${opacity * 0.6})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(pulse.x, pulse.y, radius, 0, Math.PI * 2);
        ctx.stroke();

        newPulses.push(pulse);
      }
    }

    setState((prev) => ({ ...prev, rewardPulses: newPulses }));
  };

  // Canvas animation loop
  const draw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    // Draw grid
    drawGrid(ctx);

    // Draw agents
    [...agents.attackers, ...agents.defenders].forEach((agent) => {
      drawAgent(ctx, agent);
    });

    // Draw reward pulses
    drawRewardPulses(ctx);

    // Rotation animation
    if (isRunning) {
      setState((prev) => ({
        ...prev,
        rotation: (prev.rotation + 0.02) % (Math.PI * 2),
      }));
    }

    animationFrameRef.current = requestAnimationFrame(draw);
  };

  useEffect(() => {
    draw();
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agents, state, selectedAgentId, isRunning]);

  // Handle canvas click
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = (e.clientX - rect.left - state.panX) / state.zoom;
    const clickY = (e.clientY - rect.top - state.panY) / state.zoom;

    // Find clicked agent
    for (const agent of [...agents.attackers, ...agents.defenders]) {
      const dist = Math.sqrt((agent.x - clickX) ** 2 + (agent.y - clickY) ** 2);
      if (dist < 12) {
        onAgentSelect(agent.id);
        return;
      }
    }

    // Trigger reward pulse
    setState((prev) => ({
      ...prev,
      rewardPulses: [
        ...prev.rewardPulses,
        {
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
          intensity: metrics.avgReward,
          timestamp: Date.now(),
        },
      ],
    }));
  };

  // Handle zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setState((prev) => ({
      ...prev,
      zoom: Math.max(0.5, Math.min(3, prev.zoom * delta)),
    }));
  };

  return (
    <div className="flex flex-col gap-3 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">
            Agent Simulation (Tick: {metrics.currentTick})
          </h3>
          <p className="text-xs text-gray-600">
            Attackers: {metrics.attackers} | Defenders: {metrics.defenders} | Compromised:{' '}
            {metrics.compromised}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition"
            title={soundEnabled ? 'Mute' : 'Unmute'}
          >
            {soundEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
          </button>

          <button
            onClick={() => onPlayPause(!isRunning)}
            className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition"
            title={isRunning ? 'Pause' : 'Play'}
          >
            {isRunning ? <Pause size={18} /> : <Play size={18} />}
          </button>

          <button
            onClick={onReset}
            className="p-1.5 text-gray-600 hover:bg-gray-200 rounded transition"
            title="Reset"
          >
            <RotateCcw size={18} />
          </button>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        onClick={handleCanvasClick}
        onWheel={handleWheel}
        className="border border-gray-300 rounded bg-white cursor-crosshair"
      />

      <div className="grid grid-cols-4 gap-2 text-xs">
        <div className="p-2 bg-red-50 rounded border border-red-200">
          <div className="font-semibold text-red-900">{metrics.attackers}</div>
          <div className="text-red-700">Attackers</div>
        </div>
        <div className="p-2 bg-blue-50 rounded border border-blue-200">
          <div className="font-semibold text-blue-900">{metrics.defenders}</div>
          <div className="text-blue-700">Defenders</div>
        </div>
        <div className="p-2 bg-orange-50 rounded border border-orange-200">
          <div className="font-semibold text-orange-900">{metrics.compromised}</div>
          <div className="text-orange-700">Compromised</div>
        </div>
        <div className="p-2 bg-green-50 rounded border border-green-200">
          <div className="font-semibold text-green-900">{metrics.recovered}</div>
          <div className="text-green-700">Recovered</div>
        </div>
      </div>
    </div>
  );
};
