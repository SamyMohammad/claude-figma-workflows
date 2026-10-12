"""Select only an evidenced application platform and installed adapter."""

import re
from urllib.parse import parse_qs, urlparse

from .errors import CoreError


_ADAPTERS = {"flutter": "figma-flutter:build", "compose": "figma-compose:build"}


def parse_figma_url(url: str) -> tuple[str, str | None]:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError:
        raise CoreError("FIGMA_URL", "Invalid Figma URL") from None
    if (parsed.scheme != "https" or parsed.hostname not in {"figma.com", "www.figma.com"}
            or parsed.username or parsed.password or port or parsed.fragment):
        raise CoreError("FIGMA_URL", "Invalid Figma URL")
    match = re.fullmatch(r"/(?:file|design)/([A-Za-z0-9]+)(?:/[^/]*)?/?", parsed.path)
    if match is None:
        raise CoreError("FIGMA_URL", "Unsupported Figma file path")
    query = parse_qs(parsed.query, keep_blank_values=True)
    nodes = query.get("node-id", [])
    if len(nodes) > 1 or (nodes and not re.fullmatch(r"[0-9]+[:-][0-9]+", nodes[0])):
        raise CoreError("FIGMA_URL", "Invalid Figma node ID")
    return match.group(1), nodes[0].replace("-", ":") if nodes else None


def select_platform(candidates: list[str], explicit: str | None) -> str:
    found = set(candidates)
    if not found or found - _ADAPTERS.keys():
        raise CoreError("TARGET_INVALID", "No supported target evidence")
    if explicit is not None:
        if explicit not in found:
            raise CoreError("TARGET_INVALID", "Selected target lacks project evidence")
        return explicit
    if len(found) != 1:
        raise CoreError("TARGET_AMBIGUOUS", "Select an explicit target")
    return found.pop()


def dispatch(platform: str, available_skills: list[str]) -> str:
    skill = _ADAPTERS.get(platform)
    if skill is None:
        raise CoreError("TARGET_INVALID", "Unsupported target")
    if skill not in available_skills:
        raise CoreError("ADAPTER_UNAVAILABLE", f"Adapter {skill} is unavailable")
    return skill
