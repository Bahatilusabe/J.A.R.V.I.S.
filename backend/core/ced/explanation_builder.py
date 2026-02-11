"""Human-readable explanation builder for model outputs and counterfactuals.

This module provides a small helper to convert raw model outputs and
counterfactual differences into concise, human-friendly narratives. It is
designed to be deterministic and dependency-free so it can be used in CI and
small-scale audits.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import logging

logger = logging.getLogger("jarvis.ced.explanation_builder")

# Optional heavy libs
_MINDSPORE_AVAILABLE = False
_PLOTLY_DASH_AVAILABLE = False
try:
    import mindspore as ms  # type: ignore
    _MINDSPORE_AVAILABLE = True
except Exception:
    ms = None  # type: ignore

try:
    import dash  # type: ignore
    from dash import html, dcc  # type: ignore
    import plotly.express as px  # type: ignore
    _PLOTLY_DASH_AVAILABLE = True
except Exception:
    dash = None  # type: ignore
    html = None  # type: ignore
    dcc = None  # type: ignore
    px = None  # type: ignore

try:
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore


class ExplanationBuilder:
    """Simple explanation generator.

    The builder accepts an original output dict and an optional counterfactual
    dict (or multiple counterfactuals) and returns short plain-text
    explanations.
    """

    def build_explanation(self, original: Dict[str, Any], counterfactual: Dict[str, Any] | None = None) -> str:
        """Create a short explanation comparing original and counterfactual.

        Args:
            original: model output or observation
            counterfactual: counterfactual outcome

        Returns:
            A human-readable paragraph summarizing key deltas.
        """
        lines: List[str] = []
        lines.append("Model output summary:")
        for k, v in original.items():
            lines.append(f"- {k}: {v}")

        if counterfactual:
            lines.append("")
            lines.append("Counterfactual outcome:")
            diffs = self._summarize_diffs(original, counterfactual)
            if not diffs:
                lines.append("- No meaningful change under the intervention.")
            else:
                for d in diffs:
                    lines.append(f"- {d}")

        return "\n".join(lines)

    def _summarize_diffs(self, orig: Dict[str, Any], cf: Dict[str, Any]) -> Iterable[str]:
        for k in sorted(set(orig.keys()) | set(cf.keys())):
            o = orig.get(k)
            c = cf.get(k)
            if o == c:
                continue
            yield f"{k} changed from {o!r} to {c!r}"


__all__ = ["ExplanationBuilder"]


class DashExplanationBuilder(ExplanationBuilder):
    """Hybrid explanation builder that can produce a narrative and an optional
    Plotly Dash app containing simple visualizations.

    This builder is gated: if Dash or MindSpore are unavailable it can still
    produce narrative text via the parent class.
    """

    def build_app(self, original: Dict[str, Any], counterfactual: Optional[Dict[str, Any]] = None, title: str = "Explanation"):
        """Return a Dash layout (callable) or raise if Dash isn't available.

        The layout contains a narrative section and a simple bar chart of
        feature values. This is intentionally lightweight and suitable for
        developer demos.
        """
        if not _PLOTLY_DASH_AVAILABLE:
            raise RuntimeError("Plotly Dash not available in this environment")

        narrative = self.build_explanation(original, counterfactual)

        # produce a simple dataframe-like structure for plotting
        keys = list(original.keys())
        vals = [original[k] for k in keys]
        fig = px.bar(x=keys, y=vals, labels={"x": "feature", "y": "value"}, title="Model output")

        layout = html.Div([
            html.H3(title),
            html.Pre(narrative),
            dcc.Graph(figure=fig),
        ])

        return layout

    def compute_saliency(self, model: Any, input_data: Any, feature_names: Optional[List[str]] = None, target_index: Optional[int] = None) -> Dict[str, float]:
        """Compute a gradients-based saliency map for `input_data` w.r.t model outputs.

        This method is gated: if MindSpore is available it uses GradOperation to
        compute gradients; otherwise it attempts a simple finite-difference
        approximation using numpy. Returns a mapping from feature name (or
        index) to saliency magnitude (absolute gradient summed over batch).
        """
        # Prefer MindSpore gradients when available
        if _MINDSPORE_AVAILABLE and ms is not None:
            # ensure input is an ms.Tensor
            inp = input_data if isinstance(input_data, ms.Tensor) else ms.Tensor(input_data)

            # use GradOperation; many MindSpore versions provide ms.GradOperation
            Grad = getattr(ms, "GradOperation", None)
            if Grad is None:
                raise RuntimeError("MindSpore GradOperation not available in this environment")

            grad_op = Grad(get_all=False, get_by_list=False)

            def loss_fn(x):
                preds = model(x)
                if target_index is not None:
                    # assume preds shape (batch, n)
                    return preds[:, target_index].sum()
                return preds.sum()

            grads = grad_op(loss_fn)(inp)
            g_np = grads.asnumpy() if hasattr(grads, "asnumpy") else None
            if g_np is None:
                # shouldn't happen; fallback
                raise RuntimeError("Unable to convert MindSpore gradients to numpy")

            arr = g_np

        else:
            # Finite-difference fallback using numpy
            if np is None:
                raise RuntimeError("Neither MindSpore nor numpy are available for saliency computation")

            x = np.asarray(input_data, dtype=float)
            eps = 1e-3
            base = np.asarray(model(x)).sum()
            # assume last dimension are features
            feat_dim = x.shape[-1] if x.ndim >= 1 else 1
            grads = np.zeros(feat_dim, dtype=float)
            for i in range(feat_dim):
                x2 = x.copy()
                if x2.ndim == 1:
                    x2[i] += eps
                else:
                    x2[..., i] += eps
                val = np.asarray(model(x2)).sum()
                grads[i] = (val - base) / eps

            arr = np.abs(grads)

        # Aggregate saliency per feature
        if feature_names:
            if len(feature_names) != arr.shape[-1]:
                raise ValueError("feature_names length doesn't match input features")
            return {n: float(arr[..., idx].sum()) for idx, n in enumerate(feature_names)}

        # return index->saliency mapping
        return {str(i): float(arr[..., i].sum()) for i in range(arr.shape[-1])}


# ============================================================================
# Singleton Factory Pattern - Lazy Initialization
# ============================================================================

_explanation_builder_singleton: Optional[ExplanationBuilder] = None


def get_explanation_builder() -> ExplanationBuilder:
    """Get or create the singleton ExplanationBuilder instance.
    
    This function implements lazy initialization following the J.A.R.V.I.S.
    pattern for stateful services. The builder is initialized on first call
    and reused for all subsequent requests.
    
    Returns:
        Initialized ExplanationBuilder singleton
    """
    global _explanation_builder_singleton
    if _explanation_builder_singleton is None:
        _explanation_builder_singleton = ExplanationBuilder()
        logger.info("ExplanationBuilder singleton initialized")
    return _explanation_builder_singleton


__all__.append("DashExplanationBuilder")
__all__.extend(["get_explanation_builder"])
