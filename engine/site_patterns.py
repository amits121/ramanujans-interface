#!/usr/bin/env python3
"""
Site Patterns Module (S-01 to S-10, L-07)

The ten patterns a hosted marketing site is assembled from, registered into the
PatternLibrary without touching the engine or the existing patterns. Output is
plain JSX (no component framework), styled by the classes in site/site.css and
the custom properties emitted by tokens.py.

Every text value is emitted as a JSON string literal inside braces, so braces,
angle brackets and quotes in content can never break the generated file.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import json
from typing import Any, Dict, List

from pattern_library import Pattern, PatternLibrary

SITE_TYPE_MAPPING = {
    'page': 'L-07',
    'image': 'S-01',
    'text-block': 'S-02',
    'nav-bar': 'S-03',
    'hero': 'S-04',
    'feature-grid': 'S-05',
    'footer': 'S-06',
    'contact-form': 'S-07',
    'cta-band': 'S-08',
    'testimonial': 'S-09',
    'faq': 'S-10',
}

BUTTON = 'site-button site-button-primary'
BUTTON_SECONDARY = 'site-button site-button-secondary'


def _t(value: Any) -> str:
    """JSX-safe text: {"..."}."""
    return '{' + json.dumps(str(value), ensure_ascii=False) + '}'


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


# ---- generators -------------------------------------------------------------------------------

def image(p: Dict) -> str:
    _req(p, 'S-01', 'src', 'alt')
    caption = f'<figcaption>{_t(p["caption"])}</figcaption>' if p.get('caption') else ''
    return (f'<figure className="site-image"><img src={_t(p["src"])} alt={_t(p["alt"])} '
            f'loading="lazy" />{caption}</figure>')


def text_block(p: Dict) -> str:
    _req(p, 'S-02', 'paragraphs')
    head = _heading(p.get('level', 2), p['heading']) if p.get('heading') else ''
    body = ''.join(f'<p>{_t(t)}</p>' for t in p['paragraphs'])
    return f'<section className="site-text">{head}{body}</section>'


def nav_bar(p: Dict) -> str:
    _req(p, 'S-03', 'brand', 'links')
    items = ''.join(f'<li>{_link(l)}</li>' for l in p['links'])
    cta = _link(p['cta'], BUTTON) if p.get('cta') else ''
    return (f'<nav className="site-nav" aria-label="Main"><a className="site-nav-brand" href="/">'
            f'{_t(p["brand"])}</a><ul className="site-nav-links">{items}</ul>{cta}</nav>')


def hero(p: Dict) -> str:
    _req(p, 'S-04', 'title')
    sub = f'<p className="site-hero-subtitle">{_t(p["subtitle"])}</p>' if p.get('subtitle') else ''
    actions = ''
    if p.get('primary_cta') or p.get('secondary_cta'):
        a = _link(p['primary_cta'], BUTTON) if p.get('primary_cta') else ''
        b = _link(p['secondary_cta'], BUTTON_SECONDARY) if p.get('secondary_cta') else ''
        actions = f'<p className="site-hero-actions">{a}{b}</p>'
    img = ''
    if p.get('image'):
        img = f'<img className="site-hero-image" src={_t(p["image"]["src"])} alt={_t(p["image"]["alt"])} />'
    return (f'<header className="site-hero"><div className="site-hero-text">{_heading(1, p["title"])}'
            f'{sub}{actions}</div>{img}</header>')


def feature_grid(p: Dict) -> str:
    _req(p, 'S-05', 'items')
    cols = min(max(int(p.get('columns', 3)), 2), 4)
    head = _heading(2, p['heading']) if p.get('heading') else ''
    cards = ''.join(f'<article className="site-feature">{_heading(3, i["title"])}<p>{_t(i["text"])}</p></article>'
                    for i in p['items'])
    return f'<section className="site-features">{head}<div className="site-grid site-grid-{cols}">{cards}</div></section>'


def footer(p: Dict) -> str:
    _req(p, 'S-06', 'brand', 'note')
    links = ''.join(f'<li>{_link(l)}</li>' for l in p.get('links', []))
    social = ''.join(f'<li>{_link(l)}</li>' for l in p.get('social', []))
    return (f'<footer className="site-footer"><div className="site-footer-brand">{_t(p["brand"])}</div>'
            f'<ul className="site-footer-links">{links}</ul><ul className="site-social">{social}</ul>'
            f'<p className="site-footer-note">{_t(p["note"])}</p></footer>')


def contact_form(p: Dict) -> str:
    _req(p, 'S-07', 'action')
    labels = {'name': 'Name', 'email': 'Email', 'message': 'Message', 'submit': 'Send', **p.get('labels', {})}
    head = _heading(2, p['heading']) if p.get('heading') else ''
    turnstile = (f'<div className="cf-turnstile" data-sitekey={_t(p["turnstile_site_key"])}></div>'
                 if p.get('turnstile_site_key') else '')
    return (f'<section className="site-contact">{head}<form className="site-form" method="post" action={_t(p["action"])}>'
            f'<label htmlFor="contact-name">{_t(labels["name"])}</label>'
            f'<input id="contact-name" name="name" type="text" required />'
            f'<label htmlFor="contact-email">{_t(labels["email"])}</label>'
            f'<input id="contact-email" name="email" type="email" required />'
            f'<label htmlFor="contact-message">{_t(labels["message"])}</label>'
            f'<textarea id="contact-message" name="message" rows={{5}} required></textarea>'
            f'{turnstile}<button type="submit" className="{BUTTON}">{_t(labels["submit"])}</button></form></section>')


def cta_band(p: Dict) -> str:
    _req(p, 'S-08', 'title', 'cta')
    text = f'<p>{_t(p["text"])}</p>' if p.get('text') else ''
    return f'<section className="site-cta">{_heading(2, p["title"])}{text}{_link(p["cta"], BUTTON)}</section>'


def testimonial(p: Dict) -> str:
    _req(p, 'S-09', 'quote', 'author')
    role = f', {p["role"]}' if p.get('role') else ''
    return (f'<figure className="site-testimonial"><blockquote>{_t(p["quote"])}</blockquote>'
            f'<figcaption>{_t(p["author"] + role)}</figcaption></figure>')


def faq(p: Dict) -> str:
    _req(p, 'S-10', 'items')
    head = _heading(2, p['heading']) if p.get('heading') else ''
    items = ''.join(f'<details className="site-faq-item"><summary>{_t(i["q"])}</summary><p>{_t(i["a"])}</p></details>'
                    for i in p['items'])
    return f'<section className="site-faq">{head}{items}</section>'


def page(p: Dict) -> str:
    return '<div className="page">{children}</div>'


PATTERNS: List[Pattern] = [
    Pattern('L-07', 'Page', 'layout', 'Vertical stack of site sections', page),
    Pattern('S-01', 'Image', 'site', 'Image with required alt text and optional caption', image),
    Pattern('S-02', 'Text Block', 'site', 'Optional heading and paragraphs', text_block),
    Pattern('S-03', 'Navigation Bar', 'site', 'Brand, links and optional call to action', nav_bar),
    Pattern('S-04', 'Hero', 'site', 'Title, subtitle, actions and optional image', hero),
    Pattern('S-05', 'Feature Grid', 'site', 'Two to four columns of titled cards', feature_grid),
    Pattern('S-06', 'Footer', 'site', 'Brand, links, social links and note', footer),
    Pattern('S-07', 'Contact Form', 'site', 'Labelled name, email, message form with optional Turnstile', contact_form),
    Pattern('S-08', 'Call to Action Band', 'site', 'Title, text and one action', cta_band),
    Pattern('S-09', 'Testimonial', 'site', 'Quote with author and role', testimonial),
    Pattern('S-10', 'FAQ', 'site', 'Questions as native disclosure elements', faq),
]


def register_site_patterns(library: PatternLibrary) -> None:
    """Register S-01 to S-10 and L-07. Idempotent."""
    for pattern in PATTERNS:
        library.register(pattern)
