"""Invoke only an explicitly supplied trusted core command array."""

import json
import math
import re
import subprocess

from .errors import ComposeError


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("non-finite number")
    return result


def _constant(value):
    raise ValueError("non-finite number")


def run_core(command: list[str], arguments: list[str]) -> dict:
    if (not isinstance(command, list) or not command or not isinstance(arguments, list)
            or any(not isinstance(item, str) or "\0" in item for item in command + arguments)
            or any(not item for item in command)):
        raise ComposeError("CORE_COMMAND", "Explicit trusted core command array is required")
    try:
        result = subprocess.run(command + arguments, shell=False, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise ComposeError("CORE_UNAVAILABLE", "Core operation is unavailable") from None
    stderr_code = re.match(r"^([A-Z][A-Z0-9_]{0,63}):", result.stderr or "")
    if result.returncode != 0 and stderr_code:
        raise ComposeError(stderr_code.group(1), "Core operation did not pass")
    try:
        document = json.loads(result.stdout, object_pairs_hook=_pairs,
                              parse_constant=_constant, parse_float=_float)
    except (ValueError, TypeError, RecursionError):
        code = "CORE_FAILED" if result.returncode != 0 else "CORE_OUTPUT"
        raise ComposeError(code, "Core returned invalid JSON") from None
    if result.returncode != 0 or not isinstance(document, dict) or document.get("status") != "passed":
        code = document.get("code") if isinstance(document, dict) else None
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", code):
            code = "CORE_FAILED" if result.returncode != 0 else "CORE_BLOCKED"
        raise ComposeError(code, "Core operation did not pass")
    return document
