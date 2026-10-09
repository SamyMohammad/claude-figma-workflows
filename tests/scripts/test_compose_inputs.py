from copy import deepcopy
import subprocess

import pytest


def config():
    return {"schemaVersion": 1, "packageName": "com.example.theme", "themeDirectory": "app/theme",
            "remBasePx": None, "names": {}, "material": {"colors": {"primary": "color.primary"},
            "typography": {"bodyLarge": "type.body"}, "shapes": {"medium": "shape.radius"}},
            "fonts": {}, "allowedMaterialDefaults": []}


def test_load_complete_synthetic_receipt():
    from compose_adapter.inputs import load_inputs
    from fixtures.compose_receipt import make_receipt
    receipt = make_receipt()
    actual, settings = load_inputs(receipt, config())
    assert actual == receipt
    assert settings["names"]["space.small"] == "spaceSmall"
    assert set(actual["resolvedByMode"]) == {"light", "dark"}


@pytest.mark.parametrize("field,value", [("packageName", "com.x;exec()"),
    ("themeDirectory", "../escape"), ("schemaVersion", 2), ("unknown", True),
    ("names", {"space.small": "x()"}), ("fonts", {"Roboto": {"400": {
    "resource": "R.font.x()", "projectPath": "res/font/x.ttf", "sha256": "a" * 64}}}),
    ("material", {"colors": {"fakeRole": "color.primary"}, "typography": {}, "shapes": {}})])
def test_invalid_config_rejected(field, value):
    from compose_adapter.inputs import load_inputs
    from compose_adapter.errors import ComposeError
    from fixtures.compose_receipt import make_receipt
    settings = config()
    settings[field] = value
    with pytest.raises(ComposeError):
        load_inputs(make_receipt(), settings)


@pytest.mark.parametrize("change", ["version", "mode", "type", "missing", "status"])
def test_invalid_receipt_rejected(change):
    from compose_adapter.inputs import load_inputs
    from compose_adapter.errors import ComposeError
    from fixtures.compose_receipt import make_receipt
    receipt = make_receipt()
    if change == "version": receipt["schemaVersion"] = 2
    if change == "mode": receipt["resolvedByMode"]["future"] = {}
    if change == "type": receipt["resolvedByMode"]["dark"]["space.small"]["type"] = "color"
    if change == "missing": del receipt["resolvedByMode"]["dark"]["space.small"]
    if change == "status": receipt["status"] = "blocked"
    with pytest.raises(ComposeError):
        load_inputs(receipt, config())


def test_names_may_be_missing_and_inputs_are_not_mutated():
    from compose_adapter.inputs import load_inputs
    from fixtures.compose_receipt import make_receipt
    settings = config()
    del settings["names"]
    original = deepcopy(settings)
    _, loaded = load_inputs(make_receipt(), settings)
    assert settings == original
    assert loaded["names"]["type.body"] == "typeBody"


@pytest.mark.parametrize("output,code", [('{}', 0), ('not json', 0),
    ('{"status":"blocked"}', 0), ('{"status":"passed"}', 2),
    ('{"status":"passed","status":"blocked"}', 0)])
def test_bridge_rejects_malformed_or_unsuccessful_results(monkeypatch, output, code):
    from compose_adapter.core_bridge import run_core
    from compose_adapter.errors import ComposeError
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], code, output, ""))
    with pytest.raises(ComposeError):
        run_core(["python", "trusted-core.py"], ["export-adapter", "--bundle", "untrusted name"])


def test_bridge_uses_argument_arrays_without_shell(monkeypatch):
    from compose_adapter.core_bridge import run_core
    def run(command, **options):
        assert command == ["python", "trusted-core.py", "--bundle", "x; y"]
        assert options["shell"] is False
        return subprocess.CompletedProcess(command, 0, '{"status":"passed"}', "")
    monkeypatch.setattr(subprocess, "run", run)
    assert run_core(["python", "trusted-core.py"], ["--bundle", "x; y"])["status"] == "passed"


def test_bridge_preserves_safe_core_error_code(monkeypatch):
    from compose_adapter.core_bridge import run_core
    from compose_adapter.errors import ComposeError
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a[0], 2, "", "APPROVAL_INVALID: untrusted secret"))
    with pytest.raises(ComposeError) as error:
        run_core(["python"], [])
    assert error.value.code == "APPROVAL_INVALID"
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("field,value", [("packageName", "com.when.theme"),
    ("themeDirectory", "theme./out"), ("remBasePx", float("nan")),
    ("allowedMaterialDefaults", ["unknown"]), ("material", {"colors": {"primary": "space.small"}, "typography": {}, "shapes": {}})])
def test_semantic_and_portable_config_checks(field, value):
    from compose_adapter.inputs import load_inputs
    from compose_adapter.errors import ComposeError
    from fixtures.compose_receipt import make_receipt
    settings = config()
    settings[field] = value
    with pytest.raises(ComposeError):
        load_inputs(make_receipt(), settings)


def test_single_selected_mode_is_preserved():
    from compose_adapter.inputs import load_inputs
    from fixtures.compose_receipt import make_receipt
    receipt = make_receipt()
    del receipt["resolvedByMode"]["dark"]
    actual, _ = load_inputs(receipt, config())
    assert list(actual["resolvedByMode"]) == ["light"]


@pytest.mark.parametrize("command,args", [("python core.py", []), ([], []), (["python"], "--bundle"), (["python"], [None])])
def test_bridge_requires_explicit_arrays(command, args):
    from compose_adapter.core_bridge import run_core
    from compose_adapter.errors import ComposeError
    with pytest.raises(ComposeError):
        run_core(command, args)


def test_bridge_preserves_blocked_json_code(monkeypatch):
    from compose_adapter.core_bridge import run_core
    from compose_adapter.errors import ComposeError
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 2, '{"status":"blocked","code":"APPROVAL_INVALID"}', ""))
    with pytest.raises(ComposeError) as error:
        run_core(["python"], [])
    assert error.value.code == "APPROVAL_INVALID"
