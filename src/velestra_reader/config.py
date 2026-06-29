"""Configuration loading for velestra-reader."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_CONFIG_PATH = Path("~/.config/velestra-reader/config.env")
DEFAULT_USER_AGENT = "script:velestra-reader:0.1.0 (by /u/unknown)"


@dataclass(frozen=True)
class ReaderConfig:
    auth_mode: str
    client_id: str | None
    client_secret: str | None
    access_token: str | None
    refresh_token: str | None
    user_agent: str
    cache_dir: Path


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def read_env_file(path: Path) -> dict[str, str]:
    """Read a simple KEY=VALUE file. Missing files are treated as empty config."""
    try:
        lines = path.expanduser().read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise RuntimeError(f"Failed to read config file {path}: {exc}") from exc

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise ValueError(f"Invalid config line {line_number} in {path}: expected KEY=VALUE.")

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not (key[0].isalpha() or key[0] == "_"):
            raise ValueError(f"Invalid config key on line {line_number} in {path}.")
        if not all(character.isalnum() or character == "_" for character in key):
            raise ValueError(f"Invalid config key on line {line_number} in {path}.")
        values[key] = _unquote(value.strip())
    return values


def config_path_for(environ: Mapping[str, str]) -> Path:
    explicit_path = environ.get("VELESTRA_READER_CONFIG", "").strip()
    if explicit_path:
        return Path(explicit_path).expanduser()

    xdg_config_home = environ.get("XDG_CONFIG_HOME", "").strip()
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / "velestra-reader" / "config.env"

    return DEFAULT_CONFIG_PATH.expanduser()


def load_config(
    environ: Mapping[str, str] | None = None,
    *,
    config_path: Path | None = None,
) -> ReaderConfig:
    """Load config from a per-user env file, then overlay process env values."""
    env = os.environ if environ is None else environ
    path = config_path.expanduser() if config_path is not None else config_path_for(env)
    file_values = read_env_file(path)
    values = {**file_values, **env}

    return ReaderConfig(
        auth_mode=values.get("VELESTRA_READER_AUTH", "auto").strip().lower() or "auto",
        client_id=values.get("VELESTRA_READER_CLIENT_ID", "").strip() or None,
        client_secret=values.get("VELESTRA_READER_CLIENT_SECRET", "").strip() or None,
        access_token=values.get("VELESTRA_READER_ACCESS_TOKEN", "").strip() or None,
        refresh_token=values.get("VELESTRA_READER_REFRESH_TOKEN", "").strip() or None,
        user_agent=values.get("VELESTRA_READER_USER_AGENT", DEFAULT_USER_AGENT).strip()
        or DEFAULT_USER_AGENT,
        cache_dir=Path(values.get("VELESTRA_READER_CACHE_DIR", "~/.cache/velestra-reader")).expanduser(),
    )
