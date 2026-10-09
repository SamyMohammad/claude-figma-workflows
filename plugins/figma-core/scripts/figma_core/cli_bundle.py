"""Bundle validation and token audit commands."""

from pathlib import Path

from .documents import read_json
from .errors import CoreError
from .paths import safe_path
from .schema import validate_bundle
from .tokens import audit_tokens, resolve_tokens


def token_modes(manifest: dict, tokens: dict) -> set[str]:
    selected = {name for name in ("light", "dark") if name in tokens}
    if set(manifest["tokenModes"]) != selected:
        raise CoreError("TOKEN_MODE", "Manifest token modes differ from token groups")
    return selected


def validate(bundle: Path) -> dict:
    manifest = validate_bundle(bundle)
    token_modes(manifest, read_json(safe_path(bundle, "tokens.json")))
    return {"status": "passed" if manifest["status"] == "complete" else "blocked",
            "bundleStatus": manifest["status"],
            "freshness": manifest["freshness"]}


def audit(bundle: Path, mode: str) -> dict:
    manifest = validate_bundle(bundle)
    tokens = read_json(safe_path(bundle, "tokens.json"))
    if mode not in token_modes(manifest, tokens):
        raise CoreError("TOKEN_MODE", "Requested mode is unavailable")
    result = audit_tokens(tokens)
    if result["status"] == "passed":
        result["resolved"] = resolve_tokens(tokens, mode)
    result["mode"] = mode
    result["freshness"] = manifest["freshness"]
    return result
