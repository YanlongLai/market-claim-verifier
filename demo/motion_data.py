"""Read pinned demo evidence and expose the small subset the film uses."""
from html import unescape
from pathlib import Path

from pipeline import BuildError, file_hash, read_json

EN = 'demo/data/demo-thread.json'
ZH = 'docs/evidence/posts-2026-10-28/tw-social-post-meta/report.json'
SITE = 'docs/site/data/site.json'
EVAL = 'docs/evidence/eval-v2-2026-10-27/summary.json'


def decode_text(value):
    """Decode source entities exactly once, before any HTML/number formatting."""
    if isinstance(value, str):
        return unescape(value)
    if isinstance(value, list):
        return [decode_text(item) for item in value]
    if isinstance(value, dict):
        return {key: decode_text(item) for key, item in value.items()}
    return value


def product_data(repo: Path) -> dict:
    en, zh, site, evaluation = [decode_text(read_json(repo / p)) for p in (EN, ZH, SITE, EVAL)]
    providers = []
    for name, label in [('meta', 'Meta Model API'), ('baseten', 'Baseten'), ('fireworks', 'Fireworks')]:
        row = next(r for r in site['chart'] if r['id'] == name)
        values = []
        for system in ('single_shot', 'agent'):
            splits = evaluation['metrics'][f'{system}@{name}'].values()
            n, correct = sum(v['n_claims'] for v in splits), sum(v['correct'] for v in splits)
            if n != site['eval']['claim_count']:
                raise BuildError('Site/evaluation claim counts disagree.')
            accuracy = correct / n
            expected = row['without' if system == 'single_shot' else 'with_checks']['accuracy']
            if abs(accuracy - expected) > 1e-9:
                raise BuildError('Site chart no longer matches the pre-registered evaluation.')
            values.append(100 * accuracy)
        providers.append(dict(id=name, label=label, alone=round(values[0]), checked=round(values[1], 1)
                              if name != 'meta' else round(values[1]), delta_label=row['change_points']))
    claim = site['examples']['en']['claims'][0]
    excerpt = claim['excerpts'][0]['excerpt']
    columns = [c['text'] for c in excerpt['row']['cells'] if c['text'] and not c['is_row_label']]
    headers = [c['text'] for c in excerpt['headers'][0]['cells'] if c['text']]
    years = [c['text'] for c in excerpt['headers'][1]['cells'] if c['text']]
    apple = en['claims'][2]
    check = apple['program_checks'][0]
    quarter = apple['evidence'][0]
    amazon_check=en['claims'][0]['program_checks'][0]
    nvidia_growth=en['claims'][1]['program_checks'][1]
    chinese = zh['claims'][2]
    chinese_check = chinese['program_checks'][0]
    chinese_amount = chinese_check['stated_value_used']
    return dict(
        providers=providers, claim_count=site['eval']['claim_count'],
        max_gain_points=max(round(row['checked']-row['alone'], 1) for row in providers),
        english_post=en['post'], chinese_post=zh['post'],
        english_claims=[{k:c.get(k) for k in ('quote','ticker','kind','status','verdict','summary','screen_reason')}
                        for c in en['claims']],
        chinese_claim={k:chinese.get(k) for k in ('index','quote','ticker','verdict','summary','program_checks','evidence')},
        claim_numbers=dict(amazon_b=amazon_check['stated_value_used']/1e9,
                           precision_b=amazon_check['precision']/1e9,
                           nvidia_multiplier=1+nvidia_growth['stated_value_used']/100,
                           chinese_yi=chinese_amount/1e8,chinese_b=chinese_amount/1e9,
                           chinese_filed_b=chinese_check['actual_value']/1e9),
        apple=dict(claimed_b=check['stated_value_used']/1e9, quarter_b=check['actual_value']/1e9,
                   full_year_b=en['apple_full_year']['value']/1e9, quarter_period=quarter['period'],
                   quarter_start=quarter['start'], quarter_end=quarter['end'], verdict=apple['verdict']),
        filing=dict(headers=headers, years=years, row_label='Total net sales', values=columns,
                    section=excerpt['section_title'], form=claim['source']['form'],
                    filed=claim['source']['filed'],
                    url=claim['excerpts'][0]['primary_url']+'#'+excerpt['fact']['id'], unit='USD in millions'),
        provenance={**{p:file_hash(repo / p) for p in (EN, ZH, SITE, EVAL, 'examples/posts/tw-social-post.txt')},
                    **{s['path']:s['sha256'] for s in en['sources'].values()}})
