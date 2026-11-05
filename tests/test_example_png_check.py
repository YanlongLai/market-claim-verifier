"""The example PNG check ignores zlib bytes but not pixels."""
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_examples  # noqa: E402


def encode(image, level):
    out = BytesIO()
    image.save(out, format="PNG", compress_level=level)
    return out.getvalue()


def test_same_pixels_with_different_compression_match():
    image = Image.new("RGB", (64, 32), (240, 238, 230))
    a, b = encode(image, 9), encode(image, 1)
    assert a != b
    assert build_examples.same_png_pixels(a, b)


def test_one_changed_pixel_is_stale(tmp_path, monkeypatch):
    image = Image.new("RGB", (64, 32), (240, 238, 230))
    changed = image.copy()
    changed.putpixel((5, 5), (0, 0, 0))
    assert not build_examples.same_png_pixels(encode(image, 9), encode(changed, 9))
    monkeypatch.setattr(build_examples, "EXAMPLES", tmp_path)
    path = tmp_path / "a.png"
    path.write_bytes(encode(image, 9))
    build_examples.put(path, encode(image, 1), check=True)
    try:
        build_examples.put(path, encode(changed, 1), check=True)
    except ValueError as error:
        assert "Stale example: a.png" in str(error)
    else:
        raise AssertionError("a changed pixel must be reported as stale")
