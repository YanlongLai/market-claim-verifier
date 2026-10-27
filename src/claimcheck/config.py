"""Environment-backed settings for claimcheck.

The model key is deliberately kept out of the settings representation used by
traces.  This module is the only place that reads the optional key file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_MODEL = "muse-spark-1.3"
DEFAULT_BUDGET_USD = 0.50
DEFAULT_SEC_USER_AGENT = "DappGo market-claim-verifier admin@dappgo.com"
DEFAULT_MODEL_API_KEY_FILE = Path("~/.config/dappgo/meta-model-api.env").expanduser()


class SettingsError(ValueError):
    """Raised when an environment setting cannot be parsed."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings.

    ``model_api_key`` is never included in request or trace payloads.  It is
    kept here only long enough for the OpenAI-compatible client constructor.
    """

    model_api_key: str | None
    model: str
    budget_usd: float
    sec_user_agent: str
    cache_dir: Path
    runs_dir: Path
    model_api_key_file: Path


def _key_from_env_file(path: Path) -> str | None:
    """Read only ``MODEL_API_KEY`` from a dotenv-like file.

    The value is returned to the caller and is never printed or persisted by
    this module.  Missing files are normal during dry runs.
    """

    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() != "MODEL_API_KEY":
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value or None
    return None


def _path_setting(raw: str | None, default: str) -> Path:
    return Path(raw or default).expanduser()


def load_settings(
    environ: Mapping[str, str] | None = None,
    *,
    read_key: bool = True,
) -> Settings:
    """Load settings from environment variables and the optional key file."""

    env = os.environ if environ is None else environ
    key_file = _path_setting(
        env.get("MODEL_API_KEY_FILE"), str(DEFAULT_MODEL_API_KEY_FILE)
    )
    api_key = env.get("MODEL_API_KEY") or None
    if api_key is None and read_key:
        api_key = _key_from_env_file(key_file)

    raw_budget = env.get("CLAIMCHECK_BUDGET_USD", str(DEFAULT_BUDGET_USD))
    try:
        budget = float(raw_budget)
    except (TypeError, ValueError) as exc:
        raise SettingsError("CLAIMCHECK_BUDGET_USD must be a number") from exc
    if budget < 0:
        raise SettingsError("CLAIMCHECK_BUDGET_USD must be non-negative")

    return Settings(
        model_api_key=api_key,
        model=env.get("CLAIMCHECK_MODEL", DEFAULT_MODEL),
        budget_usd=budget,
        sec_user_agent=env.get("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT),
        cache_dir=_path_setting(env.get("CLAIMCHECK_CACHE_DIR"), ".cache"),
        runs_dir=_path_setting(env.get("CLAIMCHECK_RUNS_DIR"), "runs"),
        model_api_key_file=key_file,
    )
