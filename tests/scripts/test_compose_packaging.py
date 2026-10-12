import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "plugins" / "figma-core"
PLUGIN = ROOT / "plugins" / "figma-compose"
SKILLS = {"build", "figma-to-composable", "compose-capture", "compose-review"}


def frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{path} has no frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, text[match.end():]


def test_marketplace_registers_core_and_compose_only():
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert marketplace["name"] == "claude-figma-workflows"
    assert marketplace["plugins"] == [
        {"name": "figma-core", "source": "./plugins/figma-core"},
        {"name": "figma-compose", "source": "./plugins/figma-compose"},
    ]
    for entry in marketplace["plugins"]:
        assert (ROOT / entry["source"] / ".claude-plugin" / "plugin.json").is_file()


def test_manifest_declares_core_dependency():
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "figma-compose"
    assert manifest["version"] == "0.1.0"
    assert manifest["description"]
    assert manifest["author"] == {"name": "Claude Figma Workflows"}
    assert manifest["dependencies"] == ["figma-core"]


def test_skills_exist_with_matching_frontmatter():
    files = list((PLUGIN / "skills").glob("*/SKILL.md"))
    assert {p.parent.name for p in files} == SKILLS
    for path in files:
        fields, body = frontmatter(path)
        assert fields["name"] == path.parent.name
        assert fields["description"].startswith("Use when")
        assert body.strip()


def test_skills_use_plugin_root_and_state_unautomated_limits():
    for name in SKILLS:
        _, body = frontmatter(PLUGIN / "skills" / name / "SKILL.md")
        assert body.count("```") % 2 == 0
    _, build = frontmatter(PLUGIN / "skills" / "build" / "SKILL.md")
    assert "${CLAUDE_PLUGIN_ROOT}/scripts/compose.py" in build
    assert "--core-command-json" in build
    assert "requirements-core.lock" in build
    assert "pip check" in build
    assert "docs/design-decisions/" in build
    assert "Not automated" in build
    assert "scanner" in build.lower()
    _, capture = frontmatter(PLUGIN / "skills" / "compose-capture" / "SKILL.md")
    assert "prepare-capture" in capture
    assert "ComposeCaptureTest.kt" in capture


def test_referenced_scripts_schemas_and_templates_exist():
    assert (PLUGIN / "scripts" / "compose.py").is_file()
    assert (PLUGIN / "templates" / "ComposeCaptureTest.kt").is_file()
    for schema in ("config", "receipt", "capture-receipt"):
        json.loads((PLUGIN / "schemas" / f"{schema}.schema.json").read_text())
    for text in (frontmatter(PLUGIN / "skills" / n / "SKILL.md")[1] for n in SKILLS):
        for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)", text):
            assert (PLUGIN / ref).exists(), ref


def test_compose_lock_is_exact_copy_of_core_lock():
    assert (PLUGIN / "requirements-core.lock").read_bytes() == (CORE / "requirements-core.lock").read_bytes()


def test_installed_compose_cli_runs_from_path_with_spaces(tmp_path):
    consumer = tmp_path / "consumer directory with spaces"
    consumer.mkdir()
    installed = tmp_path / "compose plugin with spaces"
    shutil.copytree(PLUGIN, installed, ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run(
        [sys.executable, str(installed / "scripts" / "compose.py"), "generate",
         "--bundle", str(consumer / "missing"), "--receipt", str(consumer / "r.json"),
         "--config", str(consumer / "c.json"), "--project", str(consumer),
         "--core-command-json", json.dumps([sys.executable, str(CORE / "scripts" / "core.py")])],
        cwd=consumer, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "blocked" and report["code"]
    assert "Traceback" not in result.stderr


def _fake_cache(tmp_path, core_versions=("0.1.1",)):
    cache = tmp_path / "cache dir" / "market"
    compose = cache / "figma-compose" / "0.1.0"
    (compose / "scripts").mkdir(parents=True)
    for version in core_versions:
        (cache / "figma-core" / version / "scripts").mkdir(parents=True)
        (cache / "figma-core" / version / "scripts" / "core.py").write_text("")
    return compose


def test_locate_core_prefers_sibling_cache_and_newest_version(tmp_path):
    from locate_core import locate

    compose = _fake_cache(tmp_path, ("0.1.1", "0.1.10", "0.1.2"))
    command = locate("py thon", root=compose, config_dir=tmp_path / "none")
    assert command == ["py thon", str(compose.parent.parent / "figma-core" / "0.1.10" / "scripts" / "core.py")]


def test_locate_core_falls_back_to_installed_registry(tmp_path):
    from locate_core import locate

    lone = tmp_path / "elsewhere" / "figma-compose" / "0.1.0"
    lone.mkdir(parents=True)
    core = tmp_path / "core install" / "scripts"
    core.mkdir(parents=True)
    (core / "core.py").write_text("")
    config = tmp_path / "cfg"
    (config / "plugins").mkdir(parents=True)
    (config / "plugins" / "installed_plugins.json").write_text(json.dumps(
        {"version": 2, "plugins": {"figma-core@m": [{"installPath": str(core.parent)}]}}))
    assert locate("python", root=lone, config_dir=config) == ["python", str(core / "core.py")]


def test_locate_core_blocks_when_missing(tmp_path):
    from locate_core import locate

    lone = tmp_path / "x" / "figma-compose" / "0.1.0"
    lone.mkdir(parents=True)
    assert locate("python", root=lone, config_dir=tmp_path / "none") is None
    script = lone.parent.parent / "locate_core.py"
    shutil.copy(PLUGIN / "scripts" / "locate_core.py", script)
    shutil.copytree(lone, tmp_path / "x" / "figma-compose" / "0.1.0" / "scripts", dirs_exist_ok=True)
    (lone / "scripts").mkdir(exist_ok=True)
    shutil.copy(script, lone / "scripts" / "locate_core.py")
    result = subprocess.run([sys.executable, str(lone / "scripts" / "locate_core.py"), "--python", "p"],
                            capture_output=True, text=True, check=False,
                            env={"CLAUDE_CONFIG_DIR": str(tmp_path / "none"), "SYSTEMROOT": r"C:\Windows"}, cwd=tmp_path)
    assert result.returncode == 2
    assert json.loads(result.stdout) == {"status": "blocked", "code": "CORE_NOT_FOUND",
        "message": "figma-core is not installed next to figma-compose"}
