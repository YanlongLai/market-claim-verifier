"""Overloaded providers are named plainly on the site log, the API and the CLI."""
from types import SimpleNamespace

import pytest

from claimcheck import cli
from claimcheck.progress import format_event, safe_fields
from claimcheck.providers import CLIENT_TIMEOUT_S, create_client
from claimcheck.retries import overloaded_exception, provider_overloaded


@pytest.mark.parametrize("status,body,expected", [
    (503, "", True), (529, "", True),
    (429, "service overloaded, please try again later", True), (502, "Model at capacity", True),
    (429, "rate limit exceeded", False), (500, "internal error", False),
    (400, "overloaded", False), (None, "overloaded", False),
])
def test_overload_rule(status, body, expected):
    assert provider_overloaded(status, body) is expected


class StatusError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status_code = status


def test_sdk_style_exception_is_classified_by_status_and_message():
    assert overloaded_exception(StatusError(503, "Error code: 503 - service overloaded"))
    assert not overloaded_exception(StatusError(401, "invalid api key"))
    assert not overloaded_exception(TimeoutError("read timed out"))


def test_progress_keeps_code_and_provider_status_only():
    fields = safe_fields("error", {"code": "provider_overloaded", "provider_status": 503,
                                   "message": "service overloaded private-account-detail"})
    assert fields == {"code": "provider_overloaded", "provider_status": 503}
    line = format_event("cli", 7.5, "error", fields)
    assert "provider_overloaded" in line and "503" in line and "private" not in line


def test_cli_names_the_overloaded_provider_and_suggests_others(capsys):
    events = []
    cli._report_provider_failure(lambda kind, fields: events.append((kind, fields)), "fireworks",
                                 StatusError(503, "service overloaded, please try again later"))
    err = capsys.readouterr().err
    assert "Fireworks is overloaded right now (HTTP 503" in err
    assert "--provider meta or --provider baseten" in err
    assert events == [("error", {"code": "provider_overloaded", "provider_status": 503})]


def test_cli_client_fails_fast_instead_of_hanging():
    client = create_client("fireworks", "test-key")
    assert client.max_retries == 0
    assert client.timeout.read == CLIENT_TIMEOUT_S == 90.0
