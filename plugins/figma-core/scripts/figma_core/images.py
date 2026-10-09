"""Safe loading and normalization of sRGB PNG captures."""

import io
import warnings
from pathlib import Path

from PIL import Image, ImageCms

from .errors import CoreError


def _check_profile(info: dict) -> None:
    profile_bytes = info.get("icc_profile")
    if profile_bytes:
        try:
            profile = ImageCms.ImageCmsProfile(io.BytesIO(profile_bytes))
            name = ImageCms.getProfileName(profile).lower()
        except (OSError, ValueError, TypeError):
            raise CoreError("IMAGE_COLOR", "Unrecognized PNG color profile") from None
        if "srgb" not in name or profile.profile.xcolor_space.strip() != "RGB":
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
