"""Deterministic synthetic bundle used by offline core tests."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    nodes = []
    for kind, names, size in (("screen", ("home", "review"), 100),
                              ("component", ("button", "card", "badge"), 20)):
        for name in names:
            directory = f"{kind}s/{name}" + ("/default" if kind == "component" else "")
            node_id = f"synthetic:{kind}:{name}"
            nodes.append({"id": node_id, "kind": kind,
                          "variant": "default" if kind == "component" else None,
                          "path": directory, "status": "complete",
                          "sourceRevision": "synthetic-v1", "errorCode": None})
            folder = root / directory
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "context.md").write_text(
                f"Synthetic {kind}: {name}. Not a Figma export.\n", encoding="utf-8")
            image = Image.new("RGB", (size, size), "#ffffff")
            draw = ImageDraw.Draw(image)
            draw.rectangle((2, 2, size - 3, size - 3), fill="#336699")
            image.save(folder / "reference.png", format="PNG")
            _write_json(folder / "meta.json", {
                "schemaVersion": 1, "nodeId": node_id, "sourceRevision": "synthetic-v1",
                "logicalSize": [size, size], "pixelSize": [size, size], "scale": 1,
                "locale": "en-US", "direction": "ltr", "theme": "light",
                "fontHashes": {}, "platform": "synthetic", "renderer": "pillow",
                "textScale": 1, "crop": [0, 0, size, size], "insets": [0, 0, 0, 0],
                "animation": "settled", "colorSpace": "srgb",
            })
    _write_json(root / "tokens.json", {
        "base": {"space": {"small": {"$type": "dimension", "$value": "8px",
                                      "$extensions": {"org.claude-figma-workflows.source":
                                                      {"nodeId": "synthetic:screen:home", "kind": "inferred"}}}}},
        "light": {"color": {"primary": {"$type": "color", "$value": "#336699"}},
                  "space": {"small": {"$type": "dimension", "$value": "{base.space.small}"}},
                  "type": {"body": {"$type": "typography", "$value": {
                      "fontFamily": "Synthetic Sans", "fontSize": "14px", "fontWeight": 400,
                      "lineHeight": 1.4, "letterSpacing": "0px"}}}},
        "dark": {"color": {"primary": {"$type": "color", "$value": "#336699"}},
                 "space": {"small": {"$type": "dimension", "$value": "{base.space.small}"}},
                 "type": {"body": {"$type": "typography", "$value": {
                     "fontFamily": "Synthetic Sans", "fontSize": "14px", "fontWeight": 400,
                     "lineHeight": 1.4, "letterSpacing": "0px"}}}},
    })
    _write_json(root / "fonts.json", {"schemaVersion": 1, "fonts": []})
    _write_json(root / "component-map.json", {"schemaVersion": 1, "components": []})
    _write_json(root / "assets/manifest.json", {"schemaVersion": 1, "assets": []})
    _write_json(root / "comparison-policy.json", {
        "schemaVersion": 1, "channelTolerance": 0, "maxChangedRatio": 0.02,
        "ignored": [], "critical": [],
    })
    (root / "README.md").write_text(
        "# Synthetic core fixture\n\nThese images and IDs are generated locally. "
        "They are not Figma exports. Typography tokens are data only; the images contain no text.\n",
        encoding="utf-8",
    )
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(root.rglob("*")) if p.is_file() and p != root / "manifest.json"}
    _write_json(root / "manifest.json", {
        "schemaVersion": 1, "synthetic": True, "fileKey": "synthetic-core-v1",
        "sourceRevision": "synthetic-v1", "extractedAt": "2026-10-09T00:00:00Z",
        "freshness": "unverified", "scope": [node["id"] for node in nodes],
        "excludedNodes": [], "tokenModes": ["light", "dark"], "capabilities": [],
        "nodes": nodes, "files": files,
        "budget": {"windowId": "synthetic", "limit": 0, "spent": 0, "reserved": 0},
        "status": "complete", "resume": {"nextNode": None, "reason": None},
    })
    return root
