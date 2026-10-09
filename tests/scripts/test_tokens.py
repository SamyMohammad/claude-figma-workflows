from copy import deepcopy

import pytest

from figma_core.errors import CoreError
from figma_core.tokens import audit_tokens, resolve_tokens
from figma_core.documents import read_json
from fixtures.make_core_fixture import make_fixture


def test_alias_cycle_reports_blocked():
    tokens = {"light": {"a": {"$type": "number", "$value": "{light.b}"},
                        "b": {"$type": "number", "$value": "{light.a}"}}}
    with pytest.raises(CoreError, match="cycle"):
        resolve_tokens(tokens, "light")


def test_audit_does_not_round_source_spacing():
    tokens = {"light": {"space": {"$type": "dimension", "$value": {"value": 13.3, "unit": "px"}}}}
    before = deepcopy(tokens)
    audit_tokens(tokens)
    assert tokens == before
    assert resolve_tokens(tokens, "light")["space"]["value"]["value"] == 13.3


def test_missing_alias_is_rejected():
    with pytest.raises(CoreError, match="alias"):
        resolve_tokens({"light": {"x": {"$type": "number", "$value": "{base.nope}"}}}, "light")


def test_cross_mode_type_mismatch_blocks_audit():
    tokens = {"light": {"x": {"$type": "number", "$value": 1}},
              "dark": {"x": {"$type": "dimension", "$value": "1px"}}}
    assert audit_tokens(tokens)["status"] == "blocked"


@pytest.mark.parametrize("value", [
    {"colorSpace": "srgb", "components": [0, 0, 0], "alpha": 1.1},
    {"colorSpace": "display-p3", "components": [0, 0, 0], "alpha": 1},
])
def test_invalid_color_is_rejected(value):
    with pytest.raises(CoreError, match="color"):
        resolve_tokens({"light": {"x": {"$type": "color", "$value": value}}}, "light")


def test_typography_composite_alias_resolves():
    tokens = {"base": {"size": {"$type": "dimension", "$value": {"value": 1, "unit": "rem"}}},
              "light": {"body": {"$type": "typography", "$value": {
                  "fontFamily": "Example", "fontSize": "{base.size}",
                  "fontWeight": 400, "letterSpacing": {"value": 0, "unit": "px"},
                  "lineHeight": 1.4}}}}
    assert resolve_tokens(tokens, "light")["body"]["value"]["fontSize"] == {"value": 1, "unit": "rem"}


def test_typography_line_height_requires_number_alias():
    tokens = {"base": {"leading": {"$type": "number", "$value": 1.4}},
              "light": {"body": {"$type": "typography", "$value": {
                  "fontFamily": "Example", "fontSize": {"value": 14, "unit": "px"},
                  "fontWeight": 400, "letterSpacing": {"value": 0, "unit": "px"},
                  "lineHeight": "{base.leading}"}}}}
    assert resolve_tokens(tokens, "light")["body"]["value"]["lineHeight"] == 1.4
    tokens["base"]["leading"] = {"$type": "dimension", "$value": {"value": 20, "unit": "px"}}
    with pytest.raises(CoreError, match="Incompatible alias"):
        resolve_tokens(tokens, "light")


def test_duplicate_values_are_proposals_only():
    tokens = {"light": {"a": {"$type": "number", "$value": 1},
                        "b": {"$type": "number", "$value": 1}}}
    before = deepcopy(tokens)
    result = audit_tokens(tokens)
    assert result["status"] == "passed"
    assert result["proposals"]
    assert tokens == before


def test_fixture_selected_modes_resolve_and_audit(tmp_path):
    root = make_fixture(tmp_path / "bundle")
    tokens = read_json(root / "tokens.json")
    manifest = read_json(root / "manifest.json")
    assert audit_tokens(tokens)["status"] == "passed"
    for mode in manifest["tokenModes"]:
        resolved = resolve_tokens(tokens, mode)
        assert resolved["color.primary"]["value"]["colorSpace"] == "srgb"
        assert resolved["space.small"]["value"] == {"value": 8, "unit": "px"}


@pytest.mark.parametrize("token", [
    {"$type": "number", "$value": float("inf")},
    {"$type": "dimension", "$value": {"value": 1, "unit": "pt"}},
    {"$type": "dimension", "$value": "8px"},
    {"$type": "duration", "$value": "100ms"},
    {"$type": "fontWeight", "$value": "Bold"},
    {"$type": "cubicBezier", "$value": [1.2, 0, 0, 1]},
    {"$type": "unknown", "$value": 1},
    {"$type": "number", "$value": 1, "child": {}},
    {"$ref": "base.x"},
    {"$extends": "base"},
])
def test_invalid_token_is_typed_error(token):
    with pytest.raises(CoreError):
        resolve_tokens({"light": {"x": token}}, "light")


def test_inherited_type_and_incompatible_alias():
    tokens = {"base": {"x": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}}},
              "light": {"$type": "number", "x": {"$value": "{base.x}"}}}
    with pytest.raises(CoreError, match="Incompatible alias"):
        resolve_tokens(tokens, "light")


def test_invalid_unused_base_blocks_audit():
    tokens = {"base": {"x": {"$type": "number", "$value": float("nan")}},
              "light": {"x": {"$type": "number", "$value": 1}}}
    assert audit_tokens(tokens)["status"] == "blocked"
