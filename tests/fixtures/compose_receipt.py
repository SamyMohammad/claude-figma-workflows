"""Explicitly synthetic approved receipt for pure unit tests."""

def make_receipt():
    from tempfile import TemporaryDirectory
    from pathlib import Path
    from fixtures.make_core_fixture import make_fixture
    from figma_core.documents import read_json
    from figma_core.storage import atomic_json, file_hash
    from figma_core.approvals import content_hash
    from figma_core.adapter_export import export_adapter
    with TemporaryDirectory() as directory:
        root = make_fixture(Path(directory) / "bundle")
        tokens = read_json(root / "tokens.json")
        for mode in ("light", "dark"):
            group = tokens[mode]
            group["type"]["body"]["$value"]["fontFamily"] = "Roboto"
            group["color"]["onPrimary"] = {"$type": "color", "$value": {
                "colorSpace": "srgb", "components": [1, 1, 1], "alpha": 1}}
            group["color"]["background"] = {"$type": "color", "$value": {
                "colorSpace": "srgb", "components": [1, 1, 1] if mode == "light" else [0, 0, 0], "alpha": 1}}
            group["shape"] = {"radius": {"$type": "dimension", "$value": {"value": 16, "unit": "px"}}}
            group["frame"] = {"size": {"$type": "dimension", "$value": {"value": 160, "unit": "px"}}}
            group["motion"] = {
                "duration": {"$type": "duration", "$value": {"value": 200, "unit": "ms"}},
                "easing": {"$type": "cubicBezier", "$value": [0.2, 0, 0, 1]}}
        atomic_json(root, "tokens.json", tokens)
        approval = {"schemaVersion": 1, "kind": "tokens", "contentHash": content_hash(tokens),
                    "owner": "synthetic-test", "evidence": "fixture-only", "approvedAt": "2026-10-09T00:00:00Z",
                    "modes": ["light", "dark"], "deviations": []}
        atomic_json(root, "tokens-approval.json", approval)
        manifest = read_json(root / "manifest.json")
        for path in ("tokens.json", "tokens-approval.json"):
            manifest["files"][path] = file_hash(root / path)
        atomic_json(root, "manifest.json", manifest)
        return export_adapter(root)
