import pytest

from fixtures.make_core_fixture import make_fixture
from figma_core.approvals import content_hash
from figma_core.documents import read_json
from figma_core.errors import CoreError
from figma_core.storage import atomic_json, file_hash


def approve(root):
    tokens = read_json(root / "tokens.json")
    atomic_json(root, "tokens-approval.json", {"schemaVersion": 1, "kind": "tokens",
        "contentHash": content_hash(tokens), "owner": "synthetic-test", "evidence": "fixture-only",
        "approvedAt": "2026-10-09T00:00:00Z", "modes": ["light", "dark"], "deviations": []})
    refresh(root, "tokens-approval.json")


def refresh(root, name):
    manifest = read_json(root / "manifest.json")
    manifest["files"][name] = file_hash(root / name)
    atomic_json(root, "manifest.json", manifest)


def test_export_requires_current_token_approval(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    with pytest.raises(CoreError, match="approval"):
        export_adapter(root)


def test_approved_export_preserves_modes_and_verified_node_data(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    receipt = export_adapter(root)
    assert receipt["status"] == "passed"
    assert receipt["freshness"] == "unverified"
    assert set(receipt["resolvedByMode"]) == {"light", "dark"}
    assert receipt["tokenHash"] == content_hash(read_json(root / "tokens.json"))
    assert receipt["manifestHash"] == content_hash(read_json(root / "manifest.json"))
    node = receipt["nodes"][0]
    assert node["referenceHash"] == file_hash(root / node["path"] / "reference.png")
    assert node["context"] == (root / node["path"] / "context.md").read_text()
    assert receipt["fonts"] == {"schemaVersion": 1, "fonts": []}


def test_changed_tokens_reject_old_approval(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    tokens = read_json(root / "tokens.json")
    tokens["base"]["space"]["small"]["$value"]["value"] = 9
    atomic_json(root, "tokens.json", tokens)
    refresh(root, "tokens.json")
    with pytest.raises(CoreError, match="approval"):
        export_adapter(root)


def test_partial_bundle_rejected(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    manifest = read_json(root / "manifest.json")
    manifest["status"] = "partial"
    atomic_json(root, "manifest.json", manifest)
    with pytest.raises(CoreError):
        export_adapter(root)


def test_missing_mode_rejected(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    tokens = read_json(root / "tokens.json")
    del tokens["dark"]
    atomic_json(root, "tokens.json", tokens)
    refresh(root, "tokens.json")
    with pytest.raises(CoreError) as error:
        export_adapter(root)
    assert error.value.code == "TOKEN_MODE"


def test_cli_exports_and_verifies_approval(tmp_path, capsys):
    import json
    from figma_core.cli import main
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    assert main(["export-adapter", "--bundle", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["schemaVersion"] == 1
    assert main(["verify-approval", "--document", str(root / "tokens.json"),
                 "--approval", str(root / "tokens-approval.json"), "--kind", "tokens"]) == 0
    assert main(["verify-approval", "--document", str(root / "tokens.json"),
                 "--approval", str(root / "tokens-approval.json"), "--kind", "policy"]) == 2


@pytest.mark.parametrize("paths", ['{}', '[1]', '["../outside"]', '["a", "A"]', '["a", "a/b"]'])
def test_cli_rejects_unsafe_paths_without_writing(tmp_path, paths):
    from figma_core.cli import main
    assert main(["check-paths", "--root", str(tmp_path), "--paths-json", paths]) == 2
    assert list(tmp_path.iterdir()) == []


def test_cli_returns_absolute_paths_without_writing(tmp_path, capsys):
    import json
    from figma_core.cli import main
    assert main(["check-paths", "--root", str(tmp_path), "--paths-json", '["theme/Tokens.kt"]']) == 0
    assert json.loads(capsys.readouterr().out)["paths"] == [str(tmp_path / "theme/Tokens.kt")]
    assert list(tmp_path.iterdir()) == []


def test_tampered_node_context_rejected(tmp_path):
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / "bundle")
    approve(root)
    (root / "screens/home/context.md").write_text("untrusted new content")
    with pytest.raises(CoreError, match="hash mismatch"):
        export_adapter(root)
