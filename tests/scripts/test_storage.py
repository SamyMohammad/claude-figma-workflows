import json
import os
import subprocess
from hashlib import sha256

import pytest

from figma_core.errors import CoreError
from figma_core.paths import check_collisions, safe_path
from figma_core.storage import atomic_json
from fixtures.make_core_fixture import make_fixture
from figma_core.schema import validate_bundle


@pytest.mark.parametrize("path", ["../escape", "C:/escape", "/escape", "a\\..\\escape", "a:stream", "a/./b", "CON", "name. ", "a?b", "a*b", "a<b", "a>b", "a|b"])
def test_external_paths_are_rejected(tmp_path, path):
    with pytest.raises(CoreError):
        safe_path(tmp_path, path)


def test_atomic_json_preserves_previous_file_on_replace_failure(tmp_path, monkeypatch):
    target = tmp_path / "manifest.json"
    target.write_text('{"old": true}', encoding="utf-8")

    def fail(*args):
        raise OSError("replace failed")

    monkeypatch.setattr("figma_core.storage.os.replace", fail)
    with pytest.raises(CoreError, match="replace failed"):
        atomic_json(tmp_path, "manifest.json", {"new": True})
    assert json.loads(target.read_text(encoding="utf-8")) == {"old": True}
    assert list(tmp_path.iterdir()) == [target]


def test_changed_recorded_file_is_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    (root / "tokens.json").write_text("{}", encoding="utf-8")
    with pytest.raises(CoreError, match="hash mismatch"):
        validate_bundle(root)


def test_case_folded_paths_are_rejected(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["Tokens.json"] = manifest["files"]["tokens.json"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CoreError, match="collision"):
        validate_bundle(root)


def test_case_folded_file_directory_collision_is_rejected():
    with pytest.raises(CoreError, match="collision"):
        check_collisions(["A", "a/x"])


def test_case_folded_directory_alias_is_rejected():
    with pytest.raises(CoreError, match="collision"):
        check_collisions(["A/x", "a/y"])


def test_symlink_escape_is_rejected_when_supported(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "linked").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"host cannot create directory symlink: {error}")
    with pytest.raises(CoreError):
        safe_path(root, "linked/file.json")


def test_complete_bundle_rejects_missing_asset(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    asset_path = root / "assets/manifest.json"
    assets = json.loads(asset_path.read_text(encoding="utf-8"))
    assets["assets"] = [{"nodeId": "synthetic:screen:home", "path": "assets/missing.png",
                         "mimeType": "image/png", "sha256": "a" * 64, "status": "missing"}]
    asset_path.write_text(json.dumps(assets), encoding="utf-8")
    with pytest.raises(CoreError, match="missing assets"):
        validate_bundle(root)


@pytest.mark.parametrize("kind", ["asset", "font"])
def test_available_entry_hash_must_match_bytes(tmp_path, kind):
    root = make_fixture(tmp_path / "bundle")
    relative = "assets/sample.png" if kind == "asset" else "fonts/sample.ttf"
    item_path = root / relative
    item_path.parent.mkdir(exist_ok=True)
    item_path.write_bytes(b"actual content")
    document_path = root / ("assets/manifest.json" if kind == "asset" else "fonts.json")
    document = json.loads(document_path.read_text(encoding="utf-8"))
    if kind == "asset":
        document["assets"] = [{"nodeId": "synthetic:screen:home", "path": relative,
                               "mimeType": "image/png", "sha256": "a" * 64,
                               "status": "available"}]
    else:
        document["fonts"] = [{"family": "Synthetic", "weight": 400,
                              "path": relative, "sha256": "a" * 64,
                              "status": "available", "license": "approved"}]
    document_path.write_text(json.dumps(document), encoding="utf-8")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for path in (item_path, document_path):
        manifest["files"][path.relative_to(root).as_posix()] = sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CoreError, match="hash mismatch"):
        validate_bundle(root)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction test")
def test_junction_escape_is_rejected_when_supported(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(root / "linked"),
                             str(outside)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        pytest.skip(f"host cannot create junction: {result.stderr or result.stdout}")
    with pytest.raises(CoreError):
        safe_path(root, "linked/file.json")
