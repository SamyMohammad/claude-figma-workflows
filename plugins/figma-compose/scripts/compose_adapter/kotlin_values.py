"""Faithful Kotlin literals with explicit target range checks."""
import math
import struct
from decimal import Decimal

from .errors import ComposeError


def number(value):
    try:
        result = float(value)
        packed = struct.pack('f', result)
        target = struct.unpack('f', packed)[0]
    except (ValueError, TypeError, OverflowError, struct.error):
        raise ComposeError('VALUE_RANGE', 'Value cannot be represented by Kotlin Float') from None
    if not math.isfinite(target) or (result != 0 and target == 0):
        raise ComposeError('VALUE_RANGE', 'Value cannot be represented by Kotlin Float')
    return str(value) if isinstance(value, int) else repr(value)


def dimension(value, config, unit='dp', nonnegative=False):
    amount = Decimal(str(value['value']))
    if value['unit'] == 'rem':
        if config['remBasePx'] is None:
            raise ComposeError('REM_BASE', 'rem requires explicit remBasePx')
        amount *= Decimal(str(config['remBasePx']))
    if nonnegative and amount < 0:
        raise ComposeError('VALUE_RANGE', 'Negative shape or font size')
    literal = format(amount, 'f').rstrip('0').rstrip('.') if '.' in format(amount, 'f') else str(amount)
    number(float(amount))
    if '.' not in literal and not -2147483648 <= amount <= 2147483647:
        literal += '.0'
    return literal + '.' + unit


def kotlin_value(token, config, shape=False):
    kind, value = token['type'], token['value']
    if kind == 'number':
        return 'Float', number(value) + 'f'
    if kind == 'fontFamily':
        families = value if isinstance(value, list) else [value]
        if len(families) != 1 or not config['fonts'].get(families[0]):
            raise ComposeError('FONT_MAPPING', 'Font family requires one explicitly mapped family')
        fonts = config['fonts'][families[0]]
        return 'FontFamily', 'FontFamily(' + ', '.join('Font(' + font['resource'] + ', weight = FontWeight(' + weight + '))'
            for weight, font in sorted(fonts.items(), key=lambda item: int(item[0]))) + ')'
    if kind == 'fontWeight':
        weight = {'normal': 400, 'bold': 700}.get(value, value)
        if not isinstance(weight, (int, float)) or int(weight) != weight:
            raise ComposeError('VALUE_RANGE', 'FontWeight requires integral weight')
        return 'FontWeight', 'FontWeight(' + str(int(weight)) + ')'
    if kind == 'dimension':
        return 'Dp', dimension(value, config, nonnegative=shape)
    if kind == 'color':
        values = value['components'] + [value.get('alpha', 1)]
        return 'Color', 'Color(' + ', '.join(number(v) + 'f' for v in values) + ')'
    if kind == 'duration':
        amount = Decimal(str(value['value'])) * (1000 if value['unit'] == 's' else 1)
        if amount != amount.to_integral_value() or not 0 <= amount <= 2147483647:
            raise ComposeError('VALUE_RANGE', 'Duration requires representable Int milliseconds')
        return 'Int', str(int(amount))
    if kind == 'cubicBezier':
        return 'CubicBezierEasing', 'CubicBezierEasing(' + ', '.join(number(v) + 'f' for v in value) + ')'
    if kind == 'typography':
        weight_value = {'normal': 400, 'bold': 700}.get(value['fontWeight'], value['fontWeight'])
        if int(weight_value) != weight_value:
            raise ComposeError('VALUE_RANGE', 'FontWeight requires integral weight')
        weight = str(int(weight_value))
        font = config['fonts'].get(value['fontFamily'], {}).get(weight)
        if font is None:
            raise ComposeError('FONT_MAPPING', 'Every font family/weight requires a resource mapping')
        size = dimension(value['fontSize'], config, 'sp', True)
        line = Decimal(size[:-3]) * Decimal(str(value['lineHeight']))
        return 'TextStyle', ('TextStyle(fontFamily = FontFamily(Font(' + font['resource'] +
            ', weight = FontWeight(' + weight + '))), fontWeight = FontWeight(' + weight +
            '), fontSize = ' + size + ', lineHeight = ' + number(float(line)) +
            '.sp, letterSpacing = ' + dimension(value['letterSpacing'], config, 'sp') + ')')
    raise ComposeError('TOKEN_TYPE', 'Unsupported Kotlin token type')
