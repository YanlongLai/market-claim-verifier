import importlib.util
from pathlib import Path


def scorer():
    p=Path(__file__).parents[1]/'eval/multimodal-v1/score.py'
    spec=importlib.util.spec_from_file_location('fair_score',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def gold():return [{'id':'g','ticker':'TSLA','metric':'revenue','period':'FY2026Q3','gold':'contradicted'}]
def claim(verdict):return {'ticker':'TSLA','claim':'Tesla revenue was 99 billion for fiscal Q3 2026.','status':'verified','verdict':verdict,'program_checks':[{'program_verdict':verdict}]}


def test_missing_wrong_ticker_and_period_remain_wrong():
    m=scorer()
    for c in [[],[{**claim('contradicted'),'ticker':'AAPL'}],[{**claim('contradicted'),'claim':'Tesla revenue was 99 billion for fiscal Q2 2026.'}]]:
        r=m.score(gold(),[{'claims':c}]);assert r['denominator']==1 and r['correct']==0


def test_duplicate_conflicts_do_not_select_best_or_inflate_denominator():
    m=scorer();r=m.score(gold(),[{'claims':[claim('supported'),claim('contradicted')]}])
    assert r['denominator']==1 and r['correct']==0 and r['false_supported']==1
    assert r['rows'][0]['prediction']=='conflict'
    r=m.score(gold(),[{'claims':[claim('contradicted'),claim('contradicted')]}])
    assert r['correct']==1 and r['denominator']==1


def test_compound_period_alignment_not_scored_twice():
    m=scorer();g=gold()+[{**gold()[0],'id':'future','period':'FY2028Q4','gold':'insufficient_evidence'}]
    c={**claim('supported'),'claim':'Tesla revenue for fiscal Q3 2026 and fiscal Q4 2028 was 99 billion.'}
    r=m.score(g,[{'claims':[c]}]);assert r['correct']==0 and r['extracted']==0 and len(r['unmatched_extractions'])==1


def test_spelled_quarters_align_without_changing_truth():
    m=scorer()
    for text in ["third quarter of fiscal 2026", "fiscal 2026 third quarter", "Q3 of fiscal 2026"]:
        assert m.period_matches(text,"FY2026Q3")
        assert not m.period_matches(text,"FY2026Q2")
