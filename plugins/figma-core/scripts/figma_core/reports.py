"""Immutable comparison evidence reports."""

import html
import json
import re
from pathlib import Path

from .errors import CoreError


def evidence_payload(reference_hash: str, actual_hash: str, meta_hash: str, policy_hash: str) -> dict:
    return {"referenceHash": reference_hash, "actualHash": actual_hash,
            "metaHash": meta_hash, "policyHash": policy_hash}


def _escape(value: object) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", html.escape(str(value)))


def write_report(run: Path, report: dict, reference=None, actual=None, diff=None, overlay=None) -> None:
    """Create a new run directory and write available evidence once."""
    try:
        run.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        raise CoreError("REPORT_EXISTS", "Run directory already exists or is unavailable") from error
    for name, image in (("reference.png", reference), ("actual.png", actual),
                        ("diff.png", diff), ("overlay.png", overlay)):
        if image is not None:
            image.save(run / name, format="PNG")
    (run / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2,
                                               ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    lines = ["# Visual comparison", "", f"Status: {_escape(report['status'])}"]
    if report.get("code"):
        lines.append(f"Code: {_escape(report['code'])}")
    if report.get("reason"):
        lines.append(f"Reason: {_escape(report['reason'])}")
    if "changedRatio" in report:
        lines.append(f"Changed ratio: {_escape(report['changedRatio'])}")
    (run / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
