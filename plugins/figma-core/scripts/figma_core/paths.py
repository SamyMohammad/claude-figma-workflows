"""Portable paths within a local design bundle."""

from pathlib import Path, PurePosixPath, PureWindowsPath

from .errors import CoreError


def safe_path(root: Path, relative: str) -> Path:
    """Return a contained path, rejecting ambiguous and linked components."""
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise CoreError("PATH_INVALID", "Invalid relative bundle path")
    posix = PurePosixPath(relative)
    windows = PureWindowsPath(relative)
    parts = relative.split("/")
    if (posix.is_absolute() or windows.is_absolute() or windows.drive
            or any(part in ("", ".", "..") or part.endswith((".", " "))
                   or PureWindowsPath(part).is_reserved() for part in parts)):
        raise CoreError("PATH_INVALID", "Invalid relative bundle path")
    base = root.resolve()
    candidate = base.joinpath(*parts)
    current = base
    for part in parts:
        current = current / part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise CoreError("PATH_INVALID", "Bundle path leaves its root or crosses a link")
    if not candidate.resolve().is_relative_to(base):
        raise CoreError("PATH_INVALID", "Bundle path leaves its root")
    return candidate


def check_collisions(paths: list[str]) -> None:
    folded = set()
    for name in paths:
        key = name.casefold()
        if key in folded:
            raise CoreError("PATH_INVALID", "Case-folded bundle path collision")
        folded.add(key)
