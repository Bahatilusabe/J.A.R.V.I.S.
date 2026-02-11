import pytest


def test_tensorforce_wrapper_smoke():
    """Smoke test for TensorForce wrapper; skipped when tensorforce is not installed."""
    tf = pytest.importorskip("tensorforce")
    # Import the trainer after tensorforce is available
    from backend.core.self_healing.marl_agent import MultiAgentEnv, MARLTrainer

    env = MultiAgentEnv(num_agents=2, obs_size=4, action_size=3, max_steps=10)
    trainer = MARLTrainer(env, backend="tensorforce", seed=1)
    # Run a single small episode to ensure wrapper works end-to-end
    stats = trainer.train(episodes=1)
    assert isinstance(stats, list)
    assert len(stats) == 1
    totals = stats[0]
    assert all(k.startswith("agent_") for k in totals.keys())
