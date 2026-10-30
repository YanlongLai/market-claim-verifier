"""Frozen deterministic alignment/scoring; never reads provider gold prompts."""
import re
METRICS={'revenue':r'\brevenue\b|\bnet sales\b','net_income':r'\bnet income\b|\bnet earnings\b','eps':r'\beps\b|earnings per (?:common )?share'}


def period_matches(text,period):
    year=period[2:6];q=period[-1]
    ordinal={'1':'(?:first|1st)','2':'(?:second|2nd)','3':'(?:third|3rd)','4':'(?:fourth|4th)'}[q]
    words=rf'(?:{ordinal}\s+(?:fiscal\s+)?quarter\s+(?:of\s+)?(?:fiscal\s+)?{year}\b|fiscal\s+{year}\s+{ordinal}\s+quarter)'
    return bool(re.search(words,text,re.I)) or bool(re.search(rf'(?:fy\s*{year}\s*q\s*{q}\b|(?:fiscal\s+)?q\s*{q}\s*(?:of\s+)?(?:fiscal\s+)?{year}\b|fiscal\s+{year}\s*q\s*{q}\b)',text,re.I))


def score(gold,channels):
    claims=[c for ch in channels for c in ch.get('claims',[])]
    bins={g['id']:[] for g in gold};unmatched=[]
    for c in claims:
        text=c.get('claim','');ticker=str(c.get('ticker') or '').upper()
        matches=[g for g in gold if (ticker==g['ticker'] or g['ticker']=='GOOGL' and ticker=='GOOG')
                 and re.search(METRICS[g['metric']],text,re.I) and period_matches(text,g['period'])]
        if len(matches)==1:bins[matches[0]['id']].append(c)
        else:unmatched.append({'claim':text,'status':c.get('status'),'match_count':len(matches)})
    rows=[]
    for g in gold:
        matches=bins[g['id']];verdicts=[]
        for c in matches:
            verdict=c.get('verdict')
            if c.get('status')=='verified' and verdict in ('supported','contradicted','insufficient_evidence') and (c.get('program_checks') or verdict=='insufficient_evidence'):
                verdicts.append(verdict)
            else:verdicts.append('unresolved')
        unique=set(verdicts)
        prediction=next(iter(unique)) if len(unique)==1 else 'conflict' if unique else 'missing'
        rows.append({'id':g['id'],'gold':g['gold'],'prediction':prediction,'correct':prediction==g['gold'],
                     'matched_extractions':len(matches),'checked':any(x in ('supported','contradicted','insufficient_evidence') for x in verdicts),
                     'unsafe_supported':g['gold']!='supported' and 'supported' in verdicts})
    return {'rows':rows,'denominator':len(gold),'correct':sum(r['correct'] for r in rows),
            'extracted':sum(r['matched_extractions']>0 for r in rows),'checked':sum(r['checked'] for r in rows),
            'negative_gold':sum(r['gold']!='supported' for r in rows),'false_supported':sum(r['unsafe_supported'] for r in rows),
            'abstentions':sum(r['prediction']=='insufficient_evidence' for r in rows),'unmatched_extractions':unmatched}
