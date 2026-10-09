"""Validation for the supported DTCG value subset."""

import math

from .errors import CoreError


SUPPORTED = frozenset({"color", "dimension", "number", "fontFamily", "fontWeight",
                       "duration", "cubicBezier", "typography"})
_FONT_WEIGHTS = frozenset({"thin", "hairline", "extra-light", "ultra-light", "light",
                           "normal", "regular", "book", "medium", "semi-bold",
                           "demi-bold", "bold", "extra-bold", "ultra-bold", "black",
                           "heavy", "extra-black", "ultra-black"})
TYPOGRAPHY_FIELDS = {"fontFamily": "fontFamily", "fontSize": "dimension",
                     "fontWeight": "fontWeight", "letterSpacing": "dimension",
                     "lineHeight": "number"}
_MAX_SAFE_INTEGER = 2**53 - 1


def _number(value: object) -> bool:
    if type(value) is int:
        return -_MAX_SAFE_INTEGER <= value <= _MAX_SAFE_INTEGER
    return type(value) is float and math.isfinite(value)


def _measure(value: object, units: set[str]) -> bool:
    return (isinstance(value, dict) and set(value) == {"value", "unit"}
            and _number(value["value"]) and isinstance(value["unit"], str)
            and value["unit"] in units)


def validate_value(kind: str, value: object, path: str) -> None:
    if kind not in SUPPORTED:
        raise CoreError("TOKEN_TYPE", f"Unsupported token type at {path}: {kind}")
    valid = False
    if kind == "number":
        valid = _number(value)
    elif kind == "dimension":
        valid = _measure(value, {"px", "rem"})
    elif kind == "duration":
        valid = _measure(value, {"ms", "s"})
    elif kind == "color":
        valid = (isinstance(value, dict) and set(value) == {"colorSpace", "components", "alpha"}
                 and value["colorSpace"] == "srgb"
                 and isinstance(value["components"], list) and len(value["components"]) == 3
                 and all(_number(channel) and 0 <= channel <= 1 for channel in value["components"])
                 and _number(value["alpha"]) and 0 <= value["alpha"] <= 1)
    elif kind == "fontFamily":
        valid = ((isinstance(value, str) and bool(value.strip()))
                 or (isinstance(value, list) and bool(value)
                     and all(isinstance(name, str) and name.strip() for name in value)))
    elif kind == "fontWeight":
        valid = (_number(value) and 1 <= value <= 1000) or (isinstance(value, str) and value in _FONT_WEIGHTS)
    elif kind == "cubicBezier":
        valid = (isinstance(value, list) and len(value) == 4
                 and all(_number(component) for component in value)
                 and 0 <= value[0] <= 1 and 0 <= value[2] <= 1)
    elif kind == "typography":
        valid = isinstance(value, dict) and set(value) == set(TYPOGRAPHY_FIELDS)
        if valid:
            for field, field_type in TYPOGRAPHY_FIELDS.items():
                validate_value(field_type, value[field], f"{path}.{field}")
    if not valid:
        raise CoreError("TOKEN_VALUE", f"Invalid {kind} value at {path}")
