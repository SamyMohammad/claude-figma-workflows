import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image
from compose_adapter.capture_metadata import prepare_capture
from compose_adapter.errors import ComposeError

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def capture(tmp_path):
    meta = json.loads((ROOT / 'tests/fixtures/compose-v1/screens/home/meta.json').read_text())
    image = tmp_path / 'candidate.png'
    Image.new('RGB', (160, 160), 'white').save(image)
    facts = {'schemaVersion': 1, 'nodeId': meta['nodeId'], 'sourceRevision': 'synthetic-v1',
             'pixelSize': [160, 160], 'logicalSize': [160, 160], 'density': 1,
             'fontScale': 1, 'locale': 'en-US', 'direction': 'ltr', 'theme': 'light',
             'crop': [0, 0, 160, 160], 'insets': [0, 0, 0, 0], 'usedFontHashes': {},
             'containsText': False, 'animation': 'settled', 'colorSpace': 'srgb',
             'platform': 'android', 'renderer': 'robolectric-native',
             'imageHash': hashlib.sha256(image.read_bytes()).hexdigest(),
             'targetBounds': [0, 0, 160, 160], 'clockAutoAdvance': False,
             'themeIdentity': {k: 'a' * 64 for k in ('tokenHash', 'manifestHash', 'configHash')},
             'versions': {'sdk': '36', 'roborazzi': '1.76.0', 'robolectric': '4.17'}}
    return meta, facts, image


def test_measured_capture_returns_strict_core_meta(capture):
    meta, facts, image = capture
    actual = prepare_capture(meta, facts, image)
    assert actual == {**meta, 'platform': 'android', 'renderer': 'robolectric-native'}
    assert 'themeIdentity' not in actual


@pytest.mark.parametrize('field,value', [
    ('density', 2), ('density', float('nan')), ('density', float('inf')), ('fontScale', 1.5), ('usedFontHashes', {'roboto_regular.ttf': 'b' * 64}),
    ('crop', [1, 0, 159, 160]), ('pixelSize', [159, 160]),
    ('targetBounds', [0, 0, 159, 160]), ('imageHash', 'c' * 64),
    ('containsText', True), ('animation', 'running'), ('clockAutoAdvance', True),
    ('renderer', 'unknown'), ('locale', 'ar-EG'), ('direction', 'rtl')])
def test_similar_image_blocks_when_observed_facts_differ(capture, field, value):
    meta, facts, image = capture
    facts[field] = value
    with pytest.raises(ComposeError):
        prepare_capture(meta, facts, image)


def test_png_dimensions_are_observed(capture):
    meta, facts, image = capture
    Image.new('RGB', (159, 160), 'white').save(image)
    facts['imageHash'] = hashlib.sha256(image.read_bytes()).hexdigest()
    with pytest.raises(ComposeError):
        prepare_capture(meta, facts, image)

@pytest.mark.parametrize('mutation', ['compiled', 'generated', 'manifest', 'config', 'font'])
def test_current_theme_and_resources_block_stale_capture(tmp_path, capture, mutation):
    import shutil
    import sys
    from compose_adapter.capture_metadata import verify_rendered_theme
    project = tmp_path / 'project'
    sample = ROOT / 'samples/compose-fixture'
    for relative in ['.workflow/compose-theme.json', 'app/src/main/java/dev/figma/fixture/core/theme', 'app/src/main/res/font']:
        source = sample / relative
        if source.is_dir():
            shutil.copytree(source, project / relative)
        else:
            (project / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, project / relative)
    config = tmp_path / 'config.json'
    shutil.copyfile(ROOT / 'tests/fixtures/compose-v1/design/figma/compose/config.json', config)
    measured = capture[1]
    manifest_path = project / '.workflow/compose-theme.json'
    manifest = json.loads(manifest_path.read_text())
    measured['themeIdentity'] = {k: manifest[k] for k in ('tokenHash', 'manifestHash', 'configHash')}
    command = [sys.executable, str(ROOT / 'plugins/figma-core/scripts/core.py')]
    verify_rendered_theme(project, ROOT / 'tests/fixtures/compose-v1', config, measured, command)
    if mutation == 'compiled': measured['themeIdentity']['tokenHash'] = 'e' * 64
    if mutation == 'generated':
        (project / next(iter(manifest['files']))).write_text('// stale')
    if mutation == 'manifest':
        manifest['files'] = {}
        manifest_path.write_text(json.dumps(manifest))
    if mutation == 'config': config.write_text('{}')
    if mutation == 'font': (project / 'app/src/main/res/font/roboto_regular.ttf').write_bytes(b'wrong')
    with pytest.raises(ComposeError):
        verify_rendered_theme(project, ROOT / 'tests/fixtures/compose-v1', config, measured, command)


def test_declared_capture_variants_are_independent_and_canonical_immutable(tmp_path):
    from fixtures.compose_capture_variants import make_capture_bundle
    from figma_core.adapter_export import export_adapter
    source = ROOT / 'tests/fixtures/compose-v1'
    hashes = {p.relative_to(source): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}
    bundle = make_capture_bundle(source, tmp_path / 'bundle')
    receipt = export_adapter(bundle)
    assert len(receipt['nodes']) == 7
    variants = {n['id']: n['meta'] for n in receipt['nodes']}
    assert variants['synthetic:screen:home-w240']['logicalSize'] == [240, 160]
    assert variants['synthetic:screen:home-fs150']['textScale'] == 1.5
    assert hashes == {p.relative_to(source): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.rglob('*') if p.is_file()}


def test_prepare_capture_cli_checks_theme_before_publication(tmp_path, capture, monkeypatch, capsys):
    import compose
    meta, facts, image = capture
    project = tmp_path / 'project'
    project.mkdir()
    reference = tmp_path / 'reference.json'
    measured = tmp_path / 'measured.json'
    reference.write_text(json.dumps(meta))
    measured.write_text(json.dumps(facts))
    output = project / 'app/build/figma-candidates/home/actual-meta.json'
    checked = []
    monkeypatch.setattr(compose, 'verify_rendered_theme', lambda *args: checked.append('identity'))
    monkeypatch.setattr(compose, 'checked_paths', lambda *args: checked.append('paths'))
    args = ['prepare-capture', '--bundle', str(tmp_path), '--config', str(tmp_path / 'config'),
            '--project', str(project), '--core-command-json', '["trusted-core"]',
            '--reference-meta', str(reference), '--measured', str(measured), '--image', str(image), '--output', str(output)]
    assert compose.main(args) == 0
    assert checked == ['identity', 'paths']
    assert json.loads(output.read_text())['platform'] == 'android'
    assert json.loads(capsys.readouterr().out)['imageHash'] == facts['imageHash']
    def stale(*args):
        raise ComposeError('STALE_THEME', 'stale compiled identity')
    monkeypatch.setattr(compose, 'verify_rendered_theme', stale)
    output.unlink()
    assert compose.main(args) == 2
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)['code'] == 'STALE_THEME'


def test_template_matches_executed_harness():
    harness = (ROOT / 'samples/compose-fixture/app/src/test/java/dev/figma/fixture/FixtureCaptureTest.kt').read_text()
    template = (ROOT / 'plugins/figma-compose/templates/ComposeCaptureTest.kt').read_text()
    assert template.strip() == harness.replace('dev.figma.fixture', '__FIXTURE_PACKAGE__').replace('class FixtureCaptureTest', 'class ComposeCaptureTest').strip()


def test_android_fixture_enables_declared_rtl_capture_configuration():
    import xml.etree.ElementTree as ET
    manifest = ET.parse(ROOT / 'samples/compose-fixture/app/src/main/AndroidManifest.xml')
    assert manifest.find('application').get('{http://schemas.android.com/apk/res/android}supportsRtl') == 'true'
