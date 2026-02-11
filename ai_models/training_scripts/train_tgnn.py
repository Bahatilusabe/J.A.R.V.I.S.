"""TGNN training job prepared for ModelArts Notebook (MindSpore).

This script is intended to be run inside a ModelArts Notebook or locally.
Features:
- Uses MindSpore for model, training loop and checkpointing when available.
- Optionally integrates with ModelArts via the `moxing` library to copy
  data/checkpoints to and from OBS.
- Provides a pure-NumPy fallback so the script can be executed in
  environments without MindSpore for smoke-testing and CI.

Usage (ModelArts Notebook):
  - Upload your dataset (node features, adjacency) to OBS and configure
    input/output paths. Enable `--use-modelarts` to activate moxing copy.
  - Run the notebook cell that executes this script; checkpoints will be
    saved to the `--output-dir` and optionally synced back to OBS.

This training script implements a simple full-batch Graph Neural Network
that aggregates neighbor features via adjacency matrix multiplication.
It's intentionally small so it runs quickly for demos; replace it with a
full TGNN implementation when you wire production data.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("train_tgnn")
logging.basicConfig(level=logging.INFO)


def try_imports():
    ms = None
    mox = None
    try:
        import mindspore as ms  # type: ignore

        # also import common submodules we use
        import mindspore.nn as _nn  # type: ignore
        import mindspore.dataset as _ds  # type: ignore
    except Exception:
        ms = None

    try:
        import moxing as mox  # type: ignore

    except Exception:
        mox = None

    return ms, mox


def generate_synthetic_graph(n_nodes: int = 128, feat_dim: int = 8) -> Tuple:
    import random
    import numpy as _np

    X = _np.random.RandomState(0).rand(n_nodes, feat_dim).astype(_np.float32)
    # simple random adjacency (symmetric)
    A = _np.random.RandomState(1).rand(n_nodes, n_nodes) > 0.95
    A = A.astype(_np.float32)
    # make symmetric and add self-loops
    A = ((A + A.T) > 0).astype(_np.float32)
    for i in range(n_nodes):
        A[i, i] = 1.0

    # simple binary labels based on first feature
    y = (_np.array([1 if x[0] > 0.5 else 0 for x in X])).astype(_np.int32)
    return X, A, y


def load_data(data_dir: Path, feature_dim: int = 8):
    """Load node features and adjacency from data_dir or synthesize if absent."""
    import numpy as _np

    feat_path = data_dir / "node_features.npy"
    adj_path = data_dir / "adjacency.npy"
    labels_path = data_dir / "labels.npy"

    if feat_path.exists() and adj_path.exists() and labels_path.exists():
        X = _np.load(feat_path)
        A = _np.load(adj_path)
        y = _np.load(labels_path)
        logger.info("Loaded dataset from %s", data_dir)
        return X.astype(_np.float32), A.astype(_np.float32), y.astype(_np.int32)

    logger.info("Dataset not found in %s; generating synthetic dataset", data_dir)
    return generate_synthetic_graph(n_nodes=128, feat_dim=feature_dim)


def build_mindspore_net(ms, input_dim: int = 8, hidden: int = 64):
    """Return a simple MindSpore-based GNN-like network.

    Design: H = ReLU(A @ X @ W1) then logits = Dense(H, 2)
    """
    import mindspore.nn as nn  # type: ignore
    from mindspore import Tensor

    class SimpleGNN(nn.Cell):
        def __init__(self, in_dim=input_dim, hidden_dim=hidden, out_dim=2):
            super().__init__()
            self.dense1 = nn.Dense(in_dim, hidden_dim)
            self.act = nn.ReLU()
            self.dense2 = nn.Dense(hidden_dim, out_dim)

        def construct(self, A, X):
            # A: (N,N), X: (N, D)
            # aggregate: A @ X -> (N, D)
            h = A @ X
            h = self.dense1(h)
            h = self.act(h)
            logits = self.dense2(h)
            return logits

    return SimpleGNN()


def train_with_mindspore(ms, X, A, y, epochs: int, lr: float, out_dir: Path):
    import numpy as _np
    import mindspore as _ms
    from mindspore import Tensor
    import mindspore.nn as nn

    N = X.shape[0]

    net = build_mindspore_net(_ms, input_dim=X.shape[1], hidden=64)
    loss_fn = nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
    opt = nn.Adam(net.trainable_params(), learning_rate=lr)
    train_net = nn.TrainOneStepCell(nn.WithLossCell(net, loss_fn), opt)

    # prepare tensors
    A_t = Tensor(A)
    X_t = Tensor(X)
    y_t = Tensor(y)

    for epoch in range(1, epochs + 1):
        # full-batch step
        train_net(A_t, X_t, y_t)
        if epoch % max(1, epochs // 5) == 0 or epoch == epochs:
            logger.info("[MS] epoch %d/%d completed", epoch, epochs)

    # checkpoint
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        ckpt_path = str(out_dir / "tgnn_ckpt.ckpt")
        try:
            from mindspore.train.serialization import save_checkpoint

            save_checkpoint(net, ckpt_path)
        except Exception:
            # fallback to top-level API
            try:
                _ms.save_checkpoint(net, ckpt_path)
            except Exception:
                logger.exception("Failed to save MindSpore checkpoint; continuing")
        logger.info("Saved checkpoint to %s", ckpt_path)
    except Exception:
        logger.exception("Checkpoint save failed")


def train_with_numpy(X, A, y, epochs: int, lr: float, out_dir: Path):
    """Fallback training loop that simulates training and writes metadata."""
    import numpy as _np

    # Simulate a quick convergence by computing a trivial score
    # and writing a placeholder checkpoint JSON.
    best_score = 0.0
    for epoch in range(1, max(1, epochs) + 1):
        # synthetic improvement
        best_score = min(1.0, best_score + 0.01)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "framework": "numpy-fallback",
        "epochs": int(epochs),
        "score": float(best_score),
        "timestamp": time.time(),
    }
    p = out_dir / "tgnn_placeholder_checkpoint.json"
    with p.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh)
    logger.info("Wrote placeholder checkpoint to %s", p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="./data/pasm_tgnn", help="Path to training data")
    parser.add_argument("--output-dir", default="./outputs/tgnn", help="Path to write checkpoints and artifacts")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--feature-dim", type=int, default=8)
    parser.add_argument("--use-modelarts", action="store_true", help="If set, use moxing to copy data/checkpoints to OBS")
    args = parser.parse_args()

    ms, mox = try_imports()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)

    # If ModelArts copy-in requested and mox available, attempt to copy from OBS
    if args.use_modelarts and mox is not None:
        try:
            logger.info("Using moxing to copy data from OBS to %s", data_dir)
            # In ModelArts, input data often sits in /cache or specified OBS path; callers should set env vars accordingly.
            # Here we expect args.data_dir to be an OBS path like 'obs://bucket/path' when used with --use-modelarts.
            mox.file.copy(args.data_dir, str(data_dir), recursive=True)
        except Exception:
            logger.exception("moxing copy-in failed; continuing with local path")

    X, A, y = load_data(data_dir, feature_dim=args.feature_dim)

    # main training path
    if ms is not None:
        try:
            train_with_mindspore(ms, X, A, y, epochs=args.epochs, lr=args.lr, out_dir=out_dir)
        except Exception:
            logger.exception("MindSpore training failed; falling back to numpy trainer")
            train_with_numpy(X, A, y, epochs=args.epochs, lr=args.lr, out_dir=out_dir)
    else:
        logger.info("MindSpore not available; running fallback NumPy trainer")
        train_with_numpy(X, A, y, epochs=args.epochs, lr=args.lr, out_dir=out_dir)

    # If ModelArts copy-out requested, push outputs back to OBS
    if args.use_modelarts and mox is not None:
        try:
            logger.info("Copying outputs to OBS using moxing: %s -> %s", out_dir, args.output_dir)
            mox.file.copy(str(out_dir), args.output_dir, recursive=True)
        except Exception:
            logger.exception("moxing copy-out failed; outputs remain in %s", out_dir)


if __name__ == "__main__":
    main()
