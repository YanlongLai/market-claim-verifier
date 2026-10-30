"""Conservative final wording from program outcomes, not model prose."""

def program_summary(verdict: str, checks: list[dict]) -> str:
    if verdict == 'supported':
        return 'The program checks support the extracted claim within the recorded evidence, period and tolerance.'
    if verdict == 'contradicted':
        return 'The program checks found a contradiction. Use the validated evidence and numeric checks below for the correction.'
    reasons = sorted({str(c.get('reason')) for c in checks if c.get('reason')})
    return 'Insufficient evidence for a supported or contradicted conclusion; no correction is validated. ' + ('Program reasons: ' + '; '.join(reasons) if reasons else 'No conclusive program checks are available.')
