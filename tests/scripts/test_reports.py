from figma_core.approvals import content_hash
from figma_core.reports import evidence_payload


def test_reference_replacement_invalidates_evidence():
    first = evidence_payload("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    second = evidence_payload("e" * 64, "b" * 64, "c" * 64, "d" * 64)
    assert content_hash(first) != content_hash(second)
