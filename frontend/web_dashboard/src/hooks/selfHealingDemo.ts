import type { Dispatch } from 'redux';
import { v4 as uuidv4 } from 'uuid';
import {
  setAgents,
  addRewardDataPoint,
  setMetrics,
  addSnapshot,
  setWebSocketConnected,
} from '@/store/slices/selfHealingSlice';
import type { Agent, RewardDataPoint, SnapshotMetadata } from '@/types/self_healing.types';

type DemoHandle = {
  stop: () => void;
};

function randomBetween(min: number, max: number) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function startSelfHealingDemo(dispatch: Dispatch): DemoHandle {
  // Start connected
  dispatch(setWebSocketConnected(true));

  // Create initial agent lists
  const attackers: Agent[] = Array.from({ length: 6 }).map((_, i) => ({
    id: `attacker-${i}`,
    type: 'attacker',
    status: 'active',
    strategy: 'aggressive',
    x: randomBetween(5, 95),
    y: randomBetween(5, 95),
    energy: randomBetween(40, 100),
    successRate: Math.random(),
    successCount: 0,
    failureCount: 0,
    lastActionTime: new Date().toISOString(),
    rewardAccumulated: 0,
    policyVersion: 'v1.0.0',
  }));

  const defenders: Agent[] = Array.from({ length: 10 }).map((_, i) => ({
    id: `defender-${i}`,
    type: 'defender',
    status: 'active',
    strategy: 'defensive',
    x: randomBetween(5, 95),
    y: randomBetween(5, 95),
    energy: randomBetween(50, 100),
    successRate: Math.random(),
    successCount: 0,
    failureCount: 0,
    lastActionTime: new Date().toISOString(),
    rewardAccumulated: 0,
    policyVersion: 'v1.0.0',
  }));

  // push initial agents
  dispatch(
    setAgents({
      attackers,
      defenders,
      totalAgents: attackers.length + defenders.length,
      activeAgents: attackers.length + defenders.length,
      compromisedAgents: 0,
      recoveryNeeded: 0,
    })
  );

  // reward history ticker
  let tick = 0;
  const rewardInterval = setInterval(() => {
    tick += 1;
    const totalReward = Math.max(0, Math.round((Math.sin(tick / 10) + 1) * 50 + Math.random() * 10));
    const point: RewardDataPoint = {
      tick,
      timestamp: new Date().toISOString(),
      totalReward,
      defenseReward: Math.round(totalReward * (0.6 + Math.random() * 0.3)),
      attackReward: Math.round(totalReward * (0.2 + Math.random() * 0.2)),
      recoveryReward: Math.round(totalReward * (0.1 + Math.random() * 0.1)),
      efficiency: Math.round(100 * Math.random()) / 100,
      trend: totalReward > 60 ? 'improving' : totalReward > 35 ? 'stable' : 'declining',
    };
  // slice expects a generic record for reward datapoints; cast to satisfy types
  dispatch(addRewardDataPoint(point as unknown as Record<string, number | string>));

    // mutate some agents slightly
    attackers.forEach((a) => {
      a.x = Math.max(1, Math.min(99, a.x + (Math.random() - 0.5) * 8));
      a.y = Math.max(1, Math.min(99, a.y + (Math.random() - 0.5) * 8));
      a.energy = Math.max(0, a.energy - Math.random() * 2);
    });

    defenders.forEach((d) => {
      d.x = Math.max(1, Math.min(99, d.x + (Math.random() - 0.5) * 6));
      d.y = Math.max(1, Math.min(99, d.y + (Math.random() - 0.5) * 6));
      d.energy = Math.max(0, d.energy - Math.random() * 1.2);
    });

    // occasionally adjust compromised/recovered counts
    const compromised = Math.random() < 0.08 ? randomBetween(0, 2) : 0;
    const recovered = Math.random() < 0.12 ? randomBetween(0, 2) : 0;

    dispatch(
      setAgents({
        attackers,
        defenders,
        totalAgents: attackers.length + defenders.length,
        activeAgents: attackers.length + defenders.length,
        compromisedAgents: compromised,
        recoveryNeeded: recovered,
      })
    );

    // emit metrics update
    dispatch(
      setMetrics({
        currentTick: tick,
        elapsedTime: tick * 1,
        attackers: attackers.length,
        defenders: defenders.length,
        compromised,
        recovered,
        avgReward: Math.round(totalReward / (attackers.length + defenders.length) * 100) / 100,
        totalReward,
        policyVersion: 'v1.0.0',
        convergenceProgress: Math.round((Math.min(tick, 100) / 100) * 100),
      })
    );
  }, 1200);

  // snapshot generator
  const snapshotInterval = setInterval(() => {
    const snap: SnapshotMetadata = {
      id: uuidv4(),
      name: `snapshot-${Date.now()}`,
      description: 'Demo snapshot',
      createdAt: new Date().toISOString(),
      tick,
      size: randomBetween(1024, 10240),
      metrics: {
        avgReward: Math.round(Math.random() * 100),
        defenseSuccess: Math.round(Math.random() * 100),
        convergenceRate: Math.round(Math.random() * 100),
      },
      status: 'available',
      agentCount: attackers.length + defenders.length,
      policyVersion: 'v1.0.0',
      automated: false,
      retentionDays: 7,
      encryption: 'AES-256-GCM',
      location: 'local',
    };
    dispatch(addSnapshot(snap));
  }, 15000);

  function stop() {
    clearInterval(rewardInterval);
    clearInterval(snapshotInterval);
    dispatch(setWebSocketConnected(false));
  }

  return { stop };
}

export default startSelfHealingDemo;
