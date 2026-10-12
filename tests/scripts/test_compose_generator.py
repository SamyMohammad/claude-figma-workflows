from fixtures.compose_receipt import make_receipt


def fixture_config():
    return {
        "schemaVersion": 1, "packageName": "dev.figma.fixture.core.theme",
        "themeDirectory": "app/src/main/java/dev/figma/fixture/core/theme",
        "remBasePx": None, "names": {},
        "material": {
            "colors": {"primary": "color.primary", "onPrimary": "color.onPrimary", "background": "color.background"},
            "typography": {"bodyLarge": "type.body"},
            "shapes": {"extraSmall": "shape.radius", "small": "shape.radius", "medium": "shape.radius", "large": "shape.radius", "extraLarge": "shape.radius"}},
        "fonts": {"Roboto": {"400": {"resource": "dev.figma.fixture.R.font.roboto_regular",
                                    "projectPath": "app/src/main/res/font/roboto_regular.ttf", "sha256": "a" * 64}}},
        "allowedMaterialDefaults": ["colorScheme:unmapped", "typography:unmapped"],
    }


def test_fractional_spacing_is_not_rounded():
    from fixtures.compose_receipt import make_receipt
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    receipt["resolvedByMode"]["light"]["space.small"]["value"]["value"] = 13.3
    files = render_theme(receipt, fixture_config())
    assert "13.3.dp" in files["AppTokenValues.kt"]


def test_generated_name_collision_blocks():
    import pytest
    from fixtures.compose_receipt import make_receipt
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    receipt["resolvedByMode"]["light"]["space_small"] = receipt["resolvedByMode"]["light"]["space.small"]
    with pytest.raises(ValueError, match="collision"):
        render_theme(receipt, fixture_config())


def test_deterministic_alias_alpha_and_dark_typography():
    from compose_adapter.generator import render_theme
    from copy import deepcopy
    receipt = make_receipt()
    before = deepcopy(receipt)
    receipt['resolvedByMode']['dark']['type.body']['value']['fontSize']['value'] = 20
    receipt['resolvedByMode']['light']['color.primary']['value']['alpha'] = 0.25
    files = render_theme(receipt, fixture_config())
    assert files == render_theme(receipt, fixture_config())
    assert '0.25f' in files['AppTokenValues.kt']
    assert '20.sp' in files['AppTokenValues.kt']
    assert '19.6.sp' in files['AppTokenValues.kt']
    assert 'if (dark) darkTypography else lightTypography' in files['AppTheme.kt']
    assert before['resolvedByMode']['light']['space.small']['value'] == receipt['resolvedByMode']['light']['space.small']['value']


def test_rem_explicit_base():
    import pytest
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    receipt['resolvedByMode']['light']['space.small']['value'] = {'value': 1.5, 'unit': 'rem'}
    with pytest.raises(ValueError, match='rem'):
        render_theme(receipt, fixture_config())
    config = fixture_config()
    config['remBasePx'] = 16
    assert '24.dp' in render_theme(receipt, config)['AppTokenValues.kt']


import pytest


@pytest.mark.parametrize('path,value', [('space.small', 1e100), ('space.small', 1e-100),
    ('shape.radius', -1), ('motion.duration', 2147483648), ('motion.duration', 13.3), ('type.body', -1)])
def test_unrepresentable_or_invalid_values_block(path, value):
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    token = receipt['resolvedByMode']['light'][path]['value']
    if path == 'type.body':
        token['fontSize']['value'] = value
    else:
        token['value'] = value
    with pytest.raises(ValueError):
        render_theme(receipt, fixture_config())


@pytest.mark.parametrize('name', ['when', 'x();', 'évil', 'valid\n'])
def test_injected_names_block(name):
    from compose_adapter.generator import render_theme
    config = fixture_config()
    config['names'] = {'space.small': name}
    with pytest.raises(ValueError):
        render_theme(make_receipt(), config)


def test_unapproved_defaults_block():
    from compose_adapter.generator import render_theme
    config = fixture_config()
    del config['material']['shapes']['extraSmall']
    with pytest.raises(ValueError, match='authorization'):
        render_theme(make_receipt(), config)
    config['allowedMaterialDefaults'].append('shapes:unmapped')
    assert render_theme(make_receipt(), config)


def test_missing_font_mapping_blocks():
    from compose_adapter.generator import render_theme
    config = fixture_config()
    config['fonts'] = {}
    with pytest.raises(ValueError, match='font'):
        render_theme(make_receipt(), config)


@pytest.mark.parametrize('alias,weight', [
    ('thin', 100), ('hairline', 100), ('extra-light', 200), ('ultra-light', 200),
    ('light', 300), ('normal', 400), ('regular', 400), ('book', 400), ('medium', 500),
    ('semi-bold', 600), ('demi-bold', 600), ('bold', 700), ('extra-bold', 800),
    ('ultra-bold', 800), ('black', 900), ('heavy', 900), ('extra-black', 950), ('ultra-black', 950)])
def test_all_named_weights_preserve_numeric_weight_and_resource(alias, weight):
    from compose_adapter.kotlin_values import kotlin_value
    config = fixture_config()
    config['fonts']['Roboto'][str(weight)] = {'resource': 'R.font.selected',
        'projectPath': 'res/font/selected.ttf', 'sha256': 'a' * 64}
    assert kotlin_value({'type': 'fontWeight', 'value': alias}, config) == ('FontWeight', f'FontWeight({weight})')
    value = {'fontFamily': 'Roboto', 'fontWeight': alias, 'fontSize': {'value': 14, 'unit': 'px'},
             'lineHeight': 1.4, 'letterSpacing': {'value': 0, 'unit': 'px'}}
    kind, rendered = kotlin_value({'type': 'typography', 'value': value}, config)
    assert kind == 'TextStyle'
    assert f'Font(R.font.selected, weight = FontWeight({weight}))' in rendered


@pytest.mark.parametrize('derived', ['rem', 'lineHeight'])
def test_decimal_nonzero_underflow_is_rejected(derived):
    from compose_adapter.generator import render_theme
    receipt = make_receipt()
    config = fixture_config()
    if derived == 'rem':
        receipt['resolvedByMode']['light']['space.small']['value'] = {'value': 1e-300, 'unit': 'rem'}
        config['remBasePx'] = 1e-300
    else:
        receipt['resolvedByMode']['light']['type.body']['value']['fontSize']['value'] = 1e-30
        receipt['resolvedByMode']['light']['type.body']['value']['lineHeight'] = 1e-300
    with pytest.raises(ValueError, match='represented'):
        render_theme(receipt, config)
