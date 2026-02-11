"""Dataset loader for PASM TGNN.

This module provides utilities to build dynamic asset graphs from a
tabular timeseries (CSV) using pandas and expose them as a MindSpore
GeneratorDataset. The produced items match the input shape expected by
`backend.core.pasm.tgnn_model.TGNNModel.predict`: a dict with keys
`nodes` (list of {id, features}) and `edges` (list of pairs).

The implementation is defensive: when MindSpore is not available the
function returns a Python generator. MindSpore and pandas are the
preferred path as requested.
"""

from __future__ import annotations

import logging
from typing import Iterator, Dict, Any, List, Optional

logger = logging.getLogger("jarvis.pasm.dataset_loader")

try:
    import pandas as pd
except Exception:  # pragma: no cover - optional dependency
    pd = None

try:
    import mindspore as ms
    import mindspore.dataset as msd
except Exception:  # pragma: no cover - optional dependency
    ms = None
    msd = None


def _iter_graphs_from_data(
    node_df,
    edges: Optional[List[List[Any]]],
    id_col: str = "asset_id",
    time_col: str = "timestamp",
    feature_cols: Optional[List[str]] = None,
    window_size: int = 1,
    stride: int = 1,
) -> Iterator[Dict[str, Any]]:
    """Yield dynamic graphs from loaded DataFrame.

    node_df must contain columns [id_col, time_col, *feature_cols]. Rows are
    grouped by time windows to produce snapshots. For each snapshot we
    produce a dict {"nodes": [...], "edges": [...] } where each node's
    features is a list of timesteps (most recent first).
    """
    if feature_cols is None:
        # default: take all other columns as features
        feature_cols = [c for c in node_df.columns if c not in (id_col, time_col)]

    # Ensure timestamp is datetime-like
    if not pd.api.types.is_datetime64_any_dtype(node_df[time_col]):
        node_df = node_df.copy()
        node_df[time_col] = pd.to_datetime(node_df[time_col])

    node_df = node_df.sort_values(time_col)

    times = node_df[time_col].drop_duplicates().to_list()
    # sliding window over time indices
    idx = 0
    while idx < len(times):
        window_times = times[idx : idx + window_size]
        # select rows in window
        window_rows = node_df[node_df[time_col].isin(window_times)]

        nodes = []
        # build per-asset temporal sequences (ordered by time)
        for asset_id, group in window_rows.groupby(id_col):
            group = group.sort_values(time_col)
            feats = group[feature_cols].to_numpy(dtype=float).tolist()
            nodes.append({"id": asset_id, "features": feats})

        yield {"nodes": nodes, "edges": edges or []}

        idx += stride


def create_mindspore_dataset(
    node_csv: str,
    edge_csv: Optional[str] = None,
    id_col: str = "asset_id",
    time_col: str = "timestamp",
    feature_cols: Optional[List[str]] = None,
    window_size: int = 1,
    stride: int = 1,
    batch_size: int = 1,
) -> "msd.Dataset | Iterator[Dict[str, Any]]":
    """Create a MindSpore GeneratorDataset (or Python generator) of graphs.

    Arguments:
      node_csv: CSV path containing timeseries rows per asset.
      edge_csv: optional CSV with two columns (u,v) for static edges.
      id_col, time_col: column names in node_csv.
      feature_cols: list of feature column names; if None, will infer.
      window_size: number of distinct time steps per snapshot.
      stride: snapshot stride.

    Returns:
      If MindSpore is installed, an ms.dataset.GeneratorDataset instance
      yielding single-column items (dicts). Otherwise, a Python generator
      producing the same dicts.
    """
    if pd is None:
        raise RuntimeError("pandas is required for create_mindspore_dataset")

    node_df = pd.read_csv(node_csv)

    edges = None
    if edge_csv is not None:
        try:
            e_df = pd.read_csv(edge_csv)
            # Expect columns named u,v or 0,1
            if {"u", "v"}.issubset(e_df.columns):
                edges = e_df[["u", "v"]].values.tolist()
            else:
                # take first two columns
                edges = e_df.iloc[:, 0:2].values.tolist()
        except Exception:
            logger.exception("failed to load edge CSV; proceeding without edges")
            edges = None

    generator = lambda: _iter_graphs_from_data(
        node_df,
        edges,
        id_col=id_col,
        time_col=time_col,
        feature_cols=feature_cols,
        window_size=window_size,
        stride=stride,
    )

    if msd is not None:
        # Create a MindSpore GeneratorDataset; yield one column 'graph'
        ds = msd.GeneratorDataset(generator(), column_names=["graph"], python_multiprocessing=False)
        if batch_size and batch_size > 1:
            ds = ds.batch(batch_size)
        return ds

    # fallback: return the plain Python iterator
    return generator()


if __name__ == "__main__":
    # quick demo (requires pandas)
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dataset_loader.py path/to/node.csv [edge.csv]")
        raise SystemExit(1)

    node_csv = sys.argv[1]
    edge_csv = sys.argv[2] if len(sys.argv) > 2 else None
    ds = create_mindspore_dataset(node_csv, edge_csv=edge_csv, window_size=3, stride=1)
    if msd is not None and hasattr(ds, "create_dict_iterator"):
        it = ds.create_dict_iterator(output_numpy=True)
        print(next(it))
    else:
        it = iter(ds)
        print(next(it))
# Placeholder dataset loader for TGNN

def load_dataset(path: str):
    return []
