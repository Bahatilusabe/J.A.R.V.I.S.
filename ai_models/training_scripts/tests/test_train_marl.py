import json
import tempfile
from pathlib import Path

from ai_models.training_scripts import train_marl


def test_train_marl_numpy_smoke():
    """Run a very short NumPy-fallback training and assert checkpoint exists."""
    td = tempfile.TemporaryDirectory()
    out = Path(td.name)

    env = train_marl.SelfHealingEnv(n_services=4, p_fail=0.1, seed=1)
    # run a single-episode, tiny-step training
    train_marl.train_numpy(env, out_dir=out, episodes=1, steps_per_episode=3, seed=1)

    p = out / "marl_numpy_checkpoint.json"
    assert p.exists(), f"expected checkpoint at {p}"

    data = json.loads(p.read_text(encoding="utf-8"))
    assert data.get("framework", "").startswith("numpy"), "unexpected checkpoint framework"

    td.cleanup()
