import json

import pytest

from figma_core.errors import CoreError
from figma_core.documents import read_json
from figma_core.schema import validate_bundle, validate_document
from fixtures.make_core_fixture import make_fixture


def test_future_schema_is_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest = read_json(root / "manifest.json")
    manifest["schemaVersion"] = 99
    with pytest.raises(CoreError, match="schemaVersion"):
        validate_document("manifest", manifest)


def test_fixture_has_two_screens_and_three_components(tmp_path):
    bundle = validate_bundle(make_fixture(tmp_path / "bundle"))
    kinds = [node["kind"] for node in bundle["nodes"]]
    assert kinds.count("screen") == 2
    assert kinds.count("component") == 3


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"x":1,"x":2}', encoding="utf-8")
    with pytest.raises(CoreError, match="duplicate"):
        read_json(path)


def test_missing_meta_field_is_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    path = root / "screens/home/meta.json"
    meta = read_json(path)
    del meta["scale"]
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(CoreError, match="scale"):
        validate_bundle(root)


def test_duplicate_node_ids_are_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    path = root / "manifest.json"
    manifest = read_json(path)
    manifest["nodes"][1]["id"] = manifest["nodes"][0]["id"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CoreError, match="Duplicate node"):
        validate_bundle(root)


def test_bad_hash_syntax_is_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest = read_json(root / "manifest.json")
    manifest["files"]["tokens.json"] = "not-a-sha256"
    with pytest.raises(CoreError, match="files"):
        validate_document("manifest", manifest)


def test_nonfinite_number_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"value":NaN}', encoding="utf-8")
    with pytest.raises(CoreError, match="non-finite"):
        read_json(path)


def test_unknown_property_is_rejected(tmp_path):
    manifest = read_json(make_fixture(tmp_path / "bundle") / "manifest.json")
    manifest["secret"] = "should not appear in error"
    with pytest.raises(CoreError, match="Invalid value") as error:
        validate_document("manifest", manifest)
    assert "should not appear" not in str(error.value)


def test_logical_pixel_inconsistency_is_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    path = root / "screens/home/meta.json"
    meta = read_json(path)
    meta["scale"] = 2
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(CoreError, match="Logical/pixel"):
        validate_bundle(root)


def test_partial_bundle_allows_pending_capture(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    path = root / "manifest.json"
    manifest = read_json(path)
    manifest["status"] = "partial"
    node = manifest["nodes"][0]
    node["status"] = "pending"
    for suffix in ("context.md", "reference.png", "meta.json"):
        relative = f"{node['path']}/{suffix}"
        del manifest["files"][relative]
        (root / relative).unlink()
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert validate_bundle(root)["status"] == "partial"


def test_comparison_region_must_fit_pixel_extent(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    path = root / "comparison-policy.json"
    policy = read_json(path)
    policy["critical"] = [{"id": "control", "box": [0, 0, 21, 20], "maxChangedRatio": 0}]
    path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(CoreError, match="region exceeds pixel size"):
        validate_bundle(root)


def test_timestamp_must_explicitly_be_utc(tmp_path):
    manifest = read_json(make_fixture(tmp_path / "bundle") / "manifest.json")
    manifest["extractedAt"] = "2026-10-09T00:00:00+02:00"
    with pytest.raises(CoreError, match="UTC timestamp"):
        validate_document("manifest", manifest)
