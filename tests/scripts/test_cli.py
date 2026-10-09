import json
import shutil
from pathlib import Path

from PIL import Image

from figma_core.approvals import content_hash
from figma_core.cli import main
from figma_core.documents import read_json
from figma_core.storage import file_hash


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "core-v1"


def test_invalid_bundle_exits_two(tmp_path):
    assert main(["validate", "--bundle", str(tmp_path)]) == 2


def test_unknown_command_exits_two():
    assert main(["unknown"]) == 2


def test_unavailable_budget_ledger_is_typed_error(tmp_path):
    assert main(["reserve", "--ledger", str(tmp_path / "missing" / "budget.sqlite"),
                 "--window", "observed", "--limit", "1", "--request-id", "one"]) == 2


def test_complete_fixture_and_modes(capsys):
    assert main(["validate", "--bundle", str(FIXTURE)]) == 0
    assert main(["audit", "--bundle", str(FIXTURE), "--mode", "light"]) == 0
    assert "passed" in capsys.readouterr().out


def test_manifest_mode_mismatch_blocks_audit(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "bundle")
    manifest = read_json(tmp_path / "bundle" / "manifest.json")
    manifest["tokenModes"] = ["dark"]
    (tmp_path / "bundle" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["audit", "--bundle", str(tmp_path / "bundle"), "--mode", "dark"]) == 2


def test_partial_bundle_validation_is_blocked(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "bundle")
    bundle = tmp_path / "bundle"
    manifest = read_json(bundle / "manifest.json")
    manifest["status"] = "partial"
    manifest["nodes"][0]["status"] = "pending"
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate", "--bundle", str(bundle)]) == 2


def test_compare_blocked_exits_two(tmp_path):
    path = tmp_path / "missing.json"
    assert main(["compare", "--bundle", str(FIXTURE), "--reference", str(path),
                 "--actual", str(path), "--reference-meta", str(path),
                 "--actual-meta", str(path), "--policy", str(path),
                 "--policy-approval", str(path), "--output", str(tmp_path / "run")]) == 2


def test_correction_requires_reference_approval(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "bundle")
    bundle = tmp_path / "bundle"
    assert main(["correction", "--bundle", str(bundle), "--node-id", "1:2",
                 "--policy", str(bundle / "comparison-policy.json"),
                 "--policy-approval", str(bundle / "policy-approval.json")]) == 2


def _approval(kind, value, modes):
    return {"schemaVersion": 1, "kind": kind, "contentHash": content_hash(value),
            "owner": "synthetic fixture", "evidence": "synthetic-test",
            "approvedAt": "2026-10-09T00:00:00Z", "modes": modes, "deviations": []}


def _approved_bundle(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURE, bundle)
    policy = read_json(bundle / "comparison-policy.json")
    tokens = read_json(bundle / "tokens.json")
    node = "components/button/default"
    identity = {"referenceHash": file_hash(bundle / node / "reference.png"),
                "metaHash": file_hash(bundle / node / "meta.json")}
    approvals = {"policy-approval.json": _approval("policy", policy, []),
                 "tokens-approval.json": _approval("tokens", tokens, ["light", "dark"]),
                 f"{node}/reference-approval.json": _approval("reference", identity, ["light"])}
    manifest = read_json(bundle / "manifest.json")
    for name, value in approvals.items():
        (bundle / name).write_text(json.dumps(value), encoding="utf-8")
        manifest["files"][name] = file_hash(bundle / name)
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return bundle


def test_correction_approval_and_limit(tmp_path):
    bundle = _approved_bundle(tmp_path)
    command = ["correction", "--bundle", str(bundle), "--node-id", "synthetic:component:button",
               "--policy", str(bundle / "comparison-policy.json"),
               "--policy-approval", str(bundle / "policy-approval.json")]
    for _ in range(4):
        assert main(command) == 0
    assert main(command) == 2


def test_correction_rejects_unrecorded_policy_path(tmp_path):
    bundle = _approved_bundle(tmp_path)
    other = tmp_path / "policy.json"
    shutil.copyfile(bundle / "comparison-policy.json", other)
    assert main(["correction", "--bundle", str(bundle), "--node-id", "synthetic:component:button",
                 "--policy", str(other), "--policy-approval", str(bundle / "policy-approval.json")]) == 2


def test_compare_exit_codes_and_human_review(tmp_path, capsys):
    bundle = _approved_bundle(tmp_path)
    node = bundle / "components/button/default"
    actual = tmp_path / "actual.png"
    shutil.copyfile(node / "reference.png", actual)
    command = ["compare", "--bundle", str(bundle), "--reference", str(node / "reference.png"),
               "--actual", str(actual), "--reference-meta", str(node / "meta.json"),
               "--actual-meta", str(node / "meta.json"),
               "--policy", str(bundle / "comparison-policy.json"),
               "--policy-approval", str(bundle / "policy-approval.json")]
    assert main([*command, "--output", str(tmp_path / "pass")]) == 0
    assert read_json(tmp_path / "pass/report.json")["visualReview"] == "not_run"
    Image.new("RGBA", (20, 20), "red").save(actual)
    assert main([*command, "--output", str(tmp_path / "fail")]) == 1
