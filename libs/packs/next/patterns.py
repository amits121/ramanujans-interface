#!/usr/bin/env python3
"""
Next.js pack (NXT-01 to NXT-07): Next.js primitives and conventions. Target: next.
Module-level patterns (metadata, font, dynamic) render nothing in the body and emit
their code through the pattern's `module` block.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

import json
from typing import Any, Dict, List

from libs.jsx import attrs, handler, req, t
from pattern_library import Pattern


def image(p: Dict) -> str:
    req(p, 'NXT-01', 'src', 'alt', 'width', 'height')
    return f'<Image{attrs({"src": p["src"], "alt": p["alt"], "width": int(p["width"]), "height": int(p["height"]), "priority": p.get("priority")})} />'


def link(p: Dict) -> str:
    req(p, 'NXT-02', 'href', 'text')
    return f'<Link{attrs({"href": p["href"], "prefetch": p.get("prefetch")})}>{t(p["text"])}</Link>'


def script(p: Dict) -> str:
    req(p, 'NXT-03', 'src')
    return f'<Script{attrs({"src": p["src"], "strategy": p.get("strategy", "afterInteractive")})} />'


def metadata(p: Dict) -> str:
    req(p, 'NXT-04', 'title')
    return ''


def font(p: Dict) -> str:
    req(p, 'NXT-05', 'family', 'text')
    return f'<span className={{{p["family"].lower()}.className}}>{t(p["text"])}</span>'


def dynamic(p: Dict) -> str:
    req(p, 'NXT-06', 'name', 'path')
    return f'<{p["name"]} />'


def form(p: Dict) -> str:
    req(p, 'NXT-07', 'action', 'fields')
    rows = ''.join(f'<label htmlFor={t("f-" + f["name"])}>{t(f["label"])}</label>'
                   f'<input{attrs({"id": "f-" + f["name"], "name": f["name"], "type": f.get("type", "text"), "required": f.get("required")})} />'
                   for f in p['fields'])
    action = p['action'] if p['action'].startswith('/') else '{' + p['action'] + '}'
    act = f'action={t(action)}' if action.startswith('/') else f'action={action}'
    return f'<Form {act}>{rows}<button type="submit">{t(p.get("submit", "Submit"))}</button></Form>'


class _Meta:
    """Builds module code from props at generation time (pure)."""


def _module_metadata(p: Dict) -> Dict[str, str]:
    data = {'title': p['title']}
    if p.get('description'):
        data['description'] = p['description']
    return {'next-metadata': 'export const metadata = ' + json.dumps(data, ensure_ascii=False) + ';'}


def _module_font(p: Dict) -> Dict[str, str]:
    subsets = json.dumps(p.get('subsets', ['latin']))
    return {f'next-font-{p["family"].lower()}': f'const {p["family"].lower()} = {p["family"]}({{ subsets: {subsets} }});'}


def _module_dynamic(p: Dict) -> Dict[str, str]:
    ssr = 'true' if p.get('ssr', False) else 'false'
    return {f'next-dynamic-{p["name"]}': f"const {p['name']} = dynamic(() => import({json.dumps(p['path'])}), {{ ssr: {ssr} }});"}


class ModulePattern(Pattern):
    """A pattern whose module block and imports depend on its props."""

    def __init__(self, *args, module_fn=None, imports_fn=None, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, 'module_fn', module_fn)
        object.__setattr__(self, 'imports_fn', imports_fn)

    def generate(self, props: Dict[str, Any]) -> str:
        if self.module_fn:
            self.module.clear()
            self.module.update(self.module_fn(props))
        if self.imports_fn:
            self.imports.clear()
            self.imports.update(self.imports_fn(props))
        return self.generator(props)


PATTERNS: List[Pattern] = [
    Pattern('NXT-01', 'Image', 'C', 'next/image with explicit size', image, imports={'next/image': ['default:Image']}),
    Pattern('NXT-02', 'Link', 'C', 'next/link', link, imports={'next/link': ['default:Link']}),
    Pattern('NXT-03', 'Script', 'C', 'next/script with strategy', script, imports={'next/script': ['default:Script']}),
    ModulePattern('NXT-04', 'Metadata', 'X', 'metadata export for the route', metadata, module_fn=_module_metadata),
    ModulePattern('NXT-05', 'Google Font', 'X', 'next/font/google with className usage', font,
                  module_fn=_module_font, imports_fn=lambda p: {'next/font/google': [p['family']]}),
    ModulePattern('NXT-06', 'Dynamic Import', 'F', 'next/dynamic component', dynamic,
                  module_fn=_module_dynamic, imports_fn=lambda p: {'next/dynamic': ['default:dynamic']}),
    Pattern('NXT-07', 'Form', 'E', 'next/form with labelled fields', form, imports={'next/form': ['default:Form']}),
]

TYPE_MAPPING = {'next-image': 'NXT-01', 'next-link': 'NXT-02', 'next-script': 'NXT-03', 'next-metadata': 'NXT-04',
                'next-font': 'NXT-05', 'next-dynamic': 'NXT-06', 'next-form': 'NXT-07'}

SAMPLES: Dict[str, Dict[str, Any]] = {
    'NXT-01': {'src': '/hero.png', 'alt': 'Hero', 'width': 1200, 'height': 800, 'priority': True},
    'NXT-02': {'href': '/about', 'text': 'About', 'prefetch': False},
    'NXT-03': {'src': 'https://example.invalid/widget.js', 'strategy': 'lazyOnload'},
    'NXT-04': {'title': 'Home', 'description': 'A page'},
    'NXT-05': {'family': 'Inter', 'text': 'Hello', 'subsets': ['latin']},
    'NXT-06': {'name': 'Chart', 'path': '../components/Chart', 'ssr': False},
    'NXT-07': {'action': '/search', 'fields': [{'name': 'q', 'label': 'Query', 'required': True}], 'submit': 'Go'},
}


def register(library) -> None:
    for pattern in PATTERNS:
        library.register(pattern)
