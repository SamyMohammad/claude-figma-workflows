"""Generate reviewable Kotlin only after a fresh trusted core export."""
import argparse
import json
import sys
from pathlib import Path

from compose_adapter.core_bridge import run_core
from compose_adapter.errors import ComposeError
from compose_adapter.generator import content_hash, generation_report, render_theme
from compose_adapter.generated_files import apply_theme, fresh_identity, verify_fonts, checked_paths


def main(argv=None):
    parser = argparse.ArgumentParser(prog='figma-compose')
    sub = parser.add_subparsers(dest='command', required=True)
    generate = sub.add_parser('generate')
    for name in ('bundle', 'receipt', 'config', 'project', 'core-command-json'):
        generate.add_argument('--' + name, required=True)
    generate.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        command = json.loads(args.core_command_json)
        receipt = json.loads(Path(args.receipt).read_text(encoding='utf-8'))
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        identity = {key: receipt[key] for key in ('tokenHash', 'manifestHash')}
        identity.update({'bundle': args.bundle, 'receiptHash': content_hash(receipt),
            'configHash': content_hash(config), 'configPath': args.config, 'config': config})
        fresh_identity(command, identity)
        files = render_theme(receipt, config)
        files = {config['themeDirectory'] + '/' + name: text for name, text in files.items()}
        identity['generation'] = generation_report(receipt, config)
        verify_fonts(Path(args.project), config, command)
        checked_paths(Path(args.project), list(files) + ['.workflow/compose-theme.json'], command)
        fresh_identity(command, identity)
        result = ({'status': 'passed', 'dryRun': True, 'files': files, **identity['generation']}
                  if args.dry_run else apply_theme(Path(args.project), files, command, identity))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result['status'] == 'passed' else 2
    except (ComposeError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'blocked', 'code': getattr(error, 'code', 'INPUT_INVALID'), 'message': str(error)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
