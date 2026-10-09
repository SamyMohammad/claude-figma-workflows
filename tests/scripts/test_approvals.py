import pytest

from figma_core.approvals import content_hash, require_approval
from figma_core.errors import CoreError


def _approval(value, modes=None):
    return {"schemaVersion": 1, "kind": "tokens", "contentHash": content_hash(value),
            "owner": "fixture", "evidence": "synthetic-test", "approvedAt": "2026-10-09T00:00:00Z",
            "modes": modes or ["light"], "deviations": []}


def test_edited_token_invalidates_approval():
    value = {"light": {"x": {"$type": "number", "$value": 1}}}
    approval = _approval(value)
    value["light"]["x"]["$value"] = 2
    with pytest.raises(CoreError, match="approval"):
        require_approval(value, approval, "tokens")


def test_key_order_does_not_invalidate_approval():
    value = {"light": {"x": {"$type": "number", "$value": 1}}}
    approval = _approval(value)
    reordered = {"light": {"x": {"$value": 1, "$type": "number"}}}
    require_approval(reordered, approval, "tokens")


def test_selected_modes_must_match():
    value = {"light": {"x": {"$type": "number", "$value": 1}}, "dark": {"x": {"$type": "number", "$value": 2}}}
    with pytest.raises(CoreError, match="modes"):
        require_approval(value, _approval(value), "tokens")
