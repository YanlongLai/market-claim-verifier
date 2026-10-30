import json
from pathlib import Path
from claimcheck.coverage_diagnostics import coverage_diagnostics
from claimcheck.stock_review import build_stock_review


def test_real_chart_has_text_but_no_claims():
    root=Path(__file__).resolve().parents[1]
    source=root/'docs/evidence/stock-context-posthoc-2026-10-30/attempt-2/REAL-TSLA-23/ingest.json'
    report=json.loads(source.read_text())
    result=coverage_diagnostics(report['channels'])
    assert {x['code'] for x in result}=={'visual_geometry_unverified','no_claims_extracted'}
    assert 'Operating Cash Flow' in report['channels'][0]['normalized_text']
    assert not report['channels'][0]['claims']


def test_visual_warning_survives_successful_text_claim():
    result=coverage_diagnostics([{'kind':'ocr','raw_text':'Revenue 1','claims':[{'status':'verified'}]}])
    assert [x['code'] for x in result]==['visual_geometry_unverified']


def test_error_is_not_misdiagnosed_as_empty_extraction():
    result=coverage_diagnostics([{'kind':'ocr','raw_text':'x','error':'output incomplete','claims':[]}])
    assert [x['code'] for x in result]==['visual_geometry_unverified','channel_error']


def test_empty_read_and_plain_text_are_distinct():
    assert coverage_diagnostics([{'kind':'text','raw_text':''}])[0]['code']=='no_readable_text'
    assert coverage_diagnostics([{'kind':'text','raw_text':'hello'}])[0]['code']=='no_claims_extracted'
    assert coverage_diagnostics([{'kind':'text','raw_text':'Revenue 1','claims':[{}]}])==[]


def test_summary_replays_gaps_without_changing_input(tmp_path):
    p=tmp_path/'ingest.json';p.write_text(json.dumps({'input':{'file':'chart.png'},'status':'completed','channels':[{'id':'<image>','kind':'ocr','raw_text':'Axis 0 1','claims':[]}]}))
    before=p.read_bytes()
    result=build_stock_review('TSLA',[p],tmp_path/'summary')
    assert p.read_bytes()==before
    assert result['documents_without_target_program_checks']==1
    assert len(result['documents'][0]['coverage_diagnostics'])==2
    html=(tmp_path/'summary/stock-review.html').read_text()
    assert '&lt;image&gt;' in html and '<image>' not in html
    assert 'no_claims_extracted' in html and 'underlying table' in html


def test_sampled_video_frame_also_discloses_geometry_gap():
    result=coverage_diagnostics([{'kind':'frame','raw_text':'Revenue 1','claims':[{}]}])
    assert result[0]['code']=='visual_geometry_unverified'
