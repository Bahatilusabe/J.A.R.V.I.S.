"""CED explanation visualizer using Dash with optional MindInsight support.

This script launches a small Dash web app to browse and inspect CED
explanations provided in a JSON file. The app is lightweight and designed
for ModelArts Notebook or local development. If `dash`/`plotly` are not
available, a minimal HTTP fallback prints the JSON.

MindInsight integration: when `mindinsight` is importable, the script exposes
an `export_for_mindinsight` helper that writes a summary JSON into a
`mindinsight_workspace/ced_exports` directory (user can configure the exact
workspace path). This is a non-invasive integration so the visualizer
remains functional even without MindInsight.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("xai_visualizer")
logging.basicConfig(level=logging.INFO)


def try_import_dash():
	try:
		import dash
		import dash_core_components as dcc
		import dash_html_components as html
		import plotly.graph_objs as go

		return dash, dcc, html, go
	except Exception:
		return None, None, None, None


def try_import_mindinsight():
	try:
		import mindinsight  # type: ignore

		return mindinsight
	except Exception:
		return None


dash, dcc, html, go = try_import_dash()
mindinsight = try_import_mindinsight()


def load_ced_json(path: Path) -> List[Dict[str, Any]]:
	with path.open("r", encoding="utf-8") as fh:
		data = json.load(fh)
	# Accept either a list or a dict with 'items' key
	if isinstance(data, dict) and "items" in data:
		items = data["items"]
	elif isinstance(data, list):
		items = data
	else:
		# try to coerce single dict into list
		items = [data]
	return items


def export_for_mindinsight(items: List[Dict[str, Any]], workspace_dir: Optional[Path] = None) -> Path:
	"""Export a compact summary suitable for ingestion by MindInsight.

	This creates a timestamped directory under `workspace_dir` (or
	~/.mindinsight/ced_exports by default) containing a JSON summary and
	per-item files. This is intentionally simple; users running MindInsight
	can configure their workspace to point at the export directory.
	"""
	if workspace_dir is None:
		home = Path.home()
		workspace_dir = home / ".mindinsight" / "ced_exports"
	workspace_dir.mkdir(parents=True, exist_ok=True)
	ts = int(time.time())
	out_dir = workspace_dir / f"ced_{ts}"
	out_dir.mkdir(parents=True, exist_ok=True)
	summary = {"count": len(items), "timestamp": ts}
	for i, it in enumerate(items):
		p = out_dir / f"item_{i}.json"
		with p.open("w", encoding="utf-8") as fh:
			json.dump(it, fh, indent=2)
	with (out_dir / "summary.json").open("w", encoding="utf-8") as fh:
		json.dump(summary, fh, indent=2)
	logger.info("Exported %d CED items to %s for MindInsight", len(items), out_dir)
	return out_dir


def run_minimal_http_fallback(items: List[Dict[str, Any]], host: str, port: int):
	# Simple fallback: print the first item and start a tiny socket server that
	# returns the JSON on GET /. This keeps the UX usable without Dash.
	import json

	data = json.dumps(items, indent=2)

	def handle_client(conn):
		try:
			req = conn.recv(1024).decode("utf-8", errors="ignore")
			# very naive GET detection
			if req.startswith("GET"):
				resp = (
					"HTTP/1.1 200 OK\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
					+ data
				)
				conn.sendall(resp.encode("utf-8"))
		finally:
			conn.close()

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((host, port))
	s.listen(1)
	logger.info("Dash not available; started minimal HTTP fallback at http://%s:%d/", host, port)
	try:
		while True:
			conn, _ = s.accept()
			handle_client(conn)
	except KeyboardInterrupt:
		logger.info("Shutting down fallback server")
	finally:
		s.close()


def build_dash_app(items: List[Dict[str, Any]], host: str, port: int):
	"""Build and run a Dash app to visualize the CED items.

	The function constructs a simple dashboard with:
	 - Dropdown to select item
	 - Bar chart of token importances (if available)
	 - Raw JSON viewer
	"""
	if dash is None:
		raise RuntimeError("dash is not available")

	app = dash.Dash(__name__)

	# prepare options
	opts = []
	for i, it in enumerate(items):
		title = it.get("id") or it.get("title") or f"item_{i}"
		opts.append({"label": title, "value": i})

	def get_token_importances(item: Dict[str, Any]):
		# expected shape: item['explanation'] -> list of { 'token': str, 'importance': float }
		expl = item.get("explanation") or item.get("ced_explanation") or []
		tokens = []
		vals = []
		if isinstance(expl, list):
			for part in expl:
				if isinstance(part, dict) and "token" in part and "importance" in part:
					tokens.append(part["token"])
					vals.append(part["importance"])
		# fallback: if item has 'importances' dict
		if not tokens and isinstance(item.get("importances"), dict):
			for t, v in item["importances"].items():
				tokens.append(t)
				vals.append(float(v))
		return tokens, vals

	# Additional visualizations: timeline, heatmap, metrics
	app.layout = html.Div(
		[
			html.H2("CED Explanations Viewer"),
			html.Div(
				[
					dcc.Dropdown(id="item-select", options=opts, value=0, style={"width": "50%"}),
					html.Div(id="metrics-box", style={"display": "inline-block", "marginLeft": "20px"}),
				],
				style={"display": "flex", "alignItems": "center"},
			),
			html.Div(
				[
					dcc.Graph(id="importance-bar", style={"width": "48%", "display": "inline-block"}),
					dcc.Graph(id="timeline", style={"width": "48%", "display": "inline-block"}),
				]
			),
			html.H4("Aggregate Heatmap (tokens x items)"),
			dcc.Graph(id="heatmap"),
			html.H4("Raw JSON"),
			html.Pre(id="raw-json", style={"whiteSpace": "pre-wrap", "maxHeight": "400px", "overflow": "auto"}),
		],
		style={"margin": "12px"},
	)

	@app.callback(
		dash.dependencies.Output("importance-bar", "figure"),
		[dash.dependencies.Input("item-select", "value")],
	)
	def update_bar(idx):
		item = items[int(idx)]
		tokens, vals = get_token_importances(item)
		if not tokens:
			# show a placeholder
			fig = go.Figure()
			fig.add_trace(go.Bar(x=["no_importances"], y=[0]))
			return fig
		fig = go.Figure([go.Bar(x=tokens, y=vals)])
		fig.update_layout(title_text=item.get("id") or item.get("title") or "item")
		return fig

	@app.callback(dash.dependencies.Output("raw-json", "children"), [dash.dependencies.Input("item-select", "value")])
	def update_json(idx):
		item = items[int(idx)]
		return json.dumps(item, indent=2)


	@app.callback(
		dash.dependencies.Output("timeline", "figure"),
		[dash.dependencies.Input("item-select", "value")],
	)
	def update_timeline(_idx):
		# Build a simple timeline across items by timestamp or index; if items
		# have `score` or `importance_sum` show it over the list.
		xs = []
		ys = []
		labels = []
		for it in items:
			ts = it.get("timestamp") or it.get("time") or None
			if ts is None:
				xs.append(None)
			else:
				xs.append(ts)
			# derive a simple score: sum(abs(importances)) or 'score' field
			if isinstance(it.get("importances"), dict):
				ys.append(sum(abs(float(v)) for v in it.get("importances").values()))
			elif isinstance(it.get("explanation"), list):
				ys.append(sum(abs(float(part.get("importance", 0.0))) for part in it.get("explanation")))
			else:
				ys.append(float(it.get("score", 0.0)))
			labels.append(it.get("id") or it.get("title", ""))
		# normalize x to indices if timestamps missing
		if all(x is None for x in xs):
			xs = list(range(len(items)))
		fig = go.Figure()
		fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", text=labels))
		fig.update_layout(title_text="Aggregate importance timeline", xaxis_title="item")
		return fig


	@app.callback(
		dash.dependencies.Output("heatmap", "figure"),
		[dash.dependencies.Input("item-select", "value")],
	)
	def update_heatmap(_idx):
		# Build token x item matrix. Collect top-K tokens across items.
		token_set = {}
		rows = []
		for i, it in enumerate(items):
			tokens, vals = get_token_importances(it)
			rows.append((tokens, vals))
			for j, t in enumerate(tokens):
				token_set[t] = token_set.get(t, 0) + abs(vals[j]) if j < len(vals) else token_set.get(t, 0)
		# pick top tokens
		top_tokens = [t for t, _ in sorted(token_set.items(), key=lambda kv: -kv[1])][:50]
		z = []
		for tokens, vals in rows:
			row_map = {t: float(v) for t, v in zip(tokens, vals)}
			z.append([row_map.get(t, 0.0) for t in top_tokens])
		if not top_tokens:
			fig = go.Figure()
			fig.add_trace(go.Heatmap(z=[[0]], x=["no_tokens"], y=["no_items"]))
			return fig
		fig = go.Figure(data=go.Heatmap(z=z, x=top_tokens, y=[it.get("id") or f"item_{i}" for i, it in enumerate(items)]))
		fig.update_layout(title_text="Token importances heatmap (tokens x items)")
		return fig

	logger.info("Starting Dash app at http://%s:%d/", host, port)
	app.run_server(host=host, port=port, debug=False)


def main():
	parser = argparse.ArgumentParser(description="CED Explanation Visualizer (Dash + MindInsight helper)")
	parser.add_argument("--input", required=True, help="Path to CED explanations JSON file")
	parser.add_argument("--host", default="127.0.0.1", help="Host to bind the web app")
	parser.add_argument("--port", type=int, default=8050, help="Port to bind the web app")
	parser.add_argument("--mindinsight-export", action="store_true", help="Export items for MindInsight (if available)")
	args = parser.parse_args()

	path = Path(args.input)
	if not path.exists():
		logger.error("Input file does not exist: %s", path)
		sys.exit(2)

	items = load_ced_json(path)

	if args.mindinsight_export:
		if mindinsight is not None:
			export_for_mindinsight(items)
		else:
			logger.warning("MindInsight not available; skipping export")

	if dash is not None:
		try:
			build_dash_app(items, host=args.host, port=args.port)
		except Exception:
			logger.exception("Dash app failed; falling back to minimal HTTP server")
			run_minimal_http_fallback(items, host=args.host, port=args.port)
	else:
		logger.warning("Dash not installed; running minimal HTTP fallback")
		run_minimal_http_fallback(items, host=args.host, port=args.port)


if __name__ == "__main__":
	main()

