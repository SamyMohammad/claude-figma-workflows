"""Atomic local document writes and content hashes."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

from .errors import CoreError
from .paths import safe_path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise CoreError("FILE_UNREADABLE", f"Cannot hash {path.name}: {error}") from None
    return digest.hexdigest()


def atomic_json(root: Path, relative: str, value: dict) -> None:
    target = safe_path(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False,
                                         dir=target.parent) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True,
                      allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except (OSError, TypeError, ValueError) as error:
        raise CoreError("WRITE_FAILED", f"Atomic JSON write failed: {error}") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
