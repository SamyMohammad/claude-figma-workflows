import io
import zlib

import pytest
from PIL import Image, ImageCms

from figma_core.errors import CoreError
from figma_core.images import load_png


def test_untagged_png_declared_srgb_loads_rgba(tmp_path):
    path = tmp_path / "capture.png"
    Image.new("RGB", (2, 1), "red").save(path)
    image = load_png(path, "srgb")
    assert image.mode == "RGBA"
    assert image.getpixel((0, 0)) == (255, 0, 0, 255)


def test_non_png_is_rejected(tmp_path):
    path = tmp_path / "capture.png"
    Image.new("RGB", (1, 1)).save(path, format="JPEG")
    with pytest.raises(CoreError, match="PNG"):
        load_png(path, "srgb")


def test_unknown_declared_color_space_is_rejected(tmp_path):
    path = tmp_path / "capture.png"
    Image.new("RGB", (1, 1)).save(path)
    with pytest.raises(CoreError, match="sRGB"):
        load_png(path, "display-p3")


def test_unrecognized_embedded_profile_is_rejected(tmp_path):
    path = tmp_path / "capture.png"
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB"))
    Image.new("RGB", (1, 1)).save(path, icc_profile=profile.tobytes())
    with pytest.raises(CoreError, match="profile"):
        load_png(path, "srgb")


def test_embedded_srgb_profile_is_accepted(tmp_path):
    path = tmp_path / "capture.png"
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    Image.new("RGB", (1, 1), "white").save(path, icc_profile=profile.tobytes())
    assert load_png(path, "srgb").getpixel((0, 0)) == (255, 255, 255, 255)


def test_unrecognized_gamma_is_rejected(tmp_path):
    path = tmp_path / "capture.png"
    buffer = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")
    data = buffer.getvalue()
    payload = (100000).to_bytes(4, "big")
    chunk = len(payload).to_bytes(4, "big") + b"gAMA" + payload
    chunk += zlib.crc32(b"gAMA" + payload).to_bytes(4, "big")
    path.write_bytes(data[:33] + chunk + data[33:])
    with pytest.raises(CoreError, match="color metadata"):
        load_png(path, "srgb")


def test_decompression_bomb_warning_is_an_error(tmp_path, monkeypatch):
    path = tmp_path / "capture.png"
    Image.new("RGB", (2, 2)).save(path)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 2)
    with pytest.raises(CoreError, match="Cannot load PNG"):
        load_png(path, "srgb")
