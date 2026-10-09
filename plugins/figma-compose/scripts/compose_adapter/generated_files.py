"""Staged publication with ownership checks and honest rollback."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .core_bridge import run_core
from .errors import ComposeError


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fresh_identity(command, identity):
    fresh = run_core(command, ['export-adapter', '--bundle', str(identity['bundle'])])
    if any(fresh[key] != identity[key] for key in ('tokenHash', 'manifestHash')):
        raise ComposeError('SOURCE_CHANGED', 'Approved source identity changed')
    if 'receiptHash' in identity:
        from .generator import content_hash
        if content_hash(fresh) != identity['receiptHash']:
            raise ComposeError('SOURCE_CHANGED', 'Receipt content differs from fresh core export')
    config_path = identity.get('configPath')
    if config_path:
        from .generator import content_hash
        if content_hash(json.loads(Path(config_path).read_text(encoding='utf-8'))) != identity['configHash']:
            raise ComposeError('CONFIG_CHANGED', 'Source config changed')
    return fresh


def checked_paths(project, paths, command):
    result = run_core(command, ['check-paths', '--root', str(project), '--paths-json', json.dumps(paths)])
    destinations = result.get('paths')
    if not isinstance(destinations, list) or len(destinations) != len(paths):
        raise ComposeError('CORE_OUTPUT', 'Core did not return validated destinations')
    return [Path(path) for path in destinations]


def verify_fonts(project, config, command):
    fonts = [font for weights in config['fonts'].values() for font in weights.values()]
    destinations = checked_paths(project, [font['projectPath'] for font in fonts], command)
    for font, destination in zip(fonts, destinations):
        if not destination.is_file() or file_hash(destination) != font['sha256']:
            raise ComposeError('FONT_CHANGED', 'Configured font file does not match its hash')


def apply_theme(project: Path, files: dict[str, str], core_command: list[str], source_identity: dict) -> dict:
    fresh_identity(core_command, source_identity)
    names = list(files) + ['.workflow/compose-theme.json']
    destinations = checked_paths(project, names, core_command)
    manifest_path = destinations[-1]
    previous = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    previous_files = previous.get('files', {})
    hashes = {name: hashlib.sha256(text.encode('utf-8')).hexdigest() for name, text in files.items()}
    changed, unchanged = [], []
    for name, destination in zip(files, destinations):
        if destination.exists():
            current = file_hash(destination)
            if current != previous_files.get(name):
                raise ComposeError('HAND_EDIT', 'Existing file is not an unchanged generated file: ' + name)
            (unchanged if current == hashes[name] else changed).append(name)
        else:
            changed.append(name)
    manifest = {key: source_identity[key] for key in ('tokenHash', 'manifestHash', 'configHash')}
    manifest.update({'schemaVersion': 1, 'files': hashes, 'generation': source_identity.get('generation', {})})
    contents = dict(files)
    contents['.workflow/compose-theme.json'] = json.dumps(manifest, sort_keys=True, indent=2) + '\n'
    backups = {destination: destination.read_bytes() if destination.exists() else None for destination in destinations}
    replaced = []
    with tempfile.TemporaryDirectory(prefix='compose-stage-') as stage:
        staged = []
        for index, text in enumerate(contents.values()):
            path = Path(stage) / str(index)
            path.write_bytes(text.encode('utf-8'))
            staged.append(path)
        fresh_identity(core_command, source_identity)
        if source_identity.get('config'):
            verify_fonts(project, source_identity['config'], core_command)
        # Revalidate after staging; core checks symlinks and path containment.
        if checked_paths(project, names, core_command) != destinations:
            raise ComposeError('PATH_CHANGED', 'Validated destinations changed')
        if any((destination.read_bytes() if destination.exists() else None) != backup
               for destination, backup in backups.items()):
            raise ComposeError('HAND_EDIT', 'Project changed during staging')
        try:
            for name, destination, staged_path in zip(contents, destinations, staged):
                if name in unchanged:
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged_path, destination)
                replaced.append(destination)
        except OSError:
            failures = []
            for destination in reversed(replaced):
                try:
                    prior = backups[destination]
                    if prior is None:
                        destination.unlink()
                    else:
                        destination.write_bytes(prior)
                except OSError:
                    failures.append(str(destination))
            return {'status': 'partial' if failures else 'error', 'compilationAllowed': False,
                    'rollbackFailed': failures, 'changed': [], 'unchanged': unchanged}
    return {'status': 'passed', 'compilationAllowed': True, 'changed': changed,
            'unchanged': unchanged, **manifest}
