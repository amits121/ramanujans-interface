#!/usr/bin/env python3
"""
Shared JSX helpers for every pattern pack.

    t(value)        -> {"..."}            escaped JSX text or attribute value
    s(value)        -> "..."              escaped plain string attribute (for custom elements)
    attrs(mapping)  -> ' a={"x"} b={1}'   attributes from a dict, keys sorted, None dropped
    req(props, pattern_id, *keys)         raise ValueError naming the first missing key
    handler(props, key)                   the handler name for an event prop, or ''

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

import json
from typing import Any, Dict

HANDLER_KEYS = ('onClick', 'onPress', 'onSubmit', 'onChange', 'onClose', 'onSelect', 'onOpen')


def t(value: Any) -> str:
    """JSX-safe text or attribute: a JSON string literal inside braces."""
    return '{' + json.dumps(str(value), ensure_ascii=False) + '}'


def s(value: Any) -> str:
    """A double-quoted attribute value with quotes, angle brackets and ampersands escaped."""
    text = str(value).replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return f'"{text}"'


def attrs(mapping: Dict[str, Any]) -> str:
    """Attributes from a dict. Strings become {"..."}, booleans and numbers braces, None is dropped."""
    parts = []
    for key in sorted(mapping):
        value = mapping[key]
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f'{key}={{{"true" if value else "false"}}}')
        elif isinstance(value, (int, float)):
            parts.append(f'{key}={{{value}}}')
        elif isinstance(value, str) and value.startswith('{') and value.endswith('}'):
            parts.append(f'{key}={value}')  # an expression supplied by the caller
        else:
            parts.append(f'{key}={t(value)}')
    return (' ' + ' '.join(parts)) if parts else ''


def req(props: Dict[str, Any], pattern_id: str, *keys: str) -> None:
    for key in keys:
        if key not in props or props[key] in ('', None, []):
            raise ValueError(f'{pattern_id} requires "{key}"')


def handler(props: Dict[str, Any], key: str) -> str:
    """The handler name for an event prop (e.g. onClick: handleSave), or ''."""
    value = props.get(key, '')
    return value if isinstance(value, str) and value.isidentifier() else ''


def expr(name: str) -> str:
    """Wrap an identifier as a JSX expression attribute value."""
    return '{' + name + '}'
