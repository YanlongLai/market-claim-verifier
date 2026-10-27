"""Provider adapters for the Meta Responses API and Baseten Chat Completions.

The evidence loop deliberately knows as little as possible about either API.
This module owns request shapes, response parsing, and the small amount of
provider-specific accounting needed by the ledger and trace recorder.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .tools import TOOL_DEFINITIONS


META_PROVIDER = "meta"
BASETEN_PROVIDER = "baseten"
PROVIDERS = (META_PROVIDER, BASETEN_PROVIDER)
DEFAULT_PROVIDER = META_PROVIDER
META_DEFAULT_MODEL = "muse-spark-1.3"
BASETEN_DEFAULT_MODEL = "meta-models/muse-spark-open-1026"
BASETEN_BASE_URL = "https://inference.baseten.co/v1"
META_BASE_URL = "https://api.meta.ai/v1"


class ProviderError(ValueError):
    """Raised for an unknown provider or an invalid provider response."""


def normalize_provider(value: str | None) -> str:
    provider = str(value or DEFAULT_PROVIDER).strip().lower()
    if provider not in PROVIDERS:
        raise ProviderError(f"provider must be one of: {', '.join(PROVIDERS)}")
    return provider


def system_parts(system: str) -> tuple[str, str]:
    """Return ``(method, provider)`` for canonical and legacy system names."""

    raw = str(system).strip()
    if "@" in raw:
        method, provider = raw.split("@", 1)
        provider = normalize_provider(provider)
    else:
        method, provider = raw, META_PROVIDER
    if method not in {"single_shot", "agent"}:
        raise ProviderError(f"unknown evaluation method: {method}")
    return method, provider


def canonical_system(system: str, *, provider: str | None = None) -> str:
    method, parsed_provider = system_parts(system)
    return f"{method}@{normalize_provider(provider) if provider else parsed_provider}"


def default_model(provider: str) -> str:
    provider = normalize_provider(provider)
    return BASETEN_DEFAULT_MODEL if provider == BASETEN_PROVIDER else META_DEFAULT_MODEL


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if value is None:
        return None
    dumper = getattr(value, "model_dump", None)
    if callable(dumper):
        try:
            dumped = dumper()
            if isinstance(dumped, Mapping):
                return dumped
        except Exception:
            pass
    return None


def _model_dump(value: Any) -> Any:
    """Serialize SDK objects, retaining model-extra reasoning fields."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _model_dump(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_model_dump(item) for item in value]
    dumper = getattr(value, "model_dump", None)
    if callable(dumper):
        try:
            dumped = _model_dump(dumper())
            if isinstance(dumped, dict):
                extras = getattr(value, "model_extra", None)
                if isinstance(extras, Mapping):
                    for key, item in extras.items():
                        dumped.setdefault(str(key), _model_dump(item))
                for key in ("reasoning_content",):
                    extra_value = getattr(value, key, None)
                    if extra_value is not None:
                        dumped[key] = _model_dump(extra_value)
                return dumped
            return dumped
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        return {str(key): _model_dump(item) for key, item in vars(value).items()}
    return str(value)


def _as_int(value: Any) -> int:
    try:
        if isinstance(value, bool):
            return 0
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        chunks: list[str] = []
        for item in value:
            text = _get(item, "text")
            if text is None:
                text = _get(item, "content")
            if isinstance(text, str):
                chunks.append(text)
        return "".join(chunks)
    return "" if value is None else str(value)


def _rate_limit_headers(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if hasattr(headers, "items"):
        items = headers.items()
    else:
        return {}
    result: dict[str, str] = {}
    for key, value in items:
        lowered = str(key).lower()
        if lowered.startswith("x-ratelimit-"):
            result[lowered] = str(value)
    return result


def chat_tool_definitions() -> list[dict[str, Any]]:
    """Convert Responses function definitions to nested Chat Completions form."""

    converted: list[dict[str, Any]] = []
    for definition in TOOL_DEFINITIONS:
        converted.append(
            {
                "type": "function",
                "function": {
                    "name": definition["name"],
                    "description": definition.get("description", ""),
                    "parameters": copy.deepcopy(definition.get("parameters", {})),
                },
            }
        )
    return converted


def _verdict_schema_text() -> str:
    from .agent import VERDICT_SCHEMA

    return json.dumps(VERDICT_SCHEMA, ensure_ascii=False, separators=(",", ":"))


def baseten_tool_loop_instructions() -> str:
    from .agent import SYSTEM_INSTRUCTIONS

    return SYSTEM_INSTRUCTIONS


def baseten_final_verdict_prompt() -> str:
    return (
        "Return only one plain JSON object for the final verdict. Do not use "
        "Markdown fences or explanatory text. Include every atomic factual "
        "assertion as a sub-claim, including claim_type other when the tools "
        "cannot check it. Copy stated_text verbatim from the claim and include "
        "claim_type, comparator, stated_value in base units, evidence_ids, "
        "verdict, model_found_value, and a concise note. The object must match "
        "this existing verdict schema: "
        + _verdict_schema_text()
    )


def baseten_repair_prompt() -> str:
    return (
        "The previous response was not valid JSON matching the required verdict "
        "schema. Repair it now. Return only the JSON object, without Markdown "
        "fences or any explanation. Use this schema exactly: "
        + _verdict_schema_text()
    )


def baseten_single_shot_instructions(today: str) -> str:
    return (
        "Judge the user's financial claim without tools and return only one "
        "plain JSON object. Do not use Markdown fences or explanatory text. "
        "Decompose the claim into every atomic factual assertion. Use only what "
        "you already know; use claim_type other, an empty evidence_ids list, "
        "model_found_value null, and insufficient_evidence when an assertion is "
        f"not established. Today's date is {today}. The object must match this "
        "verdict schema: "
        + _verdict_schema_text()
    )


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass
class ParsedResponse:
    raw: Any
    raw_response: Any
    response_id: str | None
    status: str
    incomplete_reason: Any
    finish_reason: str | None
    text: str
    tool_calls: list[ToolCall]
    usage: dict[str, Any] | None
    normalized_usage: dict[str, int]
    raw_usage: Any
    rate_limit_headers: dict[str, str]
    assistant_message: dict[str, Any] | None = None
    output_items: list[Any] | None = None


def _common_usage(
    *, input_tokens: Any, output_tokens: Any, cached_tokens: Any = 0, reasoning_tokens: Any = 0
) -> tuple[dict[str, Any], dict[str, int]]:
    normalized = {
        "input": _as_int(input_tokens),
        "cached": min(_as_int(input_tokens), _as_int(cached_tokens)),
        "output": _as_int(output_tokens),
        "reasoning": _as_int(reasoning_tokens),
    }
    ledger_usage = {
        "input_tokens": normalized["input"],
        "output_tokens": normalized["output"],
        "input_tokens_details": {"cached_tokens": normalized["cached"]},
        "output_tokens_details": {"reasoning_tokens": normalized["reasoning"]},
    }
    return ledger_usage, normalized


def normalize_usage(raw_usage: Any) -> dict[str, int]:
    """Normalize Chat Completions usage to input/cached/output/reasoning."""

    value = _model_dump(raw_usage)
    mapping = value if isinstance(value, Mapping) else {}
    prompt_tokens = _get(mapping, "prompt_tokens", _get(mapping, "input_tokens", 0))
    completion_tokens = _get(mapping, "completion_tokens", _get(mapping, "output_tokens", 0))
    prompt_details = _get(mapping, "prompt_tokens_details", {})
    completion_details = _get(mapping, "completion_tokens_details", {})
    _, normalized = _common_usage(
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        cached_tokens=_get(prompt_details, "cached_tokens", _get(mapping, "cached", 0)),
        reasoning_tokens=_get(
            completion_details,
            "reasoning_tokens",
            _get(mapping, "reasoning", 0),
        ),
    )
    return normalized


class ProviderAdapter:
    """Small common interface consumed by the agent and evaluator."""

    name = ""
    default_model = ""
    base_url = ""
    chat_completions = False

    def initial_request(
        self, claim: str, model: str, *, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        raise NotImplementedError

    def continuation_request(
        self,
        payload: Mapping[str, Any],
        response: ParsedResponse,
        tool_results: Sequence[Mapping[str, Any]],
        *,
        model: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def final_request(
        self,
        payload: Mapping[str, Any],
        response: ParsedResponse,
        *,
        model: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def repair_request(
        self,
        payload: Mapping[str, Any],
        response: ParsedResponse,
        *,
        model: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def single_shot_request(
        self,
        claim: str,
        model: str,
        *,
        today: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def call(self, client: Any, payload: Mapping[str, Any]) -> ParsedResponse:
        raise NotImplementedError

    def fallback_request(
        self,
        payload: Mapping[str, Any],
        conversation: Sequence[Mapping[str, Any]],
        *,
        model: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        """Build a request that does not depend on provider response state."""

        return dict(payload)

    def tool_result_records(
        self, response: ParsedResponse, results: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        return [dict(result) for result in results]


class MetaProvider(ProviderAdapter):
    name = META_PROVIDER
    default_model = META_DEFAULT_MODEL
    base_url = META_BASE_URL

    def initial_request(self, claim: str, model: str, *, max_output_tokens: int, reasoning_effort: str | None) -> dict[str, Any]:
        from .agent import initial_request

        return initial_request(
            claim,
            model,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )

    def continuation_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, tool_results: Sequence[Mapping[str, Any]], *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        next_payload: dict[str, Any] = {
            "model": model,
            "previous_response_id": response.response_id,
            "input": [
                {
                    "type": "function_call_output",
                    "call_id": result.get("call_id"),
                    "output": json.dumps(result.get("result"), ensure_ascii=False, separators=(",", ":")),
                }
                for result in tool_results
            ],
            "tools": TOOL_DEFINITIONS,
            "parallel_tool_calls": True,
            "max_output_tokens": max_output_tokens,
        }
        if reasoning_effort:
            next_payload["reasoning"] = {"effort": reasoning_effort}
        return next_payload

    def final_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        from .agent import AGENT_FINAL_VERDICT_PROMPT, verdict_text_format

        final_payload: dict[str, Any] = {
            "model": model,
            "previous_response_id": response.response_id,
            "input": [{"role": "user", "content": AGENT_FINAL_VERDICT_PROMPT}],
            "text": verdict_text_format(),
            "max_output_tokens": max_output_tokens,
        }
        if reasoning_effort:
            final_payload["reasoning"] = {"effort": reasoning_effort}
        return final_payload

    def fallback_request(
        self,
        payload: Mapping[str, Any],
        conversation: Sequence[Mapping[str, Any]],
        *,
        model: str,
        max_output_tokens: int,
        reasoning_effort: str | None,
    ) -> dict[str, Any]:
        fallback_payload = copy.deepcopy(dict(payload))
        fallback_payload.pop("previous_response_id", None)
        fallback_payload["input"] = copy.deepcopy(list(conversation))
        # A previous-response continuation normally inherits the initial
        # instructions from the server-side response.  A standalone replay
        # does not, so carry them explicitly with the fallback request.
        if "instructions" not in fallback_payload:
            from .agent import SYSTEM_INSTRUCTIONS

            fallback_payload["instructions"] = SYSTEM_INSTRUCTIONS
        return fallback_payload

    def repair_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        return self.final_request(payload, response, model=model, max_output_tokens=max_output_tokens, reasoning_effort=reasoning_effort)

    def single_shot_request(
        self, claim: str, model: str, *, today: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        from .evaluate import single_shot_request

        return single_shot_request(
            claim,
            model,
            today=today,
            max_output_tokens=max_output_tokens,
            reasoning_effort=reasoning_effort,
        )

    def call(self, client: Any, payload: Mapping[str, Any]) -> ParsedResponse:
        response = client.responses.create(**dict(payload))
        from .agent import _function_calls, _incomplete_reason, _response_status, _response_text, _usage_dict

        usage = _usage_dict(response)
        normalized = _usage_buckets_from_ledger(usage)
        output_items = _model_dump(_get(response, "output", []))
        if not isinstance(output_items, list):
            output_items = [output_items]
        calls = [
            ToolCall(
                call_id=str(_get(item, "call_id") or _get(item, "id") or ""),
                name=str(_get(item, "name") or ""),
                arguments=_arguments_string(_get(item, "arguments", {})),
            )
            for item in _function_calls(response)
        ]
        status = _response_status(response)
        return ParsedResponse(
            raw=response,
            raw_response=response,
            response_id=str(_get(response, "id")) if _get(response, "id") is not None else None,
            status=status,
            incomplete_reason=_incomplete_reason(response),
            finish_reason=None,
            text=_response_text(response),
            tool_calls=calls,
            usage=usage,
            normalized_usage=normalized,
            raw_usage=_model_dump(_get(response, "usage")),
            rate_limit_headers={},
            output_items=output_items,
        )


def _arguments_string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _usage_buckets_from_ledger(usage: Any) -> dict[str, int]:
    if not isinstance(usage, Mapping):
        return {"input": 0, "cached": 0, "output": 0, "reasoning": 0}
    input_tokens = _as_int(usage.get("input_tokens"))
    details = usage.get("input_tokens_details")
    output_details = usage.get("output_tokens_details")
    return {
        "input": input_tokens,
        "cached": min(input_tokens, _as_int(_get(details, "cached_tokens", 0))),
        "output": _as_int(usage.get("output_tokens")),
        "reasoning": _as_int(_get(output_details, "reasoning_tokens", 0)),
    }


class BasetenProvider(ProviderAdapter):
    name = BASETEN_PROVIDER
    default_model = BASETEN_DEFAULT_MODEL
    base_url = BASETEN_BASE_URL
    chat_completions = True

    @staticmethod
    def _reasoning(payload: dict[str, Any], reasoning_effort: str | None) -> dict[str, Any]:
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        return payload

    def initial_request(self, claim: str, model: str, *, max_output_tokens: int, reasoning_effort: str | None) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": baseten_tool_loop_instructions()},
                {"role": "user", "content": claim},
            ],
            "tools": chat_tool_definitions(),
            "parallel_tool_calls": True,
            "max_tokens": max_output_tokens,
        }
        return self._reasoning(payload, reasoning_effort)

    @staticmethod
    def _assistant_message(response: ParsedResponse) -> dict[str, Any]:
        message = response.assistant_message
        if message is not None:
            return copy.deepcopy(message)
        return {"role": "assistant", "content": response.text or None}

    def _messages_with_response(
        self, payload: Mapping[str, Any], response: ParsedResponse, tool_results: Sequence[Mapping[str, Any]] = ()
    ) -> list[dict[str, Any]]:
        messages = [copy.deepcopy(item) for item in payload.get("messages", [])]
        messages.append(self._assistant_message(response))
        for result in tool_results:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": result.get("call_id"),
                    "content": json.dumps(result.get("result"), ensure_ascii=False, separators=(",", ":")),
                }
            )
        return messages

    def continuation_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, tool_results: Sequence[Mapping[str, Any]], *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        next_payload = {
            "model": model,
            "messages": self._messages_with_response(payload, response, tool_results),
            "tools": chat_tool_definitions(),
            "parallel_tool_calls": True,
            "max_tokens": max_output_tokens,
        }
        return self._reasoning(next_payload, reasoning_effort)

    def final_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        next_payload = {
            "model": model,
            "messages": self._messages_with_response(payload, response)
            + [{"role": "user", "content": baseten_final_verdict_prompt()}],
            "max_tokens": max_output_tokens,
        }
        return self._reasoning(next_payload, reasoning_effort)

    def repair_request(
        self, payload: Mapping[str, Any], response: ParsedResponse, *, model: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        next_payload = {
            "model": model,
            "messages": self._messages_with_response(payload, response)
            + [{"role": "user", "content": baseten_repair_prompt()}],
            "max_tokens": max_output_tokens,
        }
        return self._reasoning(next_payload, reasoning_effort)

    def single_shot_request(
        self, claim: str, model: str, *, today: str, max_output_tokens: int, reasoning_effort: str | None
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": baseten_single_shot_instructions(today)},
                {"role": "user", "content": claim},
            ],
            "max_tokens": max_output_tokens,
        }
        return self._reasoning(payload, reasoning_effort)

    def call(self, client: Any, payload: Mapping[str, Any]) -> ParsedResponse:
        completions = client.chat.completions
        raw_wrapper = getattr(completions, "with_raw_response", None)
        headers: dict[str, str] = {}
        if raw_wrapper is not None:
            if callable(raw_wrapper) and not hasattr(raw_wrapper, "create"):
                raw_wrapper = raw_wrapper()
            raw_result = raw_wrapper.create(**dict(payload))
            headers = _rate_limit_headers(_get(raw_result, "headers"))
            parser = getattr(raw_result, "parse", None)
            response = parser() if callable(parser) else raw_result
        else:
            response = completions.create(**dict(payload))

        choices = _get(response, "choices", []) or []
        choice = choices[0] if choices else None
        message = _get(choice, "message") if choice is not None else None
        finish_reason = _get(choice, "finish_reason") if choice is not None else None
        finish_reason = str(finish_reason) if finish_reason is not None else None
        raw_usage = _model_dump(_get(response, "usage"))
        raw_usage_mapping = raw_usage if isinstance(raw_usage, Mapping) else {}
        prompt_tokens = _get(raw_usage_mapping, "prompt_tokens", _get(raw_usage_mapping, "input_tokens", 0))
        completion_tokens = _get(raw_usage_mapping, "completion_tokens", _get(raw_usage_mapping, "output_tokens", 0))
        prompt_details = _get(raw_usage_mapping, "prompt_tokens_details", {})
        completion_details = _get(raw_usage_mapping, "completion_tokens_details", {})
        cached_tokens = _get(prompt_details, "cached_tokens", 0)
        reasoning_tokens = _get(completion_details, "reasoning_tokens", 0)
        ledger_usage, normalized = _common_usage(
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )
        tool_calls: list[ToolCall] = []
        raw_tool_calls = _get(message, "tool_calls", []) or []
        for item in raw_tool_calls:
            function = _get(item, "function")
            tool_calls.append(
                ToolCall(
                    call_id=str(_get(item, "id") or ""),
                    name=str(_get(function, "name") or ""),
                    arguments=_arguments_string(_get(function, "arguments", {})),
                )
            )
        content = _text_content(_get(message, "content")) if message is not None else ""
        assistant_message: dict[str, Any] | None = None
        if message is not None:
            assistant_message = {"role": "assistant", "content": _get(message, "content")}
            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": item.call_id,
                        "type": "function",
                        "function": {"name": item.name, "arguments": item.arguments},
                    }
                    for item in tool_calls
                ]
        status = str(_get(response, "status") or "completed")
        incomplete_reason = _get(_get(response, "incomplete_details"), "reason")
        if finish_reason == "length":
            status = "incomplete"
            incomplete_reason = incomplete_reason or "max_output_tokens"
        raw_dump = _model_dump(response)
        if isinstance(raw_dump, dict) and assistant_message is not None:
            # Preserve reasoning content even when an SDK model keeps it in
            # ``model_extra`` and omits it from its default dump.
            reasoning_content = _get(message, "reasoning_content")
            if reasoning_content is None:
                extras = _get(message, "model_extra")
                reasoning_content = _get(extras, "reasoning_content")
            choices_dump = raw_dump.get("choices")
            if reasoning_content is not None and isinstance(choices_dump, list) and choices_dump:
                message_dump = choices_dump[0].get("message") if isinstance(choices_dump[0], dict) else None
                if isinstance(message_dump, dict):
                    message_dump["reasoning_content"] = _model_dump(reasoning_content)
        return ParsedResponse(
            raw=response,
            raw_response=raw_dump,
            response_id=str(_get(response, "id")) if _get(response, "id") is not None else None,
            status=status,
            incomplete_reason=incomplete_reason,
            finish_reason=finish_reason,
            text=content,
            tool_calls=tool_calls,
            usage=ledger_usage,
            normalized_usage=normalized,
            raw_usage=raw_usage,
            rate_limit_headers=headers,
            assistant_message=assistant_message,
        )


META = MetaProvider()
BASETEN = BasetenProvider()
_PROVIDER_INSTANCES = {META_PROVIDER: META, BASETEN_PROVIDER: BASETEN}


def get_provider(value: str | ProviderAdapter | None = None) -> ProviderAdapter:
    if isinstance(value, ProviderAdapter):
        return value
    if value is not None and hasattr(value, "name") and hasattr(value, "call"):
        return value  # type: ignore[return-value]
    name = normalize_provider(value if isinstance(value, str) else None)
    return _PROVIDER_INSTANCES[name]


def create_client(provider: str, api_key: str) -> Any:
    from openai import OpenAI

    adapter = get_provider(provider)
    return OpenAI(base_url=adapter.base_url, api_key=api_key)


def _raw_response_for_trace(parsed: ParsedResponse) -> Any:
    return parsed.raw_response


# Short aliases keep the public adapter surface convenient for callers that do
# not need to distinguish the implementation class name from the concept.
Provider = ProviderAdapter
provider_for = get_provider


__all__ = [
    "BASETEN",
    "BASETEN_BASE_URL",
    "BASETEN_DEFAULT_MODEL",
    "BASETEN_PROVIDER",
    "META",
    "META_BASE_URL",
    "META_DEFAULT_MODEL",
    "META_PROVIDER",
    "PROVIDERS",
    "ProviderAdapter",
    "Provider",
    "ProviderError",
    "ParsedResponse",
    "ToolCall",
    "baseten_final_verdict_prompt",
    "baseten_repair_prompt",
    "baseten_single_shot_instructions",
    "baseten_tool_loop_instructions",
    "canonical_system",
    "chat_tool_definitions",
    "create_client",
    "default_model",
    "get_provider",
    "provider_for",
    "normalize_provider",
    "normalize_usage",
    "system_parts",
]
