import json
import shutil
from pathlib import Path

import pytest

from fixtures.make_compose_fixture import make_compose_fixture, verify_component_sources
from figma_core.adapter_export import export_adapter

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / 'samples/compose-fixture/app/src/main/res/font/roboto_regular.ttf'

def test_synthetic_bundle_has_five_contexts_and_real_font(tmp_path):
    root = make_compose_fixture(tmp_path / 'bundle', FONT)
    receipt = export_adapter(root)
    assert len(receipt['nodes']) == 5
    assert all(n['meta']['logicalSize'] == [160, 160] for n in receipt['nodes'])
    assert receipt['fonts']['fonts'][0]['sha256'] == 'd7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134'

def test_component_sources_are_current():
    verify_component_sources(ROOT / 'tests/fixtures/compose-v1', ROOT / 'samples/compose-fixture')


@pytest.mark.parametrize('mutation, expected', [('variant','variant'),('symbol','symbol'),('hash','stale'),('missing','missing'),('escape','path')])
def test_component_mapping_rejects_drift(tmp_path, mutation, expected):
    bundle = tmp_path / 'bundle'
    shutil.copytree(ROOT / 'tests/fixtures/compose-v1', bundle)
    document = json.loads((bundle / 'component-map.json').read_text())
    entry = document['components'][0]
    if mutation == 'variant': entry['variant'] = 'unmapped'
    if mutation == 'symbol': entry['symbol'] = 'AbsentSymbol'
    if mutation == 'hash': entry['sourceHash'] = '0' * 64
    if mutation == 'missing': entry['path'] = 'app/Missing.kt'
    if mutation == 'escape': entry['path'] = '../escape.kt'
    (bundle / 'component-map.json').write_text(json.dumps(document))
    with pytest.raises(ValueError, match=expected):
        verify_component_sources(bundle, ROOT / 'samples/compose-fixture')
