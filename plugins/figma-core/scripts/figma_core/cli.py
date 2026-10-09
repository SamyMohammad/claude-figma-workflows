"""Safe local command interface for bundle workflows."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .budget import mark_sent, reserve
from .checkpoint import complete_node
from .cli_bundle import audit, validate
from .cli_compare import compare, correction
from .errors import CoreError


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CoreError("CLI_ARGUMENT", message)


def _parser():
    parser = _Parser(prog="figma-core")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_Parser)
    for command in ("validate", "audit", "complete-node", "correction", "compare"):
        part = commands.add_parser(command)
        part.add_argument("--bundle", type=Path, required=True)
        if command in ("complete-node", "correction"):
            part.add_argument("--node-id", required=True)
        if command == "audit":
            part.add_argument("--mode", choices=("light", "dark"), required=True)
        if command == "correction":
            part.add_argument("--policy", type=Path, required=True)
            part.add_argument("--policy-approval", type=Path, required=True)
        if command == "compare":
            for name in ("reference", "actual", "reference-meta", "actual-meta", "policy",
                         "policy-approval", "output"):
                part.add_argument(f"--{name}", type=Path, required=True)
    part = commands.add_parser("reserve")
    part.add_argument("--ledger", type=Path, required=True)
    part.add_argument("--window", required=True)
    part.add_argument("--limit", type=int, required=True)
    part.add_argument("--request-id", required=True)
    part = commands.add_parser("mark-sent")
    part.add_argument("--ledger", type=Path, required=True)
    part.add_argument("--request-id", required=True)
    return parser


def main(argv: list[str]) -> int:
    try:
        args = _parser().parse_args(argv)
        match args.command:
            case "validate":
                result = validate(args.bundle)
            case "audit":
                result = audit(args.bundle, args.mode)
            case "compare":
                result = compare(args)
            case "reserve":
                accepted = reserve(args.ledger, args.window, args.limit, args.request_id)
                result = {"status": "passed" if accepted else "blocked", "reserved": accepted}
            case "mark-sent":
                mark_sent(args.ledger, args.request_id)
                result = {"status": "passed"}
            case "complete-node":
                manifest = complete_node(args.bundle, args.node_id)
                result = {"status": "passed" if manifest["status"] == "complete" else "blocked",
                          "bundleStatus": manifest["status"]}
            case "correction":
                result = correction(args.bundle, args.node_id, args.policy, args.policy_approval)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return {"passed": 0, "failed": 1, "blocked": 2, "not_run": 2}[result["status"]]
    except CoreError as error:
        print(f"{error.code}: {error}", file=sys.stderr)
        return 2
    except (OSError, sqlite3.Error, ImportError) as error:
        code = "DEPENDENCY_MISSING" if isinstance(error, ImportError) else "IO_ERROR"
        print(f"{code}: Local operation unavailable; install requirements-core.lock from this plugin in the selected venv", file=sys.stderr)
        return 2
