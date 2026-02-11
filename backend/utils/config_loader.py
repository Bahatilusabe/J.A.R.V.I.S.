import yaml  # type: ignore[import]
from pathlib import Path

def load_config(path: str = "config/default.yaml"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    with open(p) as f:
        return yaml.safe_load(f)
