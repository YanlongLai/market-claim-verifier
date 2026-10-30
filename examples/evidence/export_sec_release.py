"""Offline META issuer-outlook evidence export; no model or network calls."""
from pathlib import Path
import argparse
import json
from claimcheck.evidence import SecReleaseConnector, export_bundle
from claimcheck.release import ReleaseService
from claimcheck.release_fetch import ReleaseClient, ReleaseError
from claimcheck.release_text import parse_html

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'tests/fixtures/releases'


class RecordedMeta:
    """This example fixes META's identity/calendar, not a general ticker resolver."""
    def resolve_ticker(self, ticker):
        if ticker != 'META':
            raise ValueError('example supports only META')
        return {'ticker': 'META', 'cik': '0001326801', 'entity': 'Meta Platforms, Inc.'}

    def fiscal_equals_calendar(self, ticker):
        return ticker == 'META'


def offline_only(url):
    raise ReleaseError('not in recorded fixture corpus; network disabled')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    client = ReleaseClient(FIXTURES, fetcher=offline_only)
    service = ReleaseService(RecordedMeta(), client)
    found = service.find('META', 'revenue', 'FY2025Q3', 'guidance')
    candidate = found['candidates'][0]
    quote = service.quote(candidate['candidate_id'], candidate['start'], candidate['end'])
    raw, metadata = client.read(quote['exhibit_url'])
    text = parse_html(raw).text
    record = SecReleaseConnector().export(quote=quote, raw=raw, text=text, metadata=metadata)
    target = export_bundle(record, raw, text, args.out)
    print(json.dumps({'record': str(target), 'record_id': record.record_id,
                      'fact': record.to_dict()['fact'], 'mode': 'offline recorded replay'}, indent=2))


if __name__ == '__main__':
    main()
