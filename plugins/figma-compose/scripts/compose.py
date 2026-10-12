"""Generate reviewable Kotlin only after a fresh trusted core export."""
import argparse
import json
import sys
from pathlib import Path

from compose_adapter.core_bridge import run_core
from compose_adapter.errors import ComposeError
from compose_adapter.generator import content_hash, generation_report, render_theme
from compose_adapter.generated_files import apply_theme, fresh_identity, verify_fonts, checked_paths
from compose_adapter.capture_metadata import prepare_capture, verify_rendered_theme


def main(argv=None):
    parser = argparse.ArgumentParser(prog='figma-compose')
    sub = parser.add_subparsers(dest='command', required=True)
    generate = sub.add_parser('generate')
    for name in ('bundle', 'receipt', 'config', 'project', 'core-command-json'):
        generate.add_argument('--' + name, required=True)
    generate.add_argument('--dry-run', action='store_true')
    capture = sub.add_parser('prepare-capture')
    for name in ('bundle', 'config', 'project', 'core-command-json', 'reference-meta', 'measured', 'image', 'output'):
        capture.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    try:
        command = json.loads(args.core_command_json)
        if args.command == 'prepare-capture':
            measured = json.loads(Path(args.measured).read_text(encoding='utf-8'))
            reference = json.loads(Path(args.reference_meta).read_text(encoding='utf-8'))
            actual = prepare_capture(reference, measured, Path(args.image))
            verify_rendered_theme(Path(args.project), Path(args.bundle), Path(args.config), measured, command)
            output = Path(args.output)
            root = Path(args.project).resolve()
            relative = output.resolve().relative_to(root).as_posix()
            if not relative.startswith('app/build/figma-candidates/'):
                raise ComposeError('OUTPUT_INVALID', 'Capture metadata belongs in candidate build artifacts')
            (output,) = checked_paths(root, [relative], command)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(actual, sort_keys=True, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'status': 'passed', 'actualMeta': str(output), 'imageHash': measured['imageHash'],
                'freshness': 'unverified', 'visualReview': 'not_run'}))
            return 0
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
