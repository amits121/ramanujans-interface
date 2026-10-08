#!/usr/bin/env python3
"""
Quality Gates Module - accessibility and performance checks on a built site.

Deterministic checks on the static output (no browser, no network):
  accessibility: html lang, title, viewport, exactly one h1, no skipped heading
                 levels, every image has alt text, every form control has a label,
                 navigation is labelled, links and buttons have text
  performance:   no script shipped, HTML and CSS within budget

    python quality.py <build-dir> [--html-max BYTES] [--css-max BYTES]

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import json
import os
import sys
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple

HTML_MAX = 60_000
CSS_MAX = 40_000
HEADINGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')


class _Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lang = None
        self.title = ''
        self.viewport = False
        self.headings: List[int] = []
        self.images_without_alt = 0
        self.scripts = 0
        self.nav_unlabelled = 0
        self.control_ids: List[str] = []
        self.label_for: List[str] = []
        self.empty_links = 0
        self.empty_buttons = 0
        self._text_stack: List[Tuple[str, str]] = []  # (tag, text so far)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        elif tag == 'meta' and a.get('name') == 'viewport':
            self.viewport = True
        elif tag in HEADINGS:
            self.headings.append(int(tag[1]))
        elif tag == 'img' and not (a.get('alt') or '').strip():
            self.images_without_alt += 1
        elif tag == 'script':
            self.scripts += 1
        elif tag == 'nav' and not (a.get('aria-label') or a.get('aria-labelledby')):
            self.nav_unlabelled += 1
        elif tag in ('input', 'textarea', 'select') and a.get('type') not in ('hidden', 'submit'):
            self.control_ids.append(a.get('id') or '')
        elif tag == 'label' and a.get('for'):
            self.label_for.append(a['for'])
        if tag in ('a', 'button', 'title'):
            self._text_stack.append((tag, ''))

    def handle_data(self, data):
        if self._text_stack:
            tag, text = self._text_stack[-1]
            self._text_stack[-1] = (tag, text + data)

    def handle_endtag(self, tag):
        if self._text_stack and self._text_stack[-1][0] == tag:
            _, text = self._text_stack.pop()
            if tag == 'title':
                self.title = text.strip()
            elif tag == 'a' and not text.strip():
                self.empty_links += 1
            elif tag == 'button' and not text.strip():
                self.empty_buttons += 1


def check_html(html: str) -> Dict[str, Any]:
    """Accessibility checks on one HTML document. Returns {name: (ok, detail)}."""
    audit = _Audit()
    audit.feed(html)
    skipped = any(b - a > 1 for a, b in zip(audit.headings, audit.headings[1:]))
    unlabelled = [cid for cid in audit.control_ids if not cid or cid not in audit.label_for]
    return {
        'html_lang': (bool(audit.lang), audit.lang or 'missing'),
        'title': (bool(audit.title), audit.title or 'missing'),
        'viewport_meta': (audit.viewport, 'present' if audit.viewport else 'missing'),
        'single_h1': (audit.headings.count(1) == 1, f'{audit.headings.count(1)} h1'),
        'heading_order': (not skipped, 'no skipped levels' if not skipped else 'skipped level'),
        'images_have_alt': (audit.images_without_alt == 0, f'{audit.images_without_alt} without alt'),
        'controls_have_labels': (not unlabelled, 'all labelled' if not unlabelled else f'unlabelled: {unlabelled}'),
        'nav_labelled': (audit.nav_unlabelled == 0, f'{audit.nav_unlabelled} unlabelled nav'),
        'links_have_text': (audit.empty_links == 0, f'{audit.empty_links} empty links'),
        'buttons_have_text': (audit.empty_buttons == 0, f'{audit.empty_buttons} empty buttons'),
        'no_script': (audit.scripts == 0, f'{audit.scripts} script tags'),
    }


def check_site(out_dir: str, html_max: int = HTML_MAX, css_max: int = CSS_MAX) -> Dict[str, Any]:
    """Run the accessibility checks on index.html and the size budget on the output."""
    index = os.path.join(out_dir, 'index.html')
    with open(index, 'r', encoding='utf-8') as f:
        html = f.read()
    checks = check_html(html)
    html_bytes = os.path.getsize(index)
    css_bytes = 0
    js_bytes = 0
    for dirpath, _, files in os.walk(out_dir):
        for name in files:
            size = os.path.getsize(os.path.join(dirpath, name))
            if name.endswith('.css'):
                css_bytes += size
            elif name.endswith('.js'):
                js_bytes += size
    checks['html_within_budget'] = (html_bytes <= html_max, f'{html_bytes} of {html_max} bytes')
    checks['css_within_budget'] = (css_bytes <= css_max, f'{css_bytes} of {css_max} bytes')
    checks['no_javascript_shipped'] = (js_bytes == 0, f'{js_bytes} bytes of js')
    return {'ok': all(ok for ok, _ in checks.values()), 'checks': checks}


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python quality.py <build-dir> [--html-max BYTES] [--css-max BYTES]')
        sys.exit(1)
    argv = sys.argv
    hmax = int(argv[argv.index('--html-max') + 1]) if '--html-max' in argv else HTML_MAX
    cmax = int(argv[argv.index('--css-max') + 1]) if '--css-max' in argv else CSS_MAX
    report = check_site(argv[1], hmax, cmax)
    for name, (ok, detail) in report['checks'].items():
        print(f'  {"PASS" if ok else "FAIL"}  {name:24s} {detail}')
    print('QUALITY PASS' if report['ok'] else 'QUALITY FAIL')
    sys.exit(0 if report['ok'] else 3)
