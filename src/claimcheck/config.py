"""Environment-backed settings for claimcheck.

The model key is deliberately kept out of the settings representation used by
traces.  This module is the only place that reads the optional key file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .providers import (
    BASETEN_DEFAULT_MODEL,
    BASETEN_PROVIDER,
    DEFAULT_PROVIDER,
    META_DEFAULT_MODEL,
    ProviderError,
    normalize_provider,
)


DEFAULT_MODEL = META_DEFAULT_MODEL
DEFAULT_BUDGET_USD = 0.50
DEFAULT_SEC_USER_AGENT = "DappGo market-claim-verifier admin@dappgo.com"
DEFAULT_MODEL_API_KEY_FILE = Path("~/.config/dappgo/meta-model-api.env").expanduser()
DEFAULT_BASETEN_API_KEY_FILE = Path("~/secret/baseten_api_key.txt").expanduser()


class SettingsError(ValueError):
    """Raised when an environment setting cannot be parsed."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings.

    ``model_api_key`` is never included in request or trace payloads.  It is
    kept here only long enough for the OpenAI-compatible client constructor.
    """

    model_api_key: str | None = field(repr=False)
    model: str
    budget_usd: float
    sec_user_agent: str
    cache_dir: Path
    runs_dir: Path
    model_api_key_file: Path
    max_output_tokens: int | None = None
    reasoning_effort: str | None = None
    provider: str = DEFAULT_PROVIDER
    baseten_api_key_file: Path = DEFAULT_BASETEN_API_KEY_FILE


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


def _key_from_raw_file(path: Path) -> str | None:
    """Read a raw key file without interpreting dotenv assignments."""

    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    return value or None


def _path_setting(raw: str | None, default: str) -> Path:
    return Path(raw or default).expanduser()


def _optional_positive_int(raw: str | None, name: str) -> int | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise SettingsError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise SettingsError(f"{name} must be a positive integer")
    return value


def load_settings(
    environ: Mapping[str, str] | None = None,
    *,
    read_key: bool = True,
    provider: str | None = None,
) -> Settings:
    """Load settings from environment variables and the optional key file."""

    env = os.environ if environ is None else environ
    try:
        selected_provider = normalize_provider(provider or env.get("CLAIMCHECK_PROVIDER", DEFAULT_PROVIDER))
    except ProviderError as exc:
        raise SettingsError(str(exc)) from exc
    key_file = _path_setting(
        env.get("MODEL_API_KEY_FILE"), str(DEFAULT_MODEL_API_KEY_FILE)
    )
    baseten_key_file = _path_setting(
        env.get("BASETEN_API_KEY_FILE"), str(DEFAULT_BASETEN_API_KEY_FILE)
    )
    api_key: str | None
    if selected_provider == BASETEN_PROVIDER:
        api_key = env.get("BASETEN_API_KEY") or None
        if api_key is None and read_key:
            api_key = _key_from_raw_file(baseten_key_file)
    else:
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

    max_output_tokens = _optional_positive_int(
        env.get("CLAIMCHECK_MAX_OUTPUT_TOKENS"),
        "CLAIMCHECK_MAX_OUTPUT_TOKENS",
    )

    configured_model = env.get("CLAIMCHECK_MODEL")
    if not configured_model:
        configured_model = BASETEN_DEFAULT_MODEL if selected_provider == BASETEN_PROVIDER else META_DEFAULT_MODEL

    return Settings(
        provider=selected_provider,
        model_api_key=api_key,
        model=configured_model,
        budget_usd=budget,
        sec_user_agent=env.get("SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT),
        cache_dir=_path_setting(env.get("CLAIMCHECK_CACHE_DIR"), ".cache"),
        runs_dir=_path_setting(env.get("CLAIMCHECK_RUNS_DIR"), "runs"),
        model_api_key_file=key_file,
        baseten_api_key_file=baseten_key_file,
        max_output_tokens=max_output_tokens,
        reasoning_effort=env.get("CLAIMCHECK_REASONING_EFFORT") or None,
    )
