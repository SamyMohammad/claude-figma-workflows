"""Safe loading and normalization of sRGB PNG captures."""

import io
import warnings
from pathlib import Path

from PIL import Image, ImageCms

from .errors import CoreError


def _profile_characteristics(data: bytes) -> tuple[bytes, bytes, bytes, dict[bytes, bytes]]:
    if len(data) < 132:
        raise ValueError("Short ICC profile")
    count = int.from_bytes(data[128:132], "big")
    end = 132 + count * 12
    if end > len(data):
        raise ValueError("Invalid ICC tag table")
    tags = {}
    for entry in range(132, end, 12):
        name = data[entry:entry + 4]
        offset = int.from_bytes(data[entry + 4:entry + 8], "big")
        length = int.from_bytes(data[entry + 8:entry + 12], "big")
        if name in tags or offset < end or length == 0 or offset + length > len(data):
            raise ValueError("Invalid ICC tag")
        if name not in (b"desc", b"cprt"):
            tags[name] = data[offset:offset + length]
    return data[8:24], data[36:40], data[64:80], tags


_SRGB_CHARACTERISTICS = _profile_characteristics(
    ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
)


def _check_profile(info: dict) -> None:
    profile_bytes = info.get("icc_profile")
    if profile_bytes:
        try:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(profile_bytes))
            characteristics = _profile_characteristics(profile_bytes)
        except (OSError, ValueError, TypeError):
            raise CoreError("IMAGE_COLOR", "Unrecognized PNG color profile") from None
        if profile.profile.xcolor_space.strip() != "RGB" or characteristics != _SRGB_CHARACTERISTICS:
            raise CoreError("IMAGE_COLOR", "Unsupported PNG color profile")
    if ("gamma" in info or "chromaticity" in info) and "srgb" not in info and not profile_bytes:
        raise CoreError("IMAGE_COLOR", "Unsupported PNG color metadata")


def load_png(path: Path, declared_color_space: str) -> Image.Image:
    """Return a fully loaded RGBA PNG after checking its color declaration."""
    if declared_color_space != "srgb":
        raise CoreError("IMAGE_COLOR", "Capture must declare sRGB color space")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as source:
                if source.format != "PNG":
                    raise CoreError("IMAGE_FORMAT", "Capture must be PNG")
                _check_profile(source.info)
                source.load()
                return source.convert("RGBA")
    except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        if isinstance(error, CoreError):
            raise
        raise CoreError("IMAGE_INVALID", f"Cannot load PNG capture: {path}") from error
