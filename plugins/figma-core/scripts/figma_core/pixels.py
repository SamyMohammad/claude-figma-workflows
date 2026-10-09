"""Pure, policy-gated comparison of visible RGBA pixels."""

from PIL import Image, ImageChops, ImageDraw

from .errors import CoreError
from .schema import validate_document


def _visible_delta(reference: Image.Image, actual: Image.Image) -> Image.Image:
    channels = []
    for color in ("black", "white"):
        background = Image.new("RGBA", reference.size, color)
        left = Image.alpha_composite(background, reference).convert("RGB")
        right = Image.alpha_composite(background, actual).convert("RGB")
        channels.extend(ImageChops.difference(left, right).split())
    result = channels[0]
    for channel in channels[1:]:
        result = ImageChops.lighter(result, channel)
    return result


def _bounds(box: list[int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y, width, height = box
    if x + width > size[0] or y + height > size[1]:
        raise CoreError("POLICY_INVALID", "Comparison region exceeds image size")
    return x, y, x + width, y + height


def _overlap(first: tuple[int, ...], second: tuple[int, ...]) -> bool:
    return first[0] < second[2] and second[0] < first[2] and first[1] < second[3] and second[1] < first[3]


def _count(mask: Image.Image) -> int:
    return mask.histogram()[255]


def measure(reference: Image.Image, actual: Image.Image, policy: dict) -> dict:
    """Compare equal-size images using explicit tolerance and eligible regions."""
    validate_document("comparison-policy", policy)
    if reference.size != actual.size:
        raise CoreError("IMAGE_INVALID", "Reference and actual image sizes differ")
    if not reference.width or not reference.height:
        raise CoreError("IMAGE_INVALID", "Images have no eligible pixels")

    ignored = [_bounds(region["box"], reference.size) for region in policy["ignored"]]
    critical = [(_bounds(region["box"], reference.size), region) for region in policy["critical"]]
    if any(_overlap(critical_box, ignored_box) for critical_box, _ in critical for ignored_box in ignored):
        raise CoreError("POLICY_INVALID", "Critical and ignored regions overlap")

    eligible = Image.new("L", reference.size, 255)
    draw = ImageDraw.Draw(eligible)
    for left, top, right, bottom in ignored:
        draw.rectangle((left, top, right - 1, bottom - 1), fill=0)
    eligible_pixels = _count(eligible)
    if not eligible_pixels:
        raise CoreError("POLICY_INVALID", "No eligible pixels remain after ignored regions")

    delta = _visible_delta(reference.convert("RGBA"), actual.convert("RGBA"))
    tolerance = policy["channelTolerance"]
    changed = delta.point([255 if value > tolerance else 0 for value in range(256)])
    changed = ImageChops.multiply(changed, eligible)
    changed_pixels = _count(changed)
    changed_ratio = changed_pixels / eligible_pixels

    critical_results = []
    for box, region in critical:
        area = (box[2] - box[0]) * (box[3] - box[1])
        count = _count(changed.crop(box))
        ratio = count / area
        critical_results.append({"id": region["id"], "changedPixels": count,
                                 "eligiblePixels": area, "changedRatio": ratio,
                                 "status": "passed" if ratio <= region["maxChangedRatio"] else "failed"})

    heat = ImageChops.multiply(delta, eligible)
    diff = Image.merge("RGB", (heat, Image.new("L", heat.size), Image.new("L", heat.size)))
    actual_rgba = actual.convert("RGBA")
    red = Image.new("RGBA", actual.size, (255, 0, 0, 255))
    overlay = Image.composite(Image.blend(actual_rgba, red, 0.5), actual_rgba, changed)
    status = "passed" if changed_ratio <= policy["maxChangedRatio"] and all(
        result["status"] == "passed" for result in critical_results) else "failed"
    return {"status": status, "changedPixels": changed_pixels,
            "eligiblePixels": eligible_pixels, "changedRatio": changed_ratio,
            "criticalResults": critical_results, "diff": diff, "overlay": overlay}
