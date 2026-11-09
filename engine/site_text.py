#!/usr/bin/env python3
"""
Site text helpers shared by the site and publication patterns.

Every text value is emitted as a JSON string literal inside braces, so braces, angle brackets
and quotes in content can never break the generated file. Rich text allows one inline mark,
**bold**, which becomes a <strong> element; nothing else in content is interpreted.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import json
from typing import Any, Dict

BUTTON = 'site-button site-button-primary'
BUTTON_SECONDARY = 'site-button site-button-secondary'


def _t(value: Any) -> str:
    """JSX-safe text: {"..."}."""
    return '{' + json.dumps(str(value), ensure_ascii=False) + '}'


def _rich(value: Any) -> str:
    """JSX-safe text with **bold** segments rendered as <strong>. Unbalanced marks are refused."""
    parts = str(value).split('**')
    if len(parts) % 2 == 0:
        raise ValueError(f'unbalanced ** in text: {str(value)[:60]!r}')
    out = []
    for i, part in enumerate(parts):
        if not part:
            continue
        out.append(f'<strong>{_t(part)}</strong>' if i % 2 else _t(part))
    return ''.join(out)


def _req(props: Dict[str, Any], pattern_id: str, *keys: str) -> None:
    for key in keys:
        if key not in props or props[key] in ('', None, []):
            raise ValueError(f'{pattern_id} requires "{key}"')


def _link(item: Dict[str, Any], css: str = '') -> str:
    cls = f' className="{css}"' if css else ''
    return f'<a{cls} href={_t(item["href"])}>{_t(item["label"])}</a>'


def _heading(level: int, text: Any) -> str:
    level = min(max(int(level), 1), 4)
    return f'<h{level}>{_t(text)}</h{level}>'
