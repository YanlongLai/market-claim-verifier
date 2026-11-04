"""Malformed credentials cannot bypass lockout or escape through native forms."""
from html.parser import HTMLParser

import pytest

from test_live_password import PASSWORD, auth
from test_site_stamps_runtime import ROOT


@pytest.mark.parametrize("attempted", ["\ud800", "\udfff", "prefix-\ud800-suffix"])
def test_lone_json_surrogates_are_counted_as_failed_passwords(attempted):
    state = {}
    for _ in range(5):
        assert auth(state, attempted)[1] == 401
    assert auth(state, PASSWORD)[1] == 429
    assert next(iter(state["auth_failures"].values()))["count"] == 5


@pytest.mark.parametrize("secret", [False, 0, 12, [], {}, b"offline-only"])
def test_invalid_secret_type_fails_closed_without_persisting_anything(secret):
    state = {}
    assert auth(state, PASSWORD, secret=secret) == ({"error": "unavailable"}, 503)
    assert state == {}


def test_native_form_keeps_password_out_of_urls_if_javascript_cannot_run():
    class Elements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.by_id = {}

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            if "id" in attributes:
                self.by_id[attributes["id"]] = (tag, attributes)

    elements = Elements()
    elements.feed((ROOT / "docs/site/index.html").read_text())
    tag, form = elements.by_id["live-form"]
    assert tag == "form" and form["method"].lower() == "post"
    assert form["action"] == "/api/check"
    tag, password = elements.by_id["live-password"]
    assert tag == "input" and password["type"] == "password"
    assert password["autocomplete"] == "off"
