"""Training and export utilities for the PASM TGNN model.

This script trains a tiny model on synthetic data and exports a MindSpore
`.mindir` file when MindSpore is available. In environments without
MindSpore it writes a safe placeholder file containing metadata so the
inference pipeline can still operate in fallback mode.

Usage (development):
    from ai_models.pasm.train_pasm_tgnn import train_and_export
    train_and_export(output_path)
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_synthetic_dataset(n_samples=200, n_features=8):
    import random

    X = [[random.random() for _ in range(n_features)] for _ in range(n_samples)]
    y = [1 if x[0] > 0.5 else 0 for x in X]
    return X, y


def train_and_export(output_path: str | Path, epochs: int = 3, feature_dim: int = 8):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Try to import MindSpore
    try:
        import mindspore as ms  # type: ignore
        import numpy as _np

        have_ms = True
    except Exception:
        have_ms = False

    X, y = generate_synthetic_dataset(n_samples=200, n_features=feature_dim)

    if have_ms:
        try:
            from ai_models.pasm.model import get_mindspore_model
            from mindspore import Tensor

            net = get_mindspore_model(ms, input_dim=feature_dim, hidden=32)
            loss = ms.nn.SoftmaxCrossEntropyWithLogits(sparse=True, reduction='mean')
            opt = ms.nn.Adam(net.trainable_params(), learning_rate=1e-3)
            train_net = ms.nn.TrainOneStepCell(ms.nn.WithLossCell(net, loss), opt)

            X_np = _np.array(X, dtype=_np.float32)
            y_np = _np.array(y, dtype=_np.int32)
            dataset = ms.dataset.NumpySlicesDataset({'x': X_np, 'y': y_np}, shuffle=True)

            for epoch in range(max(1, int(epochs))):
                for batch in dataset.create_dict_iterator():
                    train_net(batch['x'], batch['y'])

            # Export to MindIR using ms.export
            try:
                sample_in = Tensor(_np.zeros((1, feature_dim), dtype=_np.float32))
                logger.info("Exporting MindSpore model to %s", str(output_path))
                ms.export(net, sample_in, file_name=str(output_path.with_suffix('')), file_format='MINDIR')
                # mindspore export will add .mindir suffix; ensure we return that path
                mindir_path = str(output_path.with_suffix('.mindir'))
                if not Path(mindir_path).exists():
                    # sometimes ms.export writes exactly file_name + '.mindir'
                    mindir_path = str(output_path) + '.mindir'
                return mindir_path
            except Exception:
                logger.exception("Failed to export MindSpore model; will write placeholder")

        except Exception:
            logger.exception("MindSpore training failed; falling back to placeholder model")

    # Fallback: write a small placeholder file containing metadata
    meta = {
        "created_at": time.time(),
        "feature_dim": feature_dim,
        "epochs": epochs,
        "note": "placeholder mindir - replace with real MindSpore export for production",
    }
    # Write a human-readable placeholder file so infer can detect its presence
    p = output_path.with_suffix('.mindir')
    with p.open('w', encoding='utf-8') as fh:
        fh.write('# Placeholder for pasm_tgnn.mindir model binary\n')
        fh.write(json.dumps(meta, indent=2))
    logger.info('Wrote placeholder MindIR to %s', p)
    return str(p)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--out', '-o', default='ai_models/pretrained/pasm_tgnn.mindir')
    parser.add_argument('--epochs', type=int, default=3)
    args = parser.parse_args()
    path = train_and_export(args.out, epochs=args.epochs)
    print('Model written to', path)
