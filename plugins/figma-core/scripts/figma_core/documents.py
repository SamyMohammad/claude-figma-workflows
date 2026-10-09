"""Strict, safe JSON document loading."""

import json
import math
from pathlib import Path

from .errors import CoreError


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("non-finite JSON number")


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("non-finite JSON number")
    return parsed


def read_json(path: Path) -> dict:
    """Read a JSON object, rejecting duplicate keys and non-finite values."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(
                stream,
                object_pairs_hook=_unique_pairs,
                parse_constant=_reject_constant,
                parse_float=_finite_float,
            )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        reason = (
            "duplicate key" if "duplicate" in str(error) else
            "non-finite number" if "non-finite" in str(error) else
            "unreadable or invalid JSON"
        )
        raise CoreError("DOCUMENT_INVALID", f"{path.name}: {reason}") from None
    if not isinstance(value, dict):
        raise CoreError("DOCUMENT_INVALID", f"{path.name}: expected JSON object")
    return value
