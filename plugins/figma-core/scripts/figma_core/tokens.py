"""Exact token resolution and advisory audit."""

import json
import re
from copy import deepcopy

from .errors import CoreError
from .token_types import SUPPORTED, TYPOGRAPHY_FIELDS, validate_value


_ALIAS = re.compile(r"^\{([^{}]+)\}$")


def _collect(document: dict) -> dict[str, tuple[str, object]]:
    if not isinstance(document, dict):
        raise CoreError("TOKEN_DOCUMENT", "Token document must be an object")
    found = {}

    def walk(node: object, path: str, inherited: str | None) -> None:
        if not isinstance(node, dict):
            raise CoreError("TOKEN_DOCUMENT", f"Invalid token/group at {path}")
        if "$ref" in node or "$extends" in node:
            raise CoreError("TOKEN_UNSUPPORTED", f"Unsupported $ref/$extends at {path}")
        declared = node.get("$type", inherited)
        if declared is not None and (not isinstance(declared, str) or declared not in SUPPORTED):
            raise CoreError("TOKEN_TYPE", f"Unknown token type at {path}: {declared}")
        if any(not isinstance(key, str) for key in node):
            raise CoreError("TOKEN_DOCUMENT", f"Invalid token key at {path}")
        children = [(key, value) for key, value in node.items() if not key.startswith("$")]
        if "$value" in node:
            if children or not path or declared is None:
                raise CoreError("TOKEN_DOCUMENT", f"Mixed or untyped token at {path}")
            found[path] = (declared, node["$value"])
            return
        if not children or any(key.startswith("$") and key not in {"$type", "$description", "$extensions"}
                               for key in node):
            raise CoreError("TOKEN_DOCUMENT", f"Invalid token group at {path}")
        for key, child in children:
            if not key or "." in key:
                raise CoreError("TOKEN_DOCUMENT", f"Invalid token path at {path}")
            walk(child, f"{path}.{key}" if path else key, declared)

    for name, group in document.items():
        if name not in {"base", "light", "dark"}:
            raise CoreError("TOKEN_MODE", f"Unknown mode/group: {name}")
        walk(group, name, None)
    return found


def _resolve_tokens(document: dict, mode: str) -> dict:
    if not isinstance(document, dict) or mode not in {"base", "light", "dark"} or mode not in document:
        raise CoreError("TOKEN_MODE", f"Unknown mode: {mode}")
    found = _collect(document)
    memo = {}
    stack = set()

    def resolve(path: str) -> tuple[str, object]:
        if path in memo:
            return memo[path]
        if path in stack:
            raise CoreError("TOKEN_ALIAS", f"Token alias cycle at {path}")
        if path not in found:
            raise CoreError("TOKEN_ALIAS", f"Missing token alias: {path}")
        stack.add(path)
        kind, raw = found[path]

        def field(value: object, expected: str) -> object:
            match = _ALIAS.fullmatch(value) if isinstance(value, str) else None
            if match:
                target = match.group(1)
                target_kind, target_value = resolve(target)
                if target_kind != expected:
                    raise CoreError("TOKEN_ALIAS", f"Incompatible alias type at {path}: {target}")
                return deepcopy(target_value)
            return deepcopy(value)

        if kind == "typography" and isinstance(raw, dict):
            value = {key: field(item, TYPOGRAPHY_FIELDS.get(key, ""))
                     for key, item in raw.items()}
        else:
            value = field(raw, kind)
        validate_value(kind, value, path)
        stack.remove(path)
        memo[path] = (kind, value)
        return memo[path]

    prefix = f"{mode}."
    return {path[len(prefix):]: {"type": resolve(path)[0], "value": resolve(path)[1]}
            for path in found if path.startswith(prefix)}


def resolve_tokens(document: dict, mode: str) -> dict:
    if mode not in {"light", "dark"}:
        raise CoreError("TOKEN_MODE", f"Unknown mode: {mode}")
    return _resolve_tokens(document, mode)


def audit_tokens(document: dict) -> dict:
    issues = []
    proposals = []
    modes = [mode for mode in ("light", "dark") if isinstance(document, dict) and mode in document]
    if not modes:
        issues.append("No selected token modes")
    resolved = {}
    if isinstance(document, dict) and "base" in document:
        try:
            _resolve_tokens(document, "base")
        except CoreError as error:
            issues.append(f"base: {error}")
    for mode in modes:
        try:
            resolved[mode] = resolve_tokens(document, mode)
        except CoreError as error:
            issues.append(f"{mode}: {error}")
    if len(resolved) == 2:
        light, dark = resolved["light"], resolved["dark"]
        for path in sorted(light.keys() | dark.keys()):
            if path not in light or path not in dark or light[path]["type"] != dark[path]["type"]:
                issues.append(f"Semantic path/type mismatch: {path}")
    if not issues:
        sources = _collect(document)
        for mode, tokens in resolved.items():
            seen = {}
            for path, token in tokens.items():
                raw_type, raw_value = sources[f"{mode}.{path}"]
                signature = (raw_type, json.dumps(raw_value, sort_keys=True,
                                                       separators=(",", ":"), allow_nan=False))
                if signature in seen:
                    proposals.append({"kind": "shared-alias", "mode": mode,
                                      "paths": [seen[signature], path], "value": deepcopy(raw_value)})
                else:
                    seen[signature] = path
            numbers = [(path, token["value"]) for path, token in tokens.items()
                       if token["type"] == "number"]
            for index, (first_path, first) in enumerate(numbers):
                for second_path, second in numbers[index + 1:]:
                    if first != second and abs(first - second) <= max(abs(first), abs(second)) * 0.05:
                        proposals.append({"kind": "near-value", "mode": mode,
                                          "paths": [first_path, second_path], "values": [first, second]})
    return {"status": "blocked" if issues else "passed", "issues": issues, "proposals": proposals}
