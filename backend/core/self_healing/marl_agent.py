"""Multi-Agent Reinforcement Learning (MARL) scaffold for self-healing.

This module provides:
- A lightweight multi-agent environment (`MultiAgentEnv`) used for testing and
  demonstration.
- Wrappers for different RL backends:
  - `TensorForceAgentWrapper` (if `tensorforce` is installed)
  - `MindSporeAgentWrapper` (scaffold if MindSpore RL is available)
  - `EmulatedAgent` fallback (random/heuristic agent used for CI/demo)
- `MARLTrainer` that orchestrates training or evaluation across agents.

Design goals:
- Do not require heavy dependencies to run tests or demos. Use gated imports
  and provide clear messages when a backend is unavailable.
- Provide a simple, reproducible emulated backend for CI and local testing.

To run a small demo locally (no extra deps required):

    python3 -m backend.core.self_healing.marl_agent

"""
from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try gated imports for heavy backends.
_has_tensorforce = False
_has_mindspore = False
try:
    import tensorforce
except Exception:  # pragma: no cover - defensive import
    pass
else:
    _has_tensorforce = True

try:
    import mindspore
    # mindspore-rl is not standardized; this is a placeholder for the real RL API
except Exception:  # pragma: no cover - defensive import
    pass
else:
    _has_mindspore = True


@dataclass
class StepResult:
    observations: Dict[str, List[float]]
    rewards: Dict[str, float]
    dones: Dict[str, bool]
    infos: Dict[str, dict]


class MultiAgentEnv:
    """A small, deterministic multi-agent environment for demos and tests.

    The environment contains N agents that each observe a small vector and can
    perform a discrete action (0..action_size-1). The environment rewards an
    agent if its action matches a hidden target for that agent. Targets
    randomly change occasionally. Episodes last `max_steps` steps.
    """

    def __init__(self, num_agents: int = 3, obs_size: int = 4, action_size: int = 3, max_steps: int = 50):
        self.num_agents = num_agents
        self.obs_size = obs_size
        self.action_size = action_size
        self.max_steps = max_steps
        self._step = 0
        self._targets = [random.randrange(action_size) for _ in range(num_agents)]
        self._rng = random.Random(0)

    def reset(self) -> Dict[str, List[float]]:
        self._step = 0
        self._targets = [self._rng.randrange(self.action_size) for _ in range(self.num_agents)]
        obs = {f"agent_{i}": self._make_obs(i) for i in range(self.num_agents)}
        logger.debug("Env reset -> targets=%s", self._targets)
        return obs

    def _make_obs(self, agent_idx: int) -> List[float]:
        # Simple observation: one-hot of target (soft) + step fraction
        one_hot = [0.0] * self.obs_size
        one_hot[agent_idx % self.obs_size] = 1.0
        return [float(self._targets[agent_idx] / max(1, self.action_size - 1))] + one_hot

    def step(self, actions: Dict[str, int]) -> StepResult:
        self._step += 1
        rewards = {}
        dones = {}
        infos = {}
        observations = {}
        for i in range(self.num_agents):
            aid = f"agent_{i}"
            a = int(actions.get(aid, 0))
            reward = 1.0 if a == self._targets[i] else 0.0
            rewards[aid] = reward
            dones[aid] = self._step >= self.max_steps
            observations[aid] = self._make_obs(i)
            infos[aid] = {"target": self._targets[i]}
        # Occasionally change targets to make the task non-trivial
        if self._rng.random() < 0.05:
            idx = self._rng.randrange(self.num_agents)
            self._targets[idx] = self._rng.randrange(self.action_size)
            logger.debug("Target changed for %s -> %s", idx, self._targets[idx])
        return StepResult(observations, rewards, dones, infos)


class EmulatedAgent:
    """Fallback agent used for CI and demos. Chooses actions randomly or by
    a simple heuristic (extracts "target" from the info in eval mode).
    """

    def __init__(self, agent_id: str, action_size: int, seed: Optional[int] = None):
        self.agent_id = agent_id
        self.action_size = action_size
        self._rng = random.Random(seed or 0)

    def act(self, observation: List[float], deterministic: bool = False, info: Optional[dict] = None) -> int:
        # If `info` contains a target (from env) and deterministic, use it.
        if deterministic and info and "target" in info:
            return int(info["target"])
        return self._rng.randrange(self.action_size)

    def observe(self, reward: float, terminal: bool):
        # Emulated agent doesn't learn; hook provided for compatibility.
        return

    def save(self, path: str):
        # No-op for emulated agent
        return

    def load(self, path: str):
        return


class TensorForceAgentWrapper:
    """A very small TensorForce wrapper. Only available when `tensorforce` is
    installed. This wrapper is intentionally limited so the repository doesn't
    require tensorforce at import time.

    NOTE: This is a scaffold — if you have `tensorforce` installed you can
    extend the `create_agent` method to configure a real agent.
    """

    def __init__(self, agent_id: str, observation_space_shape: Tuple[int, ...], action_size: int):
        if not _has_tensorforce:
            raise RuntimeError("TensorForce is not available in this environment")
        self.agent_id = agent_id
        self.action_size = action_size
        self.agent = None
        # Lazily create the agent so import-time side-effects are minimal
        self._create_agent(tuple(observation_space_shape))

    def _create_agent(self, obs_shape: Tuple[int, ...]):
        # Create a simple PPO agent using tensorforce's configuration API.
        # Use the `states`/`actions` arguments so we don't need a full env wrapper.
        try:
            # Preferred modern API
            from tensorforce import Agent

            states = dict(type="float", shape=obs_shape)
            actions = dict(type="int", num_actions=self.action_size)
            network = [dict(type="dense", size=64), dict(type="dense", size=32)]
            # Create a small, generic PPO agent. This may be adjusted per tensorforce version.
            self.agent = Agent.create(agent="ppo", states=states, actions=actions, network=network)
        except Exception as exc:  # pragma: no cover - guarded by import gate
            # If the API differs, fall back to a very small compatibility layer.
            raise RuntimeError("Failed to create TensorForce agent: %s" % exc)

    def act(self, observation: List[float], deterministic: bool = False, info: Optional[dict] = None) -> int:
        # TensorForce's Agent.act expects the raw observation (matching states spec)
        if self.agent is None:
            raise RuntimeError("TensorForce agent not initialized")
        try:
            # Many tensorforce versions accept deterministic flag; pass if supported
            action = self.agent.act(observation, deterministic=deterministic)
        except TypeError:
            # Older versions may not accept deterministic kwarg
            action = self.agent.act(observation)
        # Ensure we return an int action
        if isinstance(action, (list, tuple)):
            return int(action[0])
        return int(action)

    def observe(self, reward: float, terminal: bool):
        if self.agent is None:
            return
        try:
            # tensorforce Agent.observe signature varies; try the common variants
            try:
                self.agent.observe(reward=reward, terminal=terminal)
            except TypeError:
                # fallback to positional
                self.agent.observe(reward, terminal)
        except Exception:
            # Learning failures shouldn't crash the trainer; log and continue
            logger.debug("TensorForce agent observe failed", exc_info=True)

    def close(self):
        if self.agent is None:
            return
        try:
            self.agent.close()
        except Exception:
            pass


class MindSporeAgentWrapper:
    """Scaffold for MindSpore RL integration.

    Real integration requires `mindspore` and a specific RL library; this is a
    placeholder that raises a helpful error if used without the dependency.
    """

    def __init__(self, agent_id: str, observation_space_shape: Tuple[int, ...], action_size: int):
        if not _has_mindspore:
            raise RuntimeError("MindSpore is not available in this environment")
        self.agent_id = agent_id

    def act(self, observation: List[float], deterministic: bool = False, info: Optional[dict] = None) -> int:
        raise NotImplementedError("MindSpore RL wrapper is a scaffold; implement when MindSpore RL APIs are available")

    def observe(self, reward: float, terminal: bool):
        pass

    def close(self):
        pass


class MARLTrainer:
    """Orchestrates multi-agent episodes, training, and evaluation.

    Backends:
    - 'tensorforce' : uses TensorForceAgentWrapper (if available)
    - 'mindspore'   : uses MindSporeAgentWrapper (if available)
    - 'emulated'    : uses EmulatedAgent fallback
    """

    def __init__(self, env: MultiAgentEnv, backend: str = "emulated", seed: Optional[int] = None):
        self.env = env
        self.backend = backend
        self.seed = seed or 0
        self.agents: Dict[str, object] = {}
        self._init_agents()

    def _init_agents(self):
        for i in range(self.env.num_agents):
            aid = f"agent_{i}"
            if self.backend == "tensorforce":
                if not _has_tensorforce:
                    raise RuntimeError("Requested backend 'tensorforce' but tensorforce is not installed")
                self.agents[aid] = TensorForceAgentWrapper(aid, (self.env.obs_size,), self.env.action_size)
            elif self.backend == "mindspore":
                if not _has_mindspore:
                    raise RuntimeError("Requested backend 'mindspore' but MindSpore is not installed")
                self.agents[aid] = MindSporeAgentWrapper(aid, (self.env.obs_size,), self.env.action_size)
            else:
                self.agents[aid] = EmulatedAgent(aid, self.env.action_size, seed=self.seed + i)

    def run_episode(self, train: bool = True, deterministic_eval: bool = False) -> Dict[str, float]:
        obs = self.env.reset()
        total_rewards = {aid: 0.0 for aid in obs}
        done = {aid: False for aid in obs}
        steps = 0
        while not all(done.values()):
            actions = {}
            for aid, ob in obs.items():
                agent = self.agents[aid]
                info = {}  # Not exposing env info during act by default
                try:
                    a = agent.act(ob, deterministic=deterministic_eval, info=info)
                except Exception as exc:
                    logger.debug("Agent %s act raised %s; falling back to random", aid, exc)
                    a = random.randrange(self.env.action_size)
                actions[aid] = int(a)
            step_result = self.env.step(actions)
            for aid in obs:
                r = step_result.rewards[aid]
                total_rewards[aid] += r
                done[aid] = step_result.dones[aid]
                # Notify agent about reward (agents that learn can implement observe)
                try:
                    self.agents[aid].observe(r, done[aid])
                except Exception:
                    pass
            obs = step_result.observations
            steps += 1
            if steps >= self.env.max_steps:
                break
        logger.info("Episode finished: total_rewards=%s", total_rewards)
        return total_rewards

    def train(self, episodes: int = 10):
        stats = []
        for ep in range(episodes):
            logger.info("Starting episode %d/%d", ep + 1, episodes)
            r = self.run_episode(train=True, deterministic_eval=False)
            stats.append(r)
        return stats

    def evaluate(self, episodes: int = 5) -> Dict[str, float]:
        agg = {f"agent_{i}": 0.0 for i in range(self.env.num_agents)}
        for _ in range(episodes):
            r = self.run_episode(train=False, deterministic_eval=True)
            for k, v in r.items():
                agg[k] += v
        return {k: v / episodes for k, v in agg.items()}

    def submit_training_to_modelarts(self, package_path: str, job_config: dict, prefer_emulator: bool = False) -> str:
        """Submit the MARL training package to Huawei ModelArts (or emulator).

        - package_path: local path to a training package (tar/zip) or remote OBS path
        - job_config: provider-specific config dict (resource, hyperparams, etc.)
        - prefer_emulator: when True force the local emulator even if SDK exists

        Returns the provider job id (string).
        """
        try:
            from .modelarts_integration import get_modelarts_client
        except Exception:
            # If import fails, fall back to the emulator implementation directly
            from .modelarts_integration import ModelArtsEmulator  # type: ignore
            client = ModelArtsEmulator(workspace_root=os.getcwd())
            info = client.submit_training_job(package_path, job_config)
            return info.job_id

        client = get_modelarts_client(prefer_emulator=prefer_emulator, workspace_root=os.getcwd())
        info = client.submit_training_job(package_path, job_config)
        logger.info("submitted ModelArts training job %s (status=%s)", info.job_id, info.status)
        return info.job_id


if __name__ == "__main__":
    # Demo runner using the emulated backend by default.
    logging.basicConfig(level=logging.INFO)
    env = MultiAgentEnv(num_agents=4, obs_size=4, action_size=3, max_steps=30)
    trainer = MARLTrainer(env, backend="emulated", seed=42)
    logger.info("Training (demo)...")
    trainer.train(episodes=3)
    eval_results = trainer.evaluate(episodes=3)
    logger.info("Eval results: %s", eval_results)
