"""Comparison and bounded correction entry points."""

from pathlib import Path

from .approvals import content_hash, require_approval
from .captures import compare_capture
from .documents import read_json
from .errors import CoreError
from .iterations import record_correction
from .paths import safe_path
from .schema import validate_bundle
from .storage import file_hash
from .cli_bundle import token_modes


def compare(args) -> dict:
    return compare_capture(args.bundle, args.reference, args.actual,
                           read_json(args.reference_meta), read_json(args.actual_meta),
                           read_json(args.policy), read_json(args.policy_approval), args.output)


def correction(bundle: Path, node_id: str, policy_path: Path, approval_path: Path) -> dict:
    manifest = validate_bundle(bundle)
    if manifest["status"] != "complete":
        raise CoreError("BUNDLE_INCOMPLETE", "Correction requires a complete bundle")
    node = next((item for item in manifest["nodes"] if item["id"] == node_id
                 and item["status"] == "complete"), None)
    if node is None:
        raise CoreError("NODE_UNKNOWN", "Correction node is unavailable")
    expected_policy = safe_path(bundle, "comparison-policy.json")
    expected_approval = safe_path(bundle, "policy-approval.json")
    if policy_path.resolve() != expected_policy.resolve() or approval_path.resolve() != expected_approval.resolve():
        raise CoreError("POLICY_INVALID", "Correction requires recorded policy and approval paths")
    for name in ("policy-approval.json", "tokens-approval.json"):
        if name not in manifest["files"]:
            raise CoreError("APPROVAL_INVALID", "Recorded approval is missing")
    policy = read_json(expected_policy)
    require_approval(policy, read_json(expected_approval), "policy")
    tokens = read_json(safe_path(bundle, "tokens.json"))
    token_modes(manifest, tokens)
    token_approval = read_json(safe_path(bundle, "tokens-approval.json"))
    require_approval(tokens, token_approval, "tokens")
    meta_path = safe_path(bundle, f'{node["path"]}/meta.json')
    reference_path = safe_path(bundle, f'{node["path"]}/reference.png')
    reference_approval_name = f'{node["path"]}/reference-approval.json'
    if reference_approval_name not in manifest["files"]:
        raise CoreError("APPROVAL_INVALID", "Recorded source-target approval is missing")
    meta = read_json(meta_path)
    if meta["nodeId"] != node_id or meta["theme"] not in token_approval["modes"]:
        raise CoreError("APPROVAL_INVALID", "Node identity or theme is not approved")
    reference_hash = file_hash(reference_path)
    identity = {"referenceHash": reference_hash, "metaHash": file_hash(meta_path)}
    reference_approval = read_json(safe_path(bundle, reference_approval_name))
    require_approval(identity, reference_approval, "reference")
    if set(reference_approval["modes"]) != {meta["theme"]}:
        raise CoreError("APPROVAL_INVALID", "Source-target approval mode differs")
    ledger = safe_path(bundle, ".workflow/corrections.sqlite3")
    count = record_correction(ledger, node_id, reference_hash, content_hash(policy))
    return {"status": "passed", "correction": count, "remaining": 4 - count}
