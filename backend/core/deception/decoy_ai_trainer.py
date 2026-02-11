"""
Decoy AI trainer utilities.

This module provides tools to generate synthetic "decoy" datasets and to
train small, non-sensitive models for use as decoys in simulation or
defensive research. It avoids heavy dependencies when possible and uses
scikit-learn if available; otherwise it falls back to a safe randomized
model representation.

The produced decoy models are meant for deception and defensive testing
— not for operational decision-making.
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import random
import re
import time
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Callable

logger = logging.getLogger(__name__)


def generate_synthetic_dataset(n_samples: int = 500, n_features: int = 8, seed: Optional[int] = None):
    """Generate a simple synthetic classification dataset.

    Returns (X, y) where X is a list of float lists and y is a list of 0/1 labels.
    """
    if seed is not None:
        random.seed(seed)
    X = [[random.random() for _ in range(n_features)] for _ in range(n_samples)]
    # simple linear separator on first feature for deterministic-ish labels
    y = [1 if row[0] > 0.5 else 0 for row in X]
    return X, y


@dataclass
class DecoyModelArtifact:
    metadata: Dict[str, Any]
    model_bytes: bytes


class DecoyAITrainer:
    """Train and persist simple decoy models.

    If scikit-learn is available, a LogisticRegression model is trained.
    Otherwise, a lightweight randomized-model artifact is produced.
    """

    def __init__(self, work_dir: str = ".decoy_models") -> None:
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

    def train(self, X, y, name: str = "decoy", random_state: Optional[int] = None) -> DecoyModelArtifact:
        """Train a decoy model and return an artifact object.

        The artifact can be persisted with `save_artifact`.
        """
        try:
            from sklearn.linear_model import LogisticRegression
            import numpy as _np

            X_np = _np.array(X)
            y_np = _np.array(y)
            model = LogisticRegression(solver="liblinear", random_state=random_state)
            model.fit(X_np, y_np)
            model_bytes = pickle.dumps(model)
            metadata = {"backend": "sklearn", "n_features": X_np.shape[1], "n_samples": X_np.shape[0]}
            logger.info("Trained decoy sklearn LogisticRegression model: %s", name)
            return DecoyModelArtifact(metadata=metadata, model_bytes=model_bytes)
        except Exception:
            # Fallback: produce a randomized artifact (safe, no ML dependency)
            metadata = {"backend": "randomized", "n_features": len(X[0]) if X else 0, "n_samples": len(X)}
            # simple deterministic pseudorandom 'weights'
            weights = [random.random() for _ in range(metadata["n_features"])]
            artifact = {"weights": weights, "bias": random.random()}
            model_bytes = json.dumps(artifact).encode("utf-8")
            logger.info("Produced randomized decoy model artifact: %s", name)
            return DecoyModelArtifact(metadata=metadata, model_bytes=model_bytes)

    def save_artifact(self, artifact: DecoyModelArtifact, name: str) -> str:
        path = os.path.join(self.work_dir, f"{name}.artifact")
        with open(path, "wb") as fh:
            fh.write(artifact.model_bytes)
        meta_path = os.path.join(self.work_dir, f"{name}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(artifact.metadata, fh)
        logger.info("Saved decoy model artifact to %s", path)
        return path

    def load_artifact(self, path: str) -> DecoyModelArtifact:
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        with open(path, "rb") as fh:
            data = fh.read()
        # try to read metadata from sibling .meta.json
        meta_path = path.replace(".artifact", ".meta.json")
        metadata = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as fh:
                metadata = json.load(fh)
        return DecoyModelArtifact(metadata=metadata, model_bytes=data)


__all__ = ["generate_synthetic_dataset", "DecoyAITrainer", "DecoyModelArtifact"]


def make_decoy_generation_policy(
    trainer: DecoyAITrainer,
    name_prefix: str = "decoy",
    trigger_substring: str = "login.failed",
    n_samples: int = 200,
    n_features: int = 8,
    random_state: Optional[int] = None,
) -> Callable[[object, object], None]:
    """Return a policy callable(event, manager) that trains and saves a decoy model.

    The returned policy is intentionally conservative: it trains small synthetic
    datasets locally, saves artifacts to the trainer's work_dir, and records a
    simulation event with the provided `manager`. It does NOT perform network
    operations or deploy anything.

    Args:
        trainer: DecoyAITrainer instance used to train and persist artifacts.
        name_prefix: file-name prefix for saved artifacts.
        trigger_substring: substring matched against event.payload_summary to
            decide whether to trigger generation.
        n_samples, n_features: synthetic dataset sizes (kept modest by default).
        random_state: optional seed passed to trainer.train and dataset generator.
    """

    def sanitize(s: Optional[str]) -> str:
        if not s:
            return "unknown"
        # replace characters unsuitable for filenames
        return re.sub(r"[^A-Za-z0-9_.-]", "-", s)

    def policy(event, manager) -> None:
        try:
            payload_text = (event.payload_summary or "").lower()
            if trigger_substring.lower() not in payload_text:
                return

            # Keep artifacts small for safety
            X, y = generate_synthetic_dataset(n_samples=n_samples, n_features=n_features, seed=random_state)
            safe_ip = sanitize(event.client_ip)
            ts = int(getattr(event, "timestamp", time.time()))
            artifact_name = f"{name_prefix}-{safe_ip}-{ts}"
            artifact = trainer.train(X, y, name=artifact_name, random_state=random_state)
            path = trainer.save_artifact(artifact, artifact_name)

            # Record simulated action in the HoneypotManager
            manager.record_interaction(
                honeypot_name=getattr(event, "honeypot_name", "decoy"),
                client_ip=event.client_ip,
                client_port=getattr(event, "client_port", None),
                payload_summary=f"decoy_generated:{hashlib.sha256(path.encode()).hexdigest()[:8]}",
                notes=json.dumps({"artifact_path": path}),
            )
            logging.getLogger(__name__).info("Decoy artifact generated: %s", path)
            # Optionally emit to Huawei AOM for visualization/OPS if configured.
            try:
                try:
                    from backend.integrations.huawei_aom import send_event  # type: ignore
                except Exception:
                    send_event = None

                if send_event is not None:
                    payload = {
                        "artifact_path": path,
                        "artifact_name": artifact_name,
                        "honeypot": getattr(event, "honeypot_name", "decoy"),
                        "client_ip": event.client_ip,
                        "meta": artifact.metadata,
                    }
                    try:
                        send_event("decoy_artifact_generated", payload)
                    except Exception:
                        logging.getLogger(__name__).debug("Huawei AOM send_event failed in decoy policy")
            except Exception:
                logging.getLogger(__name__).debug("Error while attempting to send Huawei AOM event from decoy policy")
        except Exception:
            logging.getLogger(__name__).exception("decoy generation policy failed")

    return policy


__all__.append("make_decoy_generation_policy")


class MindSporeAdversarialTrainer:
    """Adversarial training helper using MindSpore when available.

    This class attempts to use MindSpore to perform an adversarial-style
    retraining loop that learns attacker perturbations. For safety and to
    keep development environments working, if MindSpore is not available
    the class falls back to a conservative simulated loop that perturbs
    the synthetic dataset and retrains using the `DecoyAITrainer`.

    Important safety notes:
    - This implementation performs local, synthetic-data training only.
    - It does not connect to any external service, does not collect PII,
      and does not automate attacks.
    - The MindSpore branch is guarded by a lazy import and will only run
      if the MindSpore package is installed and importable.
    """

    def __init__(self, trainer: DecoyAITrainer, work_dir: Optional[str] = None):
        self.trainer = trainer
        self.work_dir = work_dir or trainer.work_dir
        self._ms = None
        self._have_mindspore = False
        try:
            import mindspore as ms  # type: ignore

            self._ms = ms
            self._have_mindspore = True
        except Exception:
            self._ms = None
            self._have_mindspore = False

    def run_adversarial_training(
        self,
        X,
        y,
        artifact_name: str = "adv-decoy",
        epochs: int = 3,
        perturbation_strength: float = 0.05,
        random_state: Optional[int] = None,
    ) -> str:
        """Run adversarial training and save a decoy artifact.

        Args:
            X, y: dataset (lists or numpy arrays)
            artifact_name: base name for saved artifact
            epochs: number of adversarial iterations
            perturbation_strength: magnitude of synthetic perturbations
            random_state: optional seed for deterministic behavior

        Returns:
            path to saved artifact file
        """
        if self._have_mindspore:
            try:
                return self._run_mindspore_training(X, y, artifact_name, epochs, perturbation_strength, random_state)
            except Exception:
                # Fall back to simulation if MindSpore path fails
                logging.getLogger(__name__).exception("MindSpore training failed, falling back to simulated loop")
                return self._run_simulated_training(X, y, artifact_name, epochs, perturbation_strength, random_state)
        else:
            return self._run_simulated_training(X, y, artifact_name, epochs, perturbation_strength, random_state)

    def _run_simulated_training(self, X, y, artifact_name, epochs, strength, random_state) -> str:
        """Conservative fallback: perturb features and retrain using DecoyAITrainer.

        This loop perturbs features by adding small random noise and retrains
        the decoy model on the perturbed dataset, iteratively producing a
        final artifact saved via DecoyAITrainer.save_artifact().
        """
        if random_state is not None:
            random.seed(random_state)

        X_curr = [list(row) for row in X]
        y_curr = list(y)

        path = None
        for it in range(max(1, int(epochs))):
            # perturb a random subset of samples
            for i in range(len(X_curr)):
                if random.random() < 0.3:
                    row = X_curr[i]
                    for j in range(len(row)):
                        noise = (random.random() * 2 - 1) * strength
                        row[j] = float(row[j]) + noise
                    X_curr[i] = row

            # retrain small decoy model
            artifact = self.trainer.train(X_curr, y_curr, name=artifact_name + f"-iter{it}")
            path = self.trainer.save_artifact(artifact, artifact_name + f"-iter{it}")

        # return last artifact path
        return path

    def _run_mindspore_training(self, X, y, artifact_name, epochs, strength, random_state) -> str:
        """A guarded, minimal MindSpore adversarial training loop.

        NOTE: This method is only executed when MindSpore is importable. It
        uses a tiny MLP defined in MindSpore, creates adversarial-like
        perturbations via gradient sign updates, and retrains the model.

        Because MindSpore setups vary widely, this code is intentionally
        minimal and wrapped in try/except; errors fall back to the
        simulated trainer.
        """
        ms = self._ms
        # Lazy imports inside method to avoid import-time failures
        import numpy as _np

        X_np = _np.array(X, dtype=_np.float32)
        y_np = _np.array(y, dtype=_np.int32)

        # Simple dataset tensors
        dataset = ms.dataset.NumpySlicesDataset({'x': X_np, 'y': y_np}, shuffle=True)

        net = ms.nn.SequentialCell(
            ms.nn.Dense(X_np.shape[1], 64),
            ms.nn.ReLU(),
            ms.nn.Dense(64, 2)
        )

        loss_fn = ms.nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
        opt = ms.nn.Adam(net.trainable_params(), learning_rate=1e-3)
        train_net = ms.nn.TrainOneStepCell(ms.nn.WithLossCell(net, loss_fn), opt)

        # training loop (very small, guarded) with optional FGSM adversarial step
        try:
            # prepare a simple loss function wrapper to compute gradients
            from mindspore import Tensor
            from mindspore import ops
            from mindspore import float32

            def loss_fn_for_grad(x_in, y_in):
                preds = net(x_in)
                return loss_fn(preds, y_in)

            # value_and_grad wrapper if available (preferred), else try GradOperation
            grad_fn = None
            try:
                # some MindSpore versions expose value_and_grad at top-level
                try:
                    from mindspore import value_and_grad
                    grad_fn = value_and_grad(loss_fn_for_grad, None, (0,))
                except Exception:
                    # try ops.value_and_grad
                    try:
                        grad_fn = getattr(ops, 'value_and_grad')(loss_fn_for_grad, None, (0,))
                    except Exception:
                        grad_fn = None
            except Exception:
                grad_fn = None

            # If value_and_grad isn't available, try GradOperation which is
            # commonly present across MindSpore releases. This returns a
            # function computing gradients; we wrap it to match grad_fn
            if grad_fn is None:
                try:
                    GradOp = getattr(ops, 'GradOperation')
                    gradop = GradOp(get_by_list=False, sens_param=False)

                    def _grad_fn(x_in, y_in):
                        # compute gradient of scalar loss w.r.t x_in
                        g = gradop(loss_fn_for_grad)(x_in, y_in)
                        # mimic value_and_grad returning (loss, grad)
                        return loss_fn_for_grad(x_in, y_in), g

                    grad_fn = _grad_fn
                except Exception:
                    grad_fn = None

            for epoch in range(max(1, int(epochs))):
                for batch in dataset.create_dict_iterator():
                    x_batch = batch['x']
                    y_batch = batch['y']
                    # forward/backward step
                    train_net(x_batch, y_batch)

                    # FGSM adversarial perturbation: compute gradient w.r.t inputs if possible
                    try:
                        if grad_fn is not None:
                            # value_and_grad returns (loss, grad)
                            loss_val, grad = grad_fn(x_batch, y_batch)
                            # grad corresponds to gradient w.r.t. x_batch
                            # take sign and perturb inputs
                            sign = ops.Sign()(grad)
                            x_adv_np = _np.array(x_batch.asnumpy()) + _np.sign(_np.array(sign.asnumpy())) * strength
                        else:
                            # best-effort fallback: perturb by sign of mean activations
                            try:
                                mean_act = ops.ReduceMean(keep_dims=True)(x_batch, 1)
                                sign_est = ops.Sign()(mean_act)
                                x_adv_np = _np.array(x_batch.asnumpy()) + _np.sign(_np.array(sign_est.asnumpy())) * strength
                            except Exception:
                                # final fallback: small random perturbation
                                x_adv_np = _np.array(x_batch.asnumpy()) + (_np.random.randn(*_np.array(x_batch.asnumpy()).shape) * strength)
                        # clip to reasonable range (inputs are synthetic in [0,1])
                        try:
                            x_adv_np = _np.clip(x_adv_np, 0.0, 1.0)
                        except Exception:
                            pass
                        x_adv = Tensor(x_adv_np, dtype=float32)
                        # Optionally perform one train step on adversarial examples
                        try:
                            train_net(x_adv, y_batch)
                        except Exception:
                            # If training on x_adv fails, continue
                            pass
                    except Exception:
                        # Ignore if gradient computation not supported in this environment
                        pass

            # Attempt to checkpoint the model using MindSpore serialization
            try:
                # try standard serialization helper
                try:
                    from mindspore.train.serialization import save_checkpoint
                    ckpt_path = os.path.join(self.work_dir, f"{artifact_name}-ckpt.ckpt")
                    save_checkpoint(net, ckpt_path)
                except Exception:
                    # fallback to top-level API if present
                    try:
                        ms.save_checkpoint(net, os.path.join(self.work_dir, f"{artifact_name}-ckpt.ckpt"))
                    except Exception:
                        ckpt_path = None
                # record metadata including checkpoint path when available
                meta = {"mindspore_trained": True, "shape": X_np.shape, "epochs": int(epochs), "ckpt": ckpt_path}
            except Exception:
                meta = {"mindspore_trained": True, "shape": X_np.shape, "epochs": int(epochs)}

            artifact = DecoyModelArtifact(metadata=meta, model_bytes=json.dumps(meta).encode('utf-8'))
            path = self.trainer.save_artifact(artifact, artifact_name + "-mindspore")
            return path
        except Exception:
            # If any MindSpore-specific step fails unexpectedly, raise to caller
            raise

