"""Measured Android evidence; core remains the comparison authority."""
import hashlib
import json
import math
from pathlib import Path

from jsonschema import Draft202012Validator
from PIL import Image

from .errors import ComposeError
from .generated_files import checked_paths, file_hash, fresh_identity, verify_fonts
from .generator import content_hash, render_theme

SCHEMA = Path(__file__).resolve().parents[2] / 'schemas/capture-receipt.schema.json'


def prepare_capture(reference_meta: dict, measured: dict, image: Path) -> dict:
    def finite(value):
        if isinstance(value, dict):
            return all(finite(item) for item in value.values())
        if isinstance(value, list):
            return all(finite(item) for item in value)
        return not isinstance(value, float) or math.isfinite(value)
    if not finite(measured):
        raise ComposeError('CAPTURE_INVALID', 'Measured numbers must be finite')
    errors = list(Draft202012Validator(json.loads(SCHEMA.read_text())).iter_errors(measured))
    if errors:
        raise ComposeError('CAPTURE_INVALID', errors[0].message)
    if file_hash(image) != measured['imageHash']:
        raise ComposeError('CAPTURE_CHANGED', 'Candidate bytes differ from measured receipt')
    with Image.open(image) as png:
        if png.format != 'PNG' or list(png.size) != measured['pixelSize']:
            raise ComposeError('CAPTURE_MISMATCH', 'Observed PNG dimensions differ')
    bounds = measured['targetBounds']
    size = [bounds[2] - bounds[0], bounds[3] - bounds[1]]
    if size != measured['pixelSize']:
        raise ComposeError('CAPTURE_MISMATCH', 'Target bounds differ from cropped PNG')
    if any(abs(dp * measured['density'] - px) > 1e-6
           for dp, px in zip(measured['logicalSize'], size)):
        raise ComposeError('CAPTURE_MISMATCH', 'Observed density differs from target bounds')
    actual = {key: measured[key] for key in (
        'schemaVersion', 'nodeId', 'sourceRevision', 'logicalSize', 'pixelSize', 'locale',
        'direction', 'theme', 'containsText', 'platform', 'renderer', 'crop', 'insets',
        'animation', 'colorSpace')}
    actual.update(scale=measured['density'], textScale=measured['fontScale'],
                  fontHashes=measured['usedFontHashes'])
    for key, value in actual.items():
        if key not in ('platform', 'renderer') and reference_meta.get(key) != value:
            raise ComposeError('CAPTURE_MISMATCH', 'Observed capture differs: ' + key)
    if actual['containsText'] and not actual['fontHashes']:
        raise ComposeError('FONT_UNAVAILABLE', 'Text content lacks rendered font registry')
    return actual


def verify_rendered_theme(project: Path, bundle: Path, config_path: Path,
                          measured: dict, command: list[str]) -> dict:
    config = json.loads(config_path.read_text(encoding='utf-8'))
    manifest_path = checked_paths(project, ['.workflow/compose-theme.json'], command)[0]
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    identity = {**manifest, 'bundle': str(bundle), 'configPath': str(config_path)}
    fresh = fresh_identity(command, identity)
    if manifest['configHash'] != content_hash(config):
        raise ComposeError('CONFIG_CHANGED', 'Current configuration differs from generated theme')
    if measured['themeIdentity'] != {key: manifest[key] for key in ('tokenHash', 'manifestHash', 'configHash')}:
        raise ComposeError('STALE_THEME', 'Rendered compiled identity differs from current theme')
    expected = {config['themeDirectory'] + '/' + name: text for name, text in render_theme(fresh, config).items()}
    hashes = {name: hashlib.sha256(text.encode()).hexdigest() for name, text in expected.items()}
    if manifest['files'] != hashes:
        raise ComposeError('STALE_THEME', 'Manifest differs from fresh generator output')
    destinations = checked_paths(project, list(hashes), command)
    if any(file_hash(path) != hashes[name] for name, path in zip(hashes, destinations)):
        raise ComposeError('HAND_EDIT', 'Generator-owned files changed after generation')
    verify_fonts(project, config, command)
    return fresh
