from copy import deepcopy
from test_edgar import fixture_client
from claimcheck.check_json import check_document

ISSUERS = {"meta": {"ticker": "META", "cik": "1326801", "market": "US"}}
DOC = {"schema_version": "sec-proposals-v1", "claims": [{"id": "revenue", "issuer_key": "meta", "ticker": "META", "cik": "1326801", "metric": "revenue", "period": "2025Q2", "unit": "USD", "value": 47_516_000_000}]}


def test_correct_and_wrong_value(tmp_path):
    client = fixture_client(tmp_path)
    assert check_document(DOC, ISSUERS, client)["results"][0]["status"] == "verified"
    doc = deepcopy(DOC)
    doc["claims"][0]["value"] = 47516
    result = check_document(doc, ISSUERS, client)
    assert result["results"][0]["status"] == "corrected"
    assert "47,516,000,000 USD" in result["publishable_statements"][0]


def test_identity_and_unit_are_not_corrected(tmp_path):
    client = fixture_client(tmp_path)
    for patch in ({"cik": "773840"}, {"ticker": "HON"}, {"issuer_key": "7769"}, {"unit": "TWD"}, {"value": True}, {"period": "2030Q1"}):
        doc = deepcopy(DOC)
        doc["claims"][0].update(patch)
        result = check_document(doc, ISSUERS, client)
        assert result["results"][0]["status"] == "omitted"
        assert result["publishable_statements"] == []


def test_pause_does_no_lookup_and_does_not_pass_claims():
    class NoLookup:
        class policy:
            @staticmethod
            def to_dict(): return {}
        def resolve_ticker(self, ticker): raise AssertionError("paused lookup")
    result = check_document(DOC, ISSUERS, NoLookup(), enabled=False)
    assert result["enabled"] is False
    assert result["results"][0]["reason"] == "verification_paused"
    assert not result["publishable_statements"]


def test_no_arbitrary_prose_echo(tmp_path):
    doc = deepcopy(DOC)
    doc["claims"][0]["text"] = "Guaranteed 300% stock gain because of AI"
    result = check_document(doc, ISSUERS, fixture_client(tmp_path))
    assert "Guaranteed" not in str(result)


def test_normalized_and_latest_period(tmp_path):
    for period in (" 2025q2 ", "latest"):
        doc = deepcopy(DOC)
        doc["claims"][0].update(period=period, metric=" REVENUE ")
        result = check_document(doc, ISSUERS, fixture_client(tmp_path))
        row = result["results"][0]
        assert row["status"] in ("verified", "corrected")
        assert "latest" not in row["statement"]
        assert row["evidence"]["period"] in row["statement"]


def test_malformed_issuer_is_omitted(tmp_path):
    doc = deepcopy(DOC)
    doc["claims"][0]["issuer_key"] = []
    assert check_document(doc, ISSUERS, fixture_client(tmp_path))["results"][0]["reason"] == "untrusted_issuer"


def test_mislabeled_cache_payload_is_not_issuer_evidence(tmp_path):
    import json
    client = fixture_client(tmp_path)
    path = tmp_path / "companyfacts-CIK0001326801.json"
    document = json.loads(path.read_text())
    document["cik"] = 773840
    path.write_text(json.dumps(document))
    result = check_document(DOC, ISSUERS, client)
    assert result["results"][0]["reason"] == "companyfacts_identity_mismatch"
    assert not result["publishable_statements"]
