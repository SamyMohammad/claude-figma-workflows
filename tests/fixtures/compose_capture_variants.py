"""Independent test variants and explicitly synthetic approvals; never live authority."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw
from figma_core.approvals import content_hash


def _write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, sort_keys=True, indent=2) + '\n', encoding='utf-8')


def _approval(kind, document, modes):
    return {'schemaVersion': 1, 'kind': kind, 'contentHash': content_hash(document),
            'owner': 'synthetic-capture-test', 'evidence': 'Independent test vectors only; no live source or owner approval',
            'approvedAt': '2026-10-10T00:00:00Z', 'modes': modes, 'deviations': []}


def make_capture_bundle(source: Path, destination: Path) -> Path:
    shutil.copytree(source, destination)
    manifest = json.loads((destination / 'manifest.json').read_text())
    home = next(node for node in manifest['nodes'] if node['id'] == 'synthetic:screen:home')
    for suffix, width, scale in [('w240', 240, 1), ('fs150', 160, 1.5)]:
        node = copy.deepcopy(home)
        node.update(id='synthetic:screen:home-' + suffix, path='screens/home-' + suffix)
        folder = destination / node['path']
        folder.mkdir(parents=True)
        meta = json.loads((destination / home['path'] / 'meta.json').read_text())
        meta.update(nodeId=node['id'], logicalSize=[width, 160], pixelSize=[width, 160], crop=[0, 0, width, 160], textScale=scale)
        _write(folder / 'meta.json', meta)
        image = Image.new('RGB', (width, 160), '#ffffff')
        draw = ImageDraw.Draw(image)
        for x, y, right, bottom in [(8, 8, 152, 72), (8, 80, 40, 112), (8, 112, 152, 160)]:
            draw.rounded_rectangle((x, y, right - 1, bottom - 1), radius=16, fill='#336699')
        image.save(folder / 'reference.png')
        (folder / 'context.md').write_text(f'Synthetic no-text Home variant: width {width}, height160, fontScale{scale}. Independent vectors; left anchored160px scene. No text fidelity claim.\n')
        manifest['nodes'].append(node)
        manifest['scope'].append(node['id'])
    policy = json.loads((destination / 'comparison-policy.json').read_text())
    _write(destination / 'policy-approval.json', _approval('policy', policy, ['light', 'dark']))
    for node in manifest['nodes']:
        folder = destination / node['path']
        identity = {key: hashlib.sha256((folder / name).read_bytes()).hexdigest()
                    for key, name in [('referenceHash', 'reference.png'), ('metaHash', 'meta.json')]}
        meta = json.loads((folder / 'meta.json').read_text())
        _write(folder / 'reference-approval.json', _approval('reference', identity, [meta['theme']]))
    manifest['files'] = {path.relative_to(destination).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in sorted(destination.rglob('*')) if path.is_file() and path != destination / 'manifest.json'}
    _write(destination / 'manifest.json', manifest)
    return destination
