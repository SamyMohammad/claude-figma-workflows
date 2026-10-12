"""Print the --core-command-json value for the installed figma-core dependency.

Usage: locate_core.py --python <venv python>
Resolution order: sibling plugin cache directory (<cache>/<marketplace>/figma-core/<version>),
then installPath in installed_plugins.json under CLAUDE_CONFIG_DIR (default ~/.claude).
Standard library only; exit code 2 with a JSON blocked report when core is not found.
"""
import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _version_key(path):
    return tuple(int(part) if part.isdigit() else 0 for part in path.name.split('.'))


def sibling_core(root):
    base = root.parent.parent / 'figma-core'
    versions = sorted((p for p in base.glob('*') if (p / 'scripts' / 'core.py').is_file()),
                      key=_version_key) if base.is_dir() else []
    return versions[-1] if versions else None


def registered_core(config_dir):
    registry = Path(config_dir) / 'plugins' / 'installed_plugins.json'
    try:
        plugins = json.loads(registry.read_text(encoding='utf-8')).get('plugins', {})
    except (OSError, ValueError, AttributeError):
        return None
    for key, entries in plugins.items():
        if key.split('@')[0] != 'figma-core' or not isinstance(entries, list):
            continue
        for entry in entries:
            path = Path(entry.get('installPath', '')) if isinstance(entry, dict) else None
            if path and (path / 'scripts' / 'core.py').is_file():
                return path
    return None


def locate(python, root=PLUGIN_ROOT, config_dir=None):
    config_dir = config_dir or os.environ.get('CLAUDE_CONFIG_DIR') or str(Path.home() / '.claude')
    core = sibling_core(Path(root)) or registered_core(config_dir)
    if core is None:
        return None
    return [str(python), str(core / 'scripts' / 'core.py')]


def main(argv=None):
    parser = argparse.ArgumentParser(prog='locate-core')
    parser.add_argument('--python', required=True)
    args = parser.parse_args(argv)
    command = locate(args.python)
    if command is None:
        print(json.dumps({'status': 'blocked', 'code': 'CORE_NOT_FOUND',
                          'message': 'figma-core is not installed next to figma-compose'}))
        return 2
    print(json.dumps(command))
    return 0


if __name__ == '__main__':
    sys.exit(main())
