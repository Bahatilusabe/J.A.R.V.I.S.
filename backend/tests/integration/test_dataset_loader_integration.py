import csv
import json
from pathlib import Path

import pytest

from backend.core.pasm.dataset_loader import create_mindspore_dataset


def _write_node_csv(path: Path):
    rows = [
        ("asset_id", "timestamp", "f1", "f2"),
        ("1", "2025-11-11T12:00:00", "0.1", "0.2"),
        ("1", "2025-11-11T12:01:00", "0.2", "0.3"),
        ("2", "2025-11-11T12:00:00", "0.0", "0.1"),
        ("2", "2025-11-11T12:01:00", "0.1", "0.0"),
    ]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)


def test_dataset_loader_generates_graphs(tmp_path: Path):
    node_csv = tmp_path / "nodes.csv"
    _write_node_csv(node_csv)

    # No MindSpore required for this integration test: create_mindspore_dataset will
    # return a Python generator when MindSpore isn't installed. We expect at least
    # one graph snapshot to be produced.
    ds = create_mindspore_dataset(str(node_csv), window_size=2, stride=1, batch_size=1)

    # If MindSpore dataset returned, iterate appropriately
    if hasattr(ds, "create_dict_iterator"):
        it = ds.create_dict_iterator(output_numpy=False)
        item = next(it)
        # mindspore GeneratorDataset yields dict with key 'graph'
        graph = item.get("graph") if isinstance(item, dict) else item
    else:
        graph = next(iter(ds))

    assert isinstance(graph, dict)
    assert "nodes" in graph
    assert len(graph["nodes"]) >= 1
    # each node must have id and features list
    for n in graph["nodes"]:
        assert "id" in n and "features" in n
        assert isinstance(n["features"], list)
