# config/loader.py
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

# ---------- Path resolution ----------
def _default_cfg_path() -> Path:
    """
    Resolve to .../config/app_config.yaml regardless of current working dir.
    This file is .../config/loader.py
    """
    here = Path(__file__).resolve()        # .../config/loader.py
    config_dir = here.parent               # .../config
    return config_dir / "app_config.yaml"  # .../config/app_config.yaml

# ---------- Loaders ----------
def load_config(ENV:str,path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load YAML config. Resolution order:
      1) explicit `path` arg
      2) env APP_CONFIG_PATH
      3) default next to this file: .../config/app_config.yaml
    """
    cfg_path = Path(_default_cfg_path())#Path(path or os.getenv("APP_CONFIG_PATH") or _default_cfg_path())
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def select_env(ENV:str,cfg: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (ENV_NAME, ENV_CONFIG) using the root key `env`, e.g., 'DEV'.
    """
    env_name = ENV
    env_cfg = cfg.get(env_name, {}) or {}
    return env_name, env_cfg

def get_setting(cfg: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    """
    Safely read a nested value using a dotted path, e.g., "aws.region".
    """
    cur: Any = cfg
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur

# ---------- Optional: file resolver for data assets ----------
def resolve_project_path(*parts: str) -> Path:
    """
    Build an absolute path from project root.
    Example: resolve_project_path('system_metadata', 'insightsiq_metadata.json')
    """
    # project root is two levels up from this file (config/loader.py -> project/)
    root = Path(__file__).resolve().parent.parent
    return root.joinpath(*parts)

