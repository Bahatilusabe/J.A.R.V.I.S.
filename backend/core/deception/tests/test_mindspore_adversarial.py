import os
import tempfile
import shutil
import pytest

from backend.core.deception.decoy_ai_trainer import (
    DecoyAITrainer,
    generate_synthetic_dataset,
    MindSporeAdversarialTrainer,
)


def test_adversarial_trainer_simulated(tmp_path):
    """Smoke test: run the adversarial trainer; if MindSpore is present and
    RUN_MINDSPORE_CI=1 it will exercise the MindSpore branch; otherwise the
    simulated fallback should run and produce artifacts.
    """
    X, y = generate_synthetic_dataset(n_samples=50, n_features=4, seed=1)
    workdir = tmp_path / "adv_work"
    workdir.mkdir()
    trainer = DecoyAITrainer(work_dir=str(workdir))
    adv = MindSporeAdversarialTrainer(trainer)

    # If RUN_MINDSPORE_CI is not enabled, skip the heavy MindSpore branch and
    # rely on the simulated fallback being exercised by the trainer.
    if os.environ.get("RUN_MINDSPORE_CI", "0") != "1":
        # run in fallback/simulated mode and assert artifact created
        path = adv.run_adversarial_training(X, y, artifact_name="ci-advtest", epochs=1, perturbation_strength=0.01, random_state=1)
        assert os.path.exists(path)
        return

    # Otherwise run the true MindSpore branch (CI must install MindSpore and set RUN_MINDSPORE_CI=1)
    path = adv.run_adversarial_training(X, y, artifact_name="ci-advtest", epochs=1, perturbation_strength=0.01, random_state=1)
    assert os.path.exists(path)
    # ensure .artifact file present
    assert any(p.endswith('.artifact') for p in os.listdir(str(workdir)))
import os
import tempfile
import shutil
import pytest

from backend.core.deception.decoy_ai_trainer import (
    DecoyAITrainer,
    generate_synthetic_dataset,
    MindSporeAdversarialTrainer,
)


def test_adversarial_trainer_simulated(tmp_path):
    """Smoke test: run the adversarial trainer; if RUN_MINDSPORE_CI=1 it will
    exercise the MindSpore branch; otherwise the simulated fallback will run
    and produce artifacts.
    """
    X, y = generate_synthetic_dataset(n_samples=50, n_features=4, seed=1)
    workdir = tmp_path / "adv_work"
    workdir.mkdir()
    trainer = DecoyAITrainer(work_dir=str(workdir))
    adv = MindSporeAdversarialTrainer(trainer)

    # If RUN_MINDSPORE_CI is not enabled, run the simulated fallback only.
    if os.environ.get("RUN_MINDSPORE_CI", "0") != "1":
        path = adv.run_adversarial_training(X, y, artifact_name="ci-advtest", epochs=1, perturbation_strength=0.01, random_state=1)
        assert os.path.exists(path)
        assert any(p.endswith('.artifact') for p in os.listdir(str(workdir)))
        return

    # Otherwise run the true MindSpore branch (CI must install MindSpore and set RUN_MINDSPORE_CI=1)
    path = adv.run_adversarial_training(X, y, artifact_name="ci-advtest", epochs=1, perturbation_strength=0.01, random_state=1)
    assert os.path.exists(path)
    assert any(p.endswith('.artifact') for p in os.listdir(str(workdir)))
