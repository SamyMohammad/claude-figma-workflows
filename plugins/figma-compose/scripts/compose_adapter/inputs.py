"""Validate portable receipts and declarative Kotlin generation settings."""

import json
import re
from copy import deepcopy
from pathlib import Path, PurePosixPath, PureWindowsPath

from jsonschema import Draft202012Validator

from .errors import ComposeError


_SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"
_KEYWORDS = frozenset("as break class continue do else false for fun if in interface is null object package return super this throw true try typealias typeof val var when while".split())


def _validate(kind: str, document: dict) -> None:
    try:
        schema = json.loads((_SCHEMAS / f"{kind}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        json.dumps(document, allow_nan=False)
        if not Draft202012Validator(schema).is_valid(document):
            raise ComposeError("INPUT_INVALID", f"Invalid {kind} document")
    except (ValueError, TypeError, RecursionError):
        raise ComposeError("INPUT_INVALID", f"Invalid {kind} document") from None


def _path(relative: str) -> None:
    parts = relative.split("/")
    if ("\\" in relative or ":" in relative or any(char in '<>"|?*' or ord(char) < 32 for char in relative)
            or PurePosixPath(relative).is_absolute() or PureWindowsPath(relative).drive
            or any(part in ("", ".", "..") or part.endswith((".", " "))
                   or PureWindowsPath(part).is_reserved() for part in parts)):
        raise ComposeError("PATH_INVALID", "Invalid relative project path")


def _symbol(value: str) -> None:
    if any(part in _KEYWORDS for part in value.split(".")):
        raise ComposeError("SYMBOL_INVALID", "Invalid Kotlin identifier")


def _normalize(path: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", path)
    name = parts[0][:1].lower() + parts[0][1:] if parts else "token"
    name += "".join(part[:1].upper() + part[1:] for part in parts[1:])
    if name[0].isdigit() or name in _KEYWORDS:
        name = "token" + name[:1].upper() + name[1:]
    return name


def load_inputs(receipt: dict, config: dict) -> tuple[dict, dict]:
    _validate("receipt", receipt)
    _validate("config", config)
    modes = list(receipt["resolvedByMode"].values())
    paths = set(modes[0])
    if any(set(mode) != paths or any(mode[path]["type"] != modes[0][path]["type"]
                                   for path in paths) for mode in modes[1:]):
        raise ComposeError("TOKEN_MODE", "Semantic token paths/types differ between modes")
    settings = deepcopy(config)
    _symbol(settings["packageName"])
    _path(settings["themeDirectory"])
    names = settings.setdefault("names", {})
    if set(names) - paths:
        raise ComposeError("TOKEN_INVALID", "Name mapping refers to an unavailable token")
    for path in sorted(paths):
        names.setdefault(path, _normalize(path))
        _symbol(names[path])
    for category, expected in (("colors", "color"), ("typography", "typography"), ("shapes", "dimension")):
        for path in settings["material"][category].values():
            if path not in paths or modes[0][path]["type"] != expected:
                raise ComposeError("TOKEN_INVALID", "Material mapping requires a matching semantic token")
    for weights in settings["fonts"].values():
        for font in weights.values():
            _symbol(font["resource"])
            _path(font["projectPath"])
    for inventory in (receipt["fonts"]["fonts"], receipt["assets"]["assets"],
                      receipt["components"]["components"]):
        for entry in inventory:
            if entry["path"] is not None:
                _path(entry["path"])
    ids = set()
    node_paths = set()
    for node in receipt["nodes"]:
        _path(node["path"])
        if node["id"] != node["meta"]["nodeId"] or node["id"] in ids or node["path"] in node_paths:
            raise ComposeError("INPUT_INVALID", "Invalid receipt node identity")
        ids.add(node["id"])
        node_paths.add(node["path"])
    return deepcopy(receipt), settings
