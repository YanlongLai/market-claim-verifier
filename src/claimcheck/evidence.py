"""Versioned evidence export contract; exports never grant verdict authority."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlsplit


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable canonical JSON; consumers receive independent copies."""
    canonical_json: str

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.canonical_json)

    @property
    def record_id(self) -> str:
        return digest(self.canonical_json.encode())


class EvidenceConnector(Protocol):
    def export(self, *, quote: dict[str, Any], raw: bytes,
               text: str, metadata: dict[str, Any]) -> EvidenceRecord: ...


class SecReleaseConnector:
    """Export an already admitted, deterministically re-extracted L4 quote.

    This is not an arbitrary document import or authentication mechanism.
    ReleaseService remains responsible for SEC index discovery and re-extraction.
    """
    version = "sec-release-v1"

    def export(self, *, quote: dict[str, Any], raw: bytes,
               text: str, metadata: dict[str, Any]) -> EvidenceRecord:
        url = quote['exhibit_url']
        parsed = urlsplit(url)
        cik = str(int(quote['cik']))
        accession = quote['accession'].replace('-', '')
        prefix = f'/Archives/edgar/data/{cik}/{accession}/'
        if (parsed.scheme != 'https' or parsed.netloc != 'www.sec.gov'
                or not parsed.path.startswith(prefix) or parsed.query or parsed.fragment):
            raise ValueError('evidence requires the admitted SEC accession URL')
        if (quote.get('form') not in {'8-K Ex 99.1', '8-K Ex 99.2'}
                or quote.get('span_verified') is not True):
            raise ValueError('evidence requires a verified release span')
        if digest(raw) != quote['sha256'] or metadata.get('sha256') != quote['sha256'] or metadata.get('url') != url:
            raise ValueError('evidence snapshot integrity mismatch')
        start, end = quote['start'], quote['end']
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or text[start:end] != quote['quote']:
            raise ValueError('evidence quote does not match normalized text')
        from .release import extract_candidates
        from .release_text import parse_html
        document = parse_html(raw)
        if document.text != text:
            raise ValueError('normalized text does not match source bytes')
        matches = [item for item in extract_candidates(
            document, quote['metric'], quote['claim_kind'], quote['period'],
            calendar=quote.get('calendar_equals_fiscal') is True)
            if item['start'] == start and item['end'] == end]
        if len(matches) != 1 or any(matches[0].get(key) != quote.get(key)
                                   for key in ('quote', 'low', 'high', 'unit', 'period', 'period_type')):
            raise ValueError('fact failed deterministic source re-extraction')
        expected_value = matches[0]['low'] if matches[0]['low'] == matches[0]['high'] else None
        if quote.get('value') != expected_value:
            raise ValueError('fact value differs from source range')
        record = {
            'schema_version': '1.0', 'connector': self.version,
            'source': {'publisher': quote['entity'], 'distributor': 'US SEC EDGAR',
                       'url': url, 'cik': quote['cik'], 'accession': quote['accession'],
                       'form': quote['form'], 'filed_on': quote['filed'],
                       'retrieved_at': metadata.get('fetched_at'),
                       'sha256': digest(raw), 'media_type': 'text/html'},
            'locator': {'kind': 'normalized_text_characters', 'start': start, 'end': end,
                        'quote': quote['quote'], 'text_sha256': digest(text.encode()),
                        'normalizer': 'claimcheck.release_text.parse_html/v1'},
            'fact': {key: quote.get(key) for key in
                     ('ticker', 'metric', 'period', 'period_type', 'unit', 'low', 'high', 'value', 'claim_kind')},
            'authority': {'scope': 'issuer_statement', 'tier': 'L4', 'audited': False,
                          'maximum_strength': 'medium', 'permitted_claim_kind': quote['claim_kind'],
                          'basis': 'SEC Item 2.02 exhibit admission and deterministic quote re-extraction'},
            'limitations': ['An issuer forecast is not proof of future performance.',
                            'Normalized text offsets are not raw HTML byte offsets.',
                            'This export does not override filing conflicts or existing verdict rules.'],
        }
        return EvidenceRecord(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False))


def export_bundle(record: EvidenceRecord, raw: bytes, text: str, directory: Path) -> Path:
    """Write content-addressed source/text/record files without overwriting history."""
    data = record.to_dict()
    if digest(raw) != data['source']['sha256'] or digest(text.encode()) != data['locator']['text_sha256']:
        raise ValueError('bundle snapshot integrity mismatch')
    directory.mkdir(parents=True, exist_ok=True)
    files = {data['source']['sha256'] + '.html': raw,
             data['locator']['text_sha256'] + '.txt': text.encode(),
             record.record_id + '.json': record.canonical_json.encode()}
    for name, content in files.items():
        path = directory / name
        try:
            with path.open('xb') as stream:
                stream.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError('existing evidence artifact was modified')
    return directory / (record.record_id + '.json')
