"""Disk persistence for repos, projects, and workflows.

Saves metadata to %TEMP%/forgeai/metadata.json so data survives backend restarts.
"""

import json
import os
from datetime import datetime, UTC
from typing import Any


METADATA_DIR = os.path.join(os.environ.get("TEMP", "/tmp"), "forgeai")
METADATA_FILE = os.path.join(METADATA_DIR, "metadata.json")


def _ensure_dir():
    os.makedirs(METADATA_DIR, exist_ok=True)


def save_metadata(data: dict[str, Any]) -> None:
    """Save metadata dict to disk."""
    _ensure_dir()
    data["_saved_at"] = datetime.now(UTC).isoformat()
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(dir=METADATA_DIR, suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, METADATA_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_metadata() -> dict[str, Any]:
    """Load metadata dict from disk. Returns empty dict if not found."""
    if not os.path.exists(METADATA_FILE):
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_repos(repos: list[dict[str, Any]]) -> None:
    """Save repository list to disk."""
    meta = load_metadata()
    meta["repositories"] = repos
    save_metadata(meta)


def save_projects(projects: list[dict[str, Any]]) -> None:
    """Save project list to disk."""
    meta = load_metadata()
    meta["projects"] = projects
    save_metadata(meta)


def save_workflows(workflows: list[dict[str, Any]]) -> None:
    """Save workflow list to disk."""
    meta = load_metadata()
    meta["workflows"] = workflows
    save_metadata(meta)


def load_repos() -> list[dict[str, Any]]:
    return load_metadata().get("repositories", [])


def load_projects() -> list[dict[str, Any]]:
    return load_metadata().get("projects", [])


def load_workflows() -> list[dict[str, Any]]:
    return load_metadata().get("workflows", [])


def save_studio_workflows(workflows: list[dict[str, Any]]) -> None:
    """Save studio workflow list to disk."""
    meta = load_metadata()
    meta["studio_workflows"] = workflows
    save_metadata(meta)


def load_studio_workflows() -> list[dict[str, Any]]:
    return load_metadata().get("studio_workflows", [])
