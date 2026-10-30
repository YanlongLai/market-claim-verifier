from pathlib import Path
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from claimcheck.ingest_media import decode, IngestError
from claimcheck.ingest import prepare_text, attach_locations


def pdf(path, *, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 50 700 Td (Revenue was $123 million in FY2025.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    writer.add_blank_page(width=600, height=800)
    if encrypted:
        writer.encrypt("secret")
    writer.write(path)


def test_page_text_and_unreadable_page_remain_visible(tmp_path):
    path = tmp_path / "input.pdf"
    pdf(path)
    kind, channels = decode(path, tmp_path / "media")
    assert kind == "pdf"
    assert len(channels) == 2
    assert channels[0]["decoded"]
    assert not channels[1]["decoded"]
    assert "not checked" in channels[1]["error"]
    prepare_text(channels[0])
    text = channels[0]["normalized_text"]
    claim = {"quote": text, "span": [0, len(text)]}
    attach_locations(channels[0], [claim])
    assert claim["source_locations"][0]["sources"][0]["page"] == 1


def test_encrypted_pdf_fails_without_password_attempt(tmp_path):
    path = tmp_path / "input.pdf"
    pdf(path, encrypted=True)
    with pytest.raises(IngestError, match="encrypted"):
        decode(path, tmp_path / "media")


def test_malformed_pdf_fails_explicitly(tmp_path):
    path = tmp_path / "bad.pdf"
    path.write_bytes(b"not a PDF")
    with pytest.raises(IngestError, match="parse PDF"):
        decode(path, tmp_path / "media")
