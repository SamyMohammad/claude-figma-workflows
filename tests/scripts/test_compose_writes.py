import hashlib
import json
import os

import pytest

from compose_adapter.generated_files import apply_theme, verify_fonts
from compose_adapter.generator import content_hash


@pytest.fixture
def publication(tmp_path, monkeypatch):
    from compose_adapter import generated_files
    identity = {'bundle': 'bundle', 'tokenHash': 'a' * 64, 'manifestHash': 'b' * 64, 'configHash': 'c' * 64}
    def core(command, args):
        if args[0] == 'export-adapter':
            return {'status': 'passed', 'tokenHash': identity['tokenHash'], 'manifestHash': identity['manifestHash']}
        paths = json.loads(args[-1])
        return {'status': 'passed', 'paths': [str(tmp_path / path) for path in paths]}
    monkeypatch.setattr(generated_files, 'run_core', core)
    return tmp_path, identity


def test_idempotence_and_hand_edit_protection(publication):
    root, identity = publication
    files = {'theme/AppTokens.kt': 'hello'}
    assert apply_theme(root, files, ['trusted'], identity)['changed'] == list(files)
    assert apply_theme(root, files, ['trusted'], identity)['unchanged'] == list(files)
    (root / 'theme/AppTokens.kt').write_text('manual')
    with pytest.raises(ValueError, match='Existing file'):
        apply_theme(root, files, ['trusted'], identity)
    assert (root / 'theme/AppTokens.kt').read_text() == 'manual'


def test_handwritten_file_never_overwritten(publication):
    root, identity = publication
    (root / 'AppTheme.kt').write_text('handwritten')
    with pytest.raises(ValueError):
        apply_theme(root, {'AppTheme.kt': 'generated'}, ['trusted'], identity)


def test_source_changes_during_staging_block(publication, monkeypatch):
    from compose_adapter import generated_files
    root, identity = publication
    original = generated_files.run_core
    exports = 0
    def core(command, args):
        nonlocal exports
        result = original(command, args)
        if args[0] == 'export-adapter':
            exports += 1
            if exports == 2:
                result['manifestHash'] = 'd' * 64
        return result
    monkeypatch.setattr(generated_files, 'run_core', core)
    with pytest.raises(ValueError, match='identity changed'):
        apply_theme(root, {'AppTheme.kt': 'generated'}, ['trusted'], identity)
    assert not (root / 'AppTheme.kt').exists()


def test_config_changes_block(publication):
    root, identity = publication
    path = root / 'config.json'
    path.write_text('{}')
    identity.update({'configPath': str(path), 'configHash': content_hash({'changed': True})})
    with pytest.raises(ValueError, match='config changed'):
        apply_theme(root, {'AppTheme.kt': 'generated'}, ['trusted'], identity)


def test_actual_font_hash_checked(publication):
    root, _ = publication
    path = root / 'font.ttf'
    path.write_bytes(b'actual fixture font bytes')
    font = {'projectPath': 'font.ttf', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    config = {'fonts': {'Roboto': {'400': font}}}
    verify_fonts(root, config, ['trusted'])
    path.write_bytes(b'changed')
    with pytest.raises(ValueError, match='font file'):
        verify_fonts(root, config, ['trusted'])


def test_failed_replacement_rolls_back_and_blocks_compilation(publication, monkeypatch):
    root, identity = publication
    files = {'A.kt': 'a', 'B.kt': 'b'}
    apply_theme(root, files, ['trusted'], identity)
    original = os.replace
    calls = 0
    def replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('injected')
        return original(source, destination)
    monkeypatch.setattr(os, 'replace', replace)
    result = apply_theme(root, {'A.kt': 'new a', 'B.kt': 'new b'}, ['trusted'], identity)
    assert result['status'] == 'error'
    assert result['compilationAllowed'] is False
    assert (root / 'A.kt').read_text() == 'a'
    assert (root / 'B.kt').read_text() == 'b'


def test_partial_rollback_is_honest(publication, monkeypatch):
    from pathlib import Path
    root, identity = publication
    apply_theme(root, {'A.kt': 'a', 'B.kt': 'b'}, ['trusted'], identity)
    original_replace = os.replace
    original_write = Path.write_bytes
    calls = 0
    def replace(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('replacement failed')
        return original_replace(source, destination)
    def write(path, data):
        if path == root / 'A.kt':
            raise OSError('rollback failed')
        return original_write(path, data)
    monkeypatch.setattr(os, 'replace', replace)
    monkeypatch.setattr(Path, 'write_bytes', write)
    result = apply_theme(root, {'A.kt': 'new', 'B.kt': 'new'}, ['trusted'], identity)
    assert result['status'] == 'partial'
    assert result['rollbackFailed'] == [str(root / 'A.kt')]
    assert result['compilationAllowed'] is False


def test_receipt_tampering_blocks(publication):
    root, identity = publication
    identity['receiptHash'] = 'e' * 64
    with pytest.raises(ValueError, match='Receipt content'):
        apply_theme(root, {'A.kt': 'a'}, ['trusted'], identity)


def test_real_core_rejects_changed_bundle(tmp_path):
    import sys
    from pathlib import Path
    from fixtures.make_core_fixture import make_fixture
    from figma_core.documents import read_json
    from figma_core.storage import atomic_json, file_hash
    from figma_core.approvals import content_hash
    from figma_core.adapter_export import export_adapter
    root = make_fixture(tmp_path / 'bundle')
    tokens = read_json(root / 'tokens.json')
    atomic_json(root, 'tokens-approval.json', {'schemaVersion': 1, 'kind': 'tokens',
        'contentHash': content_hash(tokens), 'owner': 'synthetic-test', 'evidence': 'fixture',
        'approvedAt': '2026-10-09T00:00:00Z', 'modes': ['light', 'dark'], 'deviations': []})
    manifest = read_json(root / 'manifest.json')
    manifest['files']['tokens-approval.json'] = file_hash(root / 'tokens-approval.json')
    atomic_json(root, 'manifest.json', manifest)
    receipt = export_adapter(root)
    identity = {'bundle': str(root), 'tokenHash': receipt['tokenHash'],
                'manifestHash': receipt['manifestHash'], 'configHash': 'c' * 64}
    tokens['light']['space']['small']['$value'] = {'value': 23, 'unit': 'px'}
    atomic_json(root, 'tokens.json', tokens)
    command = [sys.executable, str(Path(__file__).parents[2] / 'plugins/figma-core/scripts/core.py')]
    project = tmp_path / 'project'
    project.mkdir()
    with pytest.raises(ValueError):
        apply_theme(project, {'A.kt': 'a'}, command, identity)
    assert not (project / 'A.kt').exists()


def test_stage_uses_each_validated_destination_filesystem(publication, monkeypatch):
    import errno
    from pathlib import Path
    root, identity = publication
    original = os.replace
    def replace(source, destination):
        # Model each destination parent as its own volume/mount boundary.
        if not Path(source).is_relative_to(Path(destination).parent):
            raise OSError(errno.EXDEV, 'Invalid cross-device link')
        return original(source, destination)
    monkeypatch.setattr(os, 'replace', replace)
    result = apply_theme(root, {'theme/AppTheme.kt': 'theme', 'other/AppTokens.kt': 'tokens'}, ['trusted'], identity)
    assert result['status'] == 'passed'
    assert (root / 'theme/AppTheme.kt').read_text() == 'theme'
    assert (root / 'other/AppTokens.kt').read_text() == 'tokens'


def test_config_mutation_during_staging_blocks_publication(publication, monkeypatch):
    from pathlib import Path
    root, identity = publication
    config_path = root / 'config.json'
    config_path.write_text('{}')
    identity.update({'configPath': str(config_path), 'configHash': content_hash({})})
    original = Path.write_bytes
    def write(path, data):
        result = original(path, data)
        if path.parent.name.startswith('.compose-stage-'):
            config_path.write_text('{"changed":true}')
        return result
    monkeypatch.setattr(Path, 'write_bytes', write)
    with pytest.raises(ValueError, match='config changed'):
        apply_theme(root, {'theme/AppTheme.kt': 'generated'}, ['trusted'], identity)
    assert not (root / 'theme/AppTheme.kt').exists()
    assert not list(root.rglob('.compose-stage-*'))
