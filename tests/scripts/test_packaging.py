import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "figma-core"
SKILLS = {"figma-extract", "token-audit", "visual-verify", "figma-build", "adapter-export"}


def test_marketplace_exports_existing_core_skills():
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())

    assert marketplace["name"] == "claude-figma-workflows"
    assert {"name": "figma-core", "source": "./plugins/figma-core"} in marketplace["plugins"]
    assert manifest["name"] == "figma-core"
    assert manifest["version"] == "0.1.1"
    skill_files = list((PLUGIN / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skill_files} == SKILLS
    for skill_file in skill_files:
        assert f"name: {skill_file.parent.name}" in skill_file.read_text(encoding="utf-8")


def test_installed_plugin_carries_exact_runtime_lock():
    assert (PLUGIN / "requirements-core.lock").read_bytes() == (
        ROOT / "requirements-core.lock"
    ).read_bytes()


def test_absolute_plugin_cli_validates_from_consumer_with_spaces(tmp_path):
    consumer = tmp_path / "consumer directory with spaces"
    consumer.mkdir()
    installed_plugin = tmp_path / "plugin with spaces"
    shutil.copytree(PLUGIN, installed_plugin, ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run(
        [
            sys.executable,
            str(installed_plugin / "scripts" / "core.py"),
            "validate",
            "--bundle",
            str(ROOT / "tests" / "fixtures" / "core-v1"),
        ],
        cwd=consumer,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "bundleStatus": "complete",
        "freshness": "unverified",
        "status": "passed",
    }
