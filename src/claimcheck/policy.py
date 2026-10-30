"""Versioned evidence eligibility; dates are inclusive filing dates, not instants."""
from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import re
from typing import Any


def parse_as_of(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('as_of must be YYYY-MM-DD')
    date.fromisoformat(value)
    return value


@dataclass(frozen=True)
class VerificationPolicy:
    as_of: str | None = None
    version: str = 'us-financial-v1'

    def __post_init__(self):
        if self.as_of is not None:
            parse_as_of(self.as_of)
        if self.version != 'us-financial-v1':
            raise ValueError('unsupported verification policy version')

    def admits(self, filed: Any) -> bool:
        if self.as_of is None:
            return True
        try:
            return parse_as_of(filed) <= self.as_of
        except (ValueError, TypeError):
            return False

    def to_dict(self) -> dict:
        data = {**asdict(self), 'cutoff_basis': 'inclusive SEC filing date',
                'missing_filing_date': 'exclude when as_of is set',
                'scope': 'evidence eligibility; not a historical model or archived SEC snapshot',
                'invariants': ['exact entity', 'matching unit and period', 'no unsupported numeric inference']}
        data['policy_id'] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        return data


def policy_for(edgar: Any) -> VerificationPolicy:
    policy = getattr(edgar, 'policy', None)
    return policy if isinstance(policy, VerificationPolicy) else VerificationPolicy()


def policy_html(report: dict) -> str:
    from html import escape
    policy = report.get('verification_policy')
    if not policy:
        return '<p>Historical report: verification policy was not recorded.</p>'
    cutoff = policy.get('as_of') or 'no cutoff (latest eligible filings)'
    return f"<p>Policy: {escape(policy['version'])} · Evidence as of: {escape(cutoff)}. Inclusive filing dates; not an archived historical snapshot.</p>"
