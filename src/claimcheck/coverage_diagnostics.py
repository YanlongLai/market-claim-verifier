"""Explain observable coverage gaps without guessing image contents or verdicts."""
from __future__ import annotations


def coverage_diagnostics(channels: list[dict]) -> list[dict]:
    findings = []
    for channel in channels:
        visual = channel.get('kind') in {'ocr', 'frame'}
        text = channel.get('normalized_text') or channel.get('raw_text') or ''
        common = {'channel_id': channel.get('id'), 'basis': 'recorded_pipeline_state'}
        if visual:
            findings.append({**common, 'code': 'visual_geometry_unverified',
                'message': 'OCR reads text. Bar heights, line positions, colors and series-to-period relationships are not verified by this text pipeline.',
                'next_step': 'For charts, supply the corresponding numeric table with units, periods and footnotes. A table check does not validate the chart geometry.'})
        if channel.get('error'):
            code, message, action = ('channel_error', 'This channel recorded a processing error; coverage is incomplete.',
                'Inspect the retained error and trace before a separately budgeted retry.')
        elif not text.strip():
            code, message, action = ('no_readable_text', 'No readable text was retained; no successful reading can be inferred.',
                'Supply a readable original or a native-text table. Check image resolution and cropping.')
        elif not channel.get('claims'):
            code, message, action = ('no_claims_extracted', 'Text was read, but no numeric claims were extracted. This is not a verified document.',
                'Inspect the original and retained text. For an unlabeled chart, provide its underlying table; never treat axis ticks as company values.')
        else:
            continue
        findings.append({**common, 'code': code, 'message': message, 'next_step': action})
    return findings
