"""Render explicitly mapped Material theme values."""
import json
from pathlib import Path


def material_defaults(config):
    schema = json.loads((Path(__file__).resolve().parents[2] / 'schemas/config.schema.json').read_text())
    roles = schema['properties']['material']['properties']
    return {group: sorted(set(roles[group]['properties']) - set(config['material'][group]))
            for group in roles}


def theme_body(config, modes):
    lines = []
    for mode in modes:
        for group, name, factory in [('colors', 'Colors', mode + 'ColorScheme'),
                                      ('typography', 'Typography', 'Typography'),
                                      ('shapes', 'Shapes', 'Shapes')]:
            arguments = []
            for role, path in sorted(config['material'][group].items()):
                expression = mode + 'Tokens.' + config['names'][path]
                if group == 'shapes':
                    expression = 'RoundedCornerShape(' + expression + ')'
                arguments.append('    ' + role + ' = ' + expression + ',')
            lines.append('internal val ' + mode + name + ' = ' + factory + '(\n' + '\n'.join(arguments) + '\n)')
    light = 'light' if 'light' in modes else modes[0]
    dark = 'dark' if 'dark' in modes else modes[0]
    lines.append('''@Composable
fun AppTheme(dark: Boolean, content: @Composable () -> Unit) {
    val tokens = if (dark) DARKTokens else LIGHTTokens
    CompositionLocalProvider(LocalAppTokens provides tokens) {
        MaterialTheme(
            colorScheme = if (dark) DARKColors else LIGHTColors,
            typography = if (dark) DARKTypography else LIGHTTypography,
            shapes = if (dark) DARKShapes else LIGHTShapes,
            content = content,
        )
    }
}'''.replace('DARK', dark).replace('LIGHT', light))
    return '\n\n'.join(lines) + '\n'
