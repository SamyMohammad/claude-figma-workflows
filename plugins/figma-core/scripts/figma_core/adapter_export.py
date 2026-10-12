"""Export a portable receipt from a complete, explicitly approved bundle."""

from pathlib import Path

from .approvals import content_hash, require_approval
from .cli_bundle import token_modes
from .documents import read_json
from .errors import CoreError
from .paths import safe_path
from .schema import validate_bundle
from .tokens import audit_tokens, resolve_tokens


def export_adapter(bundle: Path) -> dict:
    manifest = validate_bundle(bundle)
    if manifest["status"] != "complete":
        raise CoreError("BUNDLE_INVALID", "Adapter export requires a complete bundle")
    tokens = read_json(safe_path(bundle, "tokens.json"))
    modes = token_modes(manifest, tokens)
    if audit_tokens(tokens)["status"] != "passed":
        raise CoreError("TOKEN_INVALID", "Adapter export requires valid tokens")
    approval_path = safe_path(bundle, "tokens-approval.json")
    if not approval_path.is_file():
        raise CoreError("APPROVAL_INVALID", "Token approval is required")
    require_approval(tokens, read_json(approval_path), "tokens")
    nodes = []
    for node in manifest["nodes"]:
        directory = node["path"]
        try:
            context = safe_path(bundle, f"{directory}/context.md").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise CoreError("DOCUMENT_INVALID", "Node context is unreadable") from None
        nodes.append({**{key: node[key] for key in ("id", "kind", "variant", "path")},
                      "referenceHash": manifest["files"][f"{directory}/reference.png"],
                      "meta": read_json(safe_path(bundle, f"{directory}/meta.json")),
                      "context": context})
    return {"schemaVersion": 1, "status": "passed", "freshness": "unverified",
            "tokenHash": content_hash(tokens), "manifestHash": content_hash(manifest),
            "resolvedByMode": {mode: resolve_tokens(tokens, mode) for mode in sorted(modes)},
            "fonts": read_json(safe_path(bundle, "fonts.json")),
            "assets": read_json(safe_path(bundle, "assets/manifest.json")),
            "components": read_json(safe_path(bundle, "component-map.json")), "nodes": nodes}
