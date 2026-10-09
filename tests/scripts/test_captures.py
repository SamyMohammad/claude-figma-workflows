from copy import deepcopy
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from figma_core.approvals import content_hash
from figma_core.captures import compare_capture, require_matching_capture
from figma_core.documents import read_json
from figma_core.errors import CoreError
from figma_core.storage import file_hash


@pytest.fixture
def meta():
    return read_json(Path(__file__).parents[1] / "fixtures/core-v1/components/button/default/meta.json")


def _write(path, value):
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "bundle"
    shutil.copytree(Path(__file__).parents[1] / "fixtures/core-v1", root)
    tokens = read_json(root / "tokens.json")
    approval = {"schemaVersion": 1, "kind": "tokens", "contentHash": content_hash(tokens),
                "owner": "synthetic fixture", "evidence": "synthetic-test", "approvedAt": "2026-10-09T00:00:00Z",
                "modes": ["light", "dark"], "deviations": []}
    _write(root / "tokens-approval.json", approval)
    manifest = read_json(root / "manifest.json")
    manifest["files"]["tokens-approval.json"] = file_hash(root / "tokens-approval.json")
    _write(root / "manifest.json", manifest)
    return root


def _run(bundle, output, actual_meta=None, policy=None, reference=None, actual=None):
    reference = reference or bundle / "components/button/default/reference.png"
    actual = actual or reference
    reference_meta = read_json(bundle / "components/button/default/meta.json")
    actual_meta = actual_meta or deepcopy(reference_meta)
    policy = policy or read_json(bundle / "comparison-policy.json")
    approval = {"schemaVersion": 1, "kind": "policy", "contentHash": content_hash(policy),
                "owner": "synthetic fixture", "evidence": "synthetic-test", "approvedAt": "2026-10-09T00:00:00Z",
                "modes": [], "deviations": []}
    return compare_capture(bundle, reference, actual, reference_meta, actual_meta, policy, approval, output)


@pytest.mark.parametrize("field,value", [("locale", "ar-EG"), ("crop", [1, 0, 19, 20]),
                                         ("fontHashes", {"x.ttf": "a" * 64}),
                                         ("pixelSize", [21, 20])])
def test_capture_mismatch_blocks(meta, field, value):
    actual = deepcopy(meta)
    actual[field] = value
    with pytest.raises(CoreError):
        require_matching_capture(meta, actual)


def test_report_contains_hashes_and_preserves_human_review(bundle, tmp_path):
    run = tmp_path / "run"
    report = _run(bundle, run)
    assert report["status"] == "passed"
    assert report["visualReview"] == "not_run"
    assert report["geometry"] == "not_run"
    assert report["referenceHash"] == file_hash(bundle / "components/button/default/reference.png")
    assert set(path.name for path in run.iterdir()) == {
        "reference.png", "actual.png", "diff.png", "overlay.png", "report.json", "report.md"}
    with pytest.raises(CoreError, match="exists"):
        _run(bundle, run)


def test_mutated_reference_and_policy_block_without_metrics(bundle, tmp_path):
    reference = bundle / "components/button/default/reference.png"
    reference.write_bytes(reference.read_bytes() + b"changed")
    report = _run(bundle, tmp_path / "changed-reference")
    assert report["status"] == "blocked" and "changedRatio" not in report
    shutil.copyfile(Path(__file__).parents[1] / "fixtures/core-v1/components/button/default/reference.png", reference)
    policy = read_json(bundle / "comparison-policy.json")
    policy["maxChangedRatio"] = 0.5
    report = _run(bundle, tmp_path / "changed-policy", policy=policy)
    assert report["status"] == "blocked" and "changedRatio" not in report


def test_actual_dimension_mismatch_blocks(bundle, tmp_path, meta):
    actual_meta = deepcopy(meta)
    actual_meta["pixelSize"] = [21, 20]
    actual_meta["logicalSize"] = [21, 20]
    report = _run(bundle, tmp_path / "wrong-size", actual_meta=actual_meta)
    assert report["status"] == "blocked" and "changedRatio" not in report


@pytest.mark.parametrize("field,value", [("locale", "ar-EG"), ("crop", [1, 0, 19, 20]),
                                         ("fontHashes", {"fonts/test.ttf": "a" * 64})])
def test_changed_capture_conditions_block_bundle_run(bundle, tmp_path, meta, field, value):
    actual_meta = deepcopy(meta)
    actual_meta[field] = value
    report = _run(bundle, tmp_path / field, actual_meta=actual_meta)
    assert report["status"] == "blocked" and "changedRatio" not in report


def test_png_dimensions_must_match_declared_capture(bundle, tmp_path):
    actual = tmp_path / "actual.png"
    Image.new("RGBA", (21, 20), "white").save(actual)
    report = _run(bundle, tmp_path / "png-size", actual=actual)
    assert report["status"] == "blocked" and report["code"] == "IMAGE_INVALID"


def test_output_cannot_overlap_sources(bundle):
    with pytest.raises(CoreError, match="overlaps"):
        _run(bundle, bundle / "run")


def test_forged_reference_metadata_blocks(bundle, tmp_path):
    reference = bundle / "components/button/default/reference.png"
    meta = read_json(bundle / "components/button/default/meta.json")
    meta["locale"] = "ar-EG"
    policy = read_json(bundle / "comparison-policy.json")
    approval = {"schemaVersion": 1, "kind": "policy", "contentHash": content_hash(policy),
                "owner": "synthetic fixture", "evidence": "synthetic-test", "approvedAt": "2026-10-09T00:00:00Z",
                "modes": [], "deviations": []}
    result = compare_capture(bundle, reference, reference, meta, meta, policy, approval, tmp_path / "forged")
    assert result["status"] == "blocked" and result["code"] == "CAPTURE_MISMATCH"


def test_unapproved_policy_blocks(bundle, tmp_path):
    reference = bundle / "components/button/default/reference.png"
    meta = read_json(bundle / "components/button/default/meta.json")
    policy = read_json(bundle / "comparison-policy.json")
    approval = {"schemaVersion": 1, "kind": "policy", "contentHash": "a" * 64,
                "owner": "synthetic fixture", "evidence": "synthetic-test", "approvedAt": "2026-10-09T00:00:00Z",
                "modes": [], "deviations": []}
    result = compare_capture(bundle, reference, reference, meta, meta, policy, approval, tmp_path / "unapproved")
    assert result["status"] == "blocked" and result["code"] == "APPROVAL_INVALID"


@pytest.mark.parametrize("status,license", [("missing", "approved"), ("available", "restricted")])
def test_unavailable_or_unlicensed_font_blocks(bundle, tmp_path, status, license):
    font_file = bundle / "fonts/test.ttf"
    font_file.parent.mkdir()
    font_file.write_bytes(b"synthetic font")
    digest = file_hash(font_file)
    fonts = read_json(bundle / "fonts.json")
    fonts["fonts"] = [{"family": "Test", "weight": 400, "path": "fonts/test.ttf",
                       "sha256": digest, "status": status, "license": license}]
    _write(bundle / "fonts.json", fonts)
    manifest = read_json(bundle / "manifest.json")
    manifest["files"]["fonts.json"] = file_hash(bundle / "fonts.json")
    manifest["files"]["fonts/test.ttf"] = digest
    _write(bundle / "manifest.json", manifest)
    report = _run(bundle, tmp_path / f"font-{status}-{license}")
    assert report["status"] == "blocked" and "changedRatio" not in report
