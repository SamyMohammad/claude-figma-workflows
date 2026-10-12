"""Independent synthetic vectors; no app capture or live Figma input."""
import hashlib
import json
import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
from fixtures.make_core_fixture import make_fixture, _write_json
from figma_core.approvals import content_hash
from figma_core.paths import safe_path
from figma_core.schema import validate_document


def verify_component_sources(bundle: Path, project: Path) -> None:
    document = json.loads((bundle / 'component-map.json').read_text())
    validate_document('component-map', document)
    manifest = json.loads((bundle / 'manifest.json').read_text())
    variants = {(n['id'], n['variant']) for n in manifest['nodes'] if n['kind'] == 'component'}
    for item in document['components']:
        if (item['nodeId'], item['variant']) not in variants:
            raise ValueError('component variant mismatch')
        path = safe_path(project, item['path'])
        if not path.is_file():
            raise ValueError('missing component source')
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sourceHash']:
            raise ValueError('stale component source')
        if not re.search(r'fun\s+' + re.escape(item['symbol']) + r'\s*\(', path.read_text()):
            raise ValueError('missing component symbol')


def make_compose_fixture(root: Path, font: Path) -> Path:
    make_fixture(root)
    font_hash = hashlib.sha256(font.read_bytes()).hexdigest()
    shutil.copyfile(font, root / 'roboto_regular.ttf')
    tokens = json.loads((root / 'tokens.json').read_text())
    for mode in ('light', 'dark'):
        group = tokens[mode]
        group['type']['body']['$value']['fontFamily'] = 'Roboto'
        group['type']['body']['$value']['fontSize']['value'] = 16
        group['type']['body']['$value']['lineHeight'] = 1.5
        group['color']['onPrimary'] = {'$type': 'color', '$value': {'colorSpace': 'srgb', 'components': [1,1,1], 'alpha': 1}}
        group['color']['background'] = {'$type': 'color', '$value': {'colorSpace': 'srgb', 'components': [1,1,1] if mode == 'light' else [0,0,0], 'alpha': 1}}
        for category, name, value in [('shape','radius',16),('frame','size',160),('control','height',48),('card','height',64),('badge','size',32)]:
            group[category] = {name: {'$type':'dimension','$value':{'value':value,'unit':'px'}}}
    _write_json(root/'tokens.json',tokens)
    _write_json(root/'tokens-approval.json',{'schemaVersion':1,'kind':'tokens','contentHash':content_hash(tokens),'owner':'synthetic-fixture-author','evidence':'Declared vector fixture only; no live Figma approval','approvedAt':'2026-10-10T00:00:00Z','modes':['light','dark'],'deviations':[]})
    _write_json(root/'fonts.json',{'schemaVersion':1,'fonts':[{'family':'Roboto','weight':400,'path':'roboto_regular.ttf','sha256':font_hash,'status':'available','license':'approved'}]})
    manifest=json.loads((root/'manifest.json').read_text())
    for n in manifest['nodes']:
        folder=root/n['path']; name=n['id'].split(':')[-1]
        meta=json.loads((folder/'meta.json').read_text())
        meta.update(logicalSize=[160,160],pixelSize=[160,160],crop=[0,0,160,160])
        if name in ('review','badge'): meta.update(theme='dark',direction='rtl')
        _write_json(folder/'meta.json',meta)
        image=Image.new('RGB',(160,160),'#000000' if meta['theme']=='dark' else '#ffffff')
        draw=ImageDraw.Draw(image)
        shapes={'button':[(8,56,152,104,16)],'card':[(8,48,152,112,16)],'badge':[(64,64,96,96,16)],'home':[(8,8,152,72,16),(8,80,40,112,16),(8,112,152,160,16)],'review':[(8,8,152,72,16),(112,80,144,112,16),(8,112,152,160,16)]}[name]
        for x,y,r,b,radius in shapes: draw.rounded_rectangle((x,y,r-1,b-1),radius=radius,fill='#336699')
        image.save(folder/'reference.png')
        (folder/'context.md').write_text(f'''# Synthetic {name}\nID: {n['id']}; variant: {n['variant']}. No live Figma source.\nGraphic-only frame: 160 x 160 logical px, scale 1; theme {meta['theme']}, direction {meta['direction']}.\nIndependent Pillow rounded rectangles (left,top,right-exclusive,bottom-exclusive,radius): {shapes}.\nPrimary #336699, background {'#000000' if meta['theme']=='dark' else '#ffffff'}, radius 16, spacing 8.\nText layer is separate from the no-text graphic reference: Roboto weight 400, size 16, line height 24, tracking 0.\nApp text: Home or Review; card Synthetic content; badge Ready; action Continue or Back. Continue selects Review; Back selects Home. Components take typed state/callbacks.\nNo-text references do not establish text golden fidelity.\n''',encoding='utf-8')
    config={'schemaVersion':1,'packageName':'dev.figma.fixture.core.theme','themeDirectory':'app/src/main/java/dev/figma/fixture/core/theme','remBasePx':None,'names':{},'material':{'colors':{'primary':'color.primary','onPrimary':'color.onPrimary','background':'color.background'},'typography':{'bodyLarge':'type.body'},'shapes':{role:'shape.radius' for role in ('extraSmall','small','medium','large','extraLarge')}},'fonts':{'Roboto':{'400':{'resource':'dev.figma.fixture.R.font.roboto_regular','projectPath':'app/src/main/res/font/roboto_regular.ttf','sha256':font_hash}}},'allowedMaterialDefaults':['colorScheme:unmapped','typography:unmapped']}
    _write_json(root/'design/figma/compose/config.json',config)
    project=Path(__file__).resolve().parents[2]/'samples/compose-fixture'
    shutil.copyfile(project / 'app/src/main/assets/Roboto-OFL.txt', root / 'Roboto-OFL.txt')
    (root / 'README.md').write_text('# Synthetic Compose source bundle\n\nAll IDs, contexts and references are synthetic. Graphic PNGs are independently drawn Pillow vectors containing no text. Roboto text is a separate app rendering layer; no real-font golden or live Figma fidelity is established. Original font bytes and OFL notice are preserved.\n', encoding='utf-8')
    entries=[]
    for name,symbol in [('button','ActionButton'),('card','ContentCard'),('badge','StatusBadge')]:
        path=f'app/src/main/java/dev/figma/fixture/core/components/{symbol}.kt'
        entries.append({'nodeId':f'synthetic:component:{name}','variant':'default','platform':'compose','path':path,'symbol':symbol,'sourceHash':hashlib.sha256((project/path).read_bytes()).hexdigest()})
    _write_json(root/'component-map.json',{'schemaVersion':1,'components':entries})
    (root / '.gitattributes').write_text('* -text\n', encoding='utf-8')
    manifest['files']={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p!=root/'manifest.json'}
    _write_json(root/'manifest.json',manifest)
    return root
