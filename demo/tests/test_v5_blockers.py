"""Regression checks for the three v018 blockers, using retained and synthetic inputs."""
import copy,json
from pathlib import Path

from PIL import Image,ImageDraw
import pytest
from check_ending_v5 import audit_cut_frames
from pipeline import BuildError
from record_v5 import apple_filing_citations,RecordingError

ROOT=Path(__file__).resolve().parents[2]


def apple_result():
    return json.loads((ROOT/'demo/motion/v5/inputs.json').read_text())['recordings']['v505']['receipt']['result']


def test_citation_cards_keep_both_actual_e3_forms_periods_and_links():
    result=apple_result();before=copy.deepcopy(result)
    citations=apple_filing_citations(result)
    assert [(c['form'],c['period_label']) for c in citations]==[
        ('10-K','fiscal 2025 annual'),('10-Q','nine months to 28 Jun 2025')]
    assert [c['url'] for c in citations]==[c['url'] for c in result['corrections']['edits'][0]['citations']]
    assert all(c['evidence_id']=='E3' for c in citations)
    assert result==before


@pytest.mark.parametrize('mutation',[
    lambda r:r['evidence'][0]['components'].pop(),
    lambda r:r['corrections']['edits'][0]['citations'][1].update(form='10-K'),
    lambda r:r['corrections']['edits'][0]['citations'][1].update(end='2025-09-27'),
    lambda r:r['corrections']['edits'][0]['citations'][0].update(url='https://example.com/'),
    lambda r:r['evidence'][0].update(evidence_id='E4'),
])
def test_a_filing_card_cannot_substitute_a_source_or_a_period(mutation):
    result=apple_result();mutation(result)
    with pytest.raises(RecordingError):apple_filing_citations(result)


@pytest.fixture
def cut_images(tmp_path):
    dark=Image.new('RGB',(1920,1080),'#111a20')
    page=Image.new('RGB',(1920,1080),'#f7f5ef');draw=ImageDraw.Draw(page)
    for y in range(90,550,70):draw.rectangle((220,y,1500,y+12),fill='#111a20')
    def save(image,name):
        path=tmp_path/name;image.save(path);return path
    before=save(dark,'before.png');native=[save(page,f'native-{i}.png') for i in range(3)]
    return [before,*native],native,before


def test_encoded_cut_accepts_native_page_from_frame_4620_without_moving_the_cut(cut_images):
    encoded,native,before=cut_images
    report=audit_cut_frames(encoded,native,outgoing=before)
    assert report['status']=='pass'
    assert [r['frame'] for r in report['frames']]==[4619,4620,4621,4622]
    assert [r['native_page'] for r in report['frames']]==[False,True,True,True]


@pytest.mark.parametrize('frame',[1,2,3])
def test_encoded_cut_rejects_the_single_dark_frame_even_after_later_images_paint(cut_images,frame):
    encoded,native,before=cut_images;encoded[frame]=before
    report=audit_cut_frames(encoded,native,outgoing=before)
    assert report['status']=='fail' and report['frames'][frame]['status']=='fail'
    assert report['frames'][frame]['expected_native_page'] and not report['frames'][frame]['native_page']


def test_encoded_cut_rejects_a_premature_ending_or_missing_boundary_frames(cut_images):
    encoded,native,before=cut_images;encoded[0]=native[0]
    assert audit_cut_frames(encoded,native)['frames'][0]['status']=='fail'
    with pytest.raises(BuildError,match='4619–4622'):audit_cut_frames(encoded[1:],native)


def test_whole_composite_mask_rejects_a_native_glyph_even_in_the_outer_gutter():
    from check_composite_v5 import mask_pixels
    clear=Image.new('RGB',(76,228),'#111a20')
    assert mask_pixels(clear)
    leaked=clear.copy();ImageDraw.Draw(leaked).text((2,100),'Facts',fill='#f7f5ef')
    assert not mask_pixels(leaked)
    password=Image.new('RGB',(1920,24),'#111a20')
    ImageDraw.Draw(password).text((180,1),'Authenticated runs are public',fill='#f7f5ef')
    assert not mask_pixels(password)
