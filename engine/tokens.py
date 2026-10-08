#!/usr/bin/env python3
"""
Design Tokens Module

Turns a theme file (YAML, see tokens/default.yaml) into CSS custom properties.
Pure: css_from_tokens() depends only on the token dictionary; keys are emitted
in sorted order so the stylesheet is byte-identical for identical tokens.

Pipeline Position:
    theme.yaml -> [tokens] -> theme.css   (consumed by site/site.css and the patterns)

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

from typing import Any, Dict

import yaml

REQUIRED = {
    'color': ('primary', 'background', 'surface', 'text_primary', 'text_secondary', 'border'),
    'font': ('family', 'size', 'weight', 'line_height'),
    'space': ('xs', 'sm', 'md', 'lg', 'xl'),
    'radius': ('sm', 'md', 'lg'),
    'shadow': ('sm', 'md', 'lg'),
    'breakpoint': ('desktop',),
}


def validate_tokens(tokens: Dict[str, Any]) -> None:
    """Raise ValueError naming the first missing group or key."""
    for group, keys in REQUIRED.items():
        if group not in tokens or not isinstance(tokens[group], dict):
            raise ValueError(f'tokens: missing group "{group}"')
        for key in keys:
            if key not in tokens[group]:
                raise ValueError(f'tokens: missing "{group}.{key}"')
    for name, pair in tokens['font']['size'].items():
        if not (isinstance(pair, list) and len(pair) == 2):
            raise ValueError(f'tokens: font.size.{name} must be [mobile, desktop]')


def _var(name: str) -> str:
    return '--' + name.replace('_', '-')


def css_from_tokens(tokens: Dict[str, Any]) -> str:
    """Emit :root custom properties plus the desktop overrides for font sizes."""
    validate_tokens(tokens)
    root = []
    for key in sorted(tokens['color']):
        root.append(f'  {_var("color_" + key)}: {tokens["color"][key]};')
    root.append(f'  {_var("font_family")}: {tokens["font"]["family"]};')
    for key in sorted(tokens['font']['size']):
        root.append(f'  {_var("font_size_" + key)}: {tokens["font"]["size"][key][0]}px;')
    for key in sorted(tokens['font']['weight']):
        root.append(f'  {_var("font_weight_" + key)}: {tokens["font"]["weight"][key]};')
    for key in sorted(tokens['font']['line_height']):
        root.append(f'  {_var("line_height_" + key)}: {tokens["font"]["line_height"][key]};')
    for group in ('space', 'radius'):
        for key in sorted(tokens[group]):
            root.append(f'  {_var(group + "_" + key)}: {tokens[group][key]}px;')
    for key in sorted(tokens['shadow']):
        root.append(f'  {_var("shadow_" + key)}: {tokens["shadow"][key]};')

    desktop = [
        f'    {_var("font_size_" + key)}: {tokens["font"]["size"][key][1]}px;'
        for key in sorted(tokens['font']['size'])
    ]
    name = tokens.get('name', 'theme')
    version = tokens.get('version', '')
    return (
        f'/* theme: {name} {version} - generated from tokens, do not edit */\n'
        ':root {\n' + '\n'.join(root) + '\n}\n'
        f'@media (min-width: {tokens["breakpoint"]["desktop"]}px) {{\n  :root {{\n'
        + '\n'.join(desktop) + '\n  }\n}\n'
    )


def load_tokens(path: str) -> Dict[str, Any]:
    """Read a theme file. File access happens here, never inside css_from_tokens()."""
    with open(path, 'r', encoding='utf-8') as f:
        tokens = yaml.safe_load(f)
    validate_tokens(tokens)
    return tokens


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: python tokens.py <theme.yaml>')
        sys.exit(1)
    sys.stdout.write(css_from_tokens(load_tokens(sys.argv[1])))
