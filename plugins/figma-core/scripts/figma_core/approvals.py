"""Content-bound approval record validation."""

import hashlib
import json

from .errors import CoreError
from .schema import validate_document


def content_hash(value: dict) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def require_approval(value: dict, approval: dict, kind: str) -> None:
    validate_document("approval", approval)
    if not approval["owner"].strip() or not approval["evidence"].strip():
        raise CoreError("APPROVAL_INVALID", "Approval owner/evidence must be nonempty")
    if approval["kind"] != kind or approval["contentHash"] != content_hash(value):
        raise CoreError("APPROVAL_INVALID", "Content approval kind or hash mismatch")
    if kind == "tokens":
        modes = {mode for mode in ("light", "dark") if mode in value}
        if set(approval["modes"]) != modes:
            raise CoreError("APPROVAL_INVALID", "Approval selected modes mismatch")
