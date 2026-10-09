"""Absolute-path executable entry point for installed plugins."""

import sys

try:
    from figma_core.cli import main
except ImportError:
    print("DEPENDENCY_MISSING: Install requirements.lock in the selected Python venv", file=sys.stderr)
    raise SystemExit(2) from None

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
