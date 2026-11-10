#!/usr/bin/env python3
"""
Publication Patterns (S-12 to S-16)

The patterns a multi-page publication site adds to the marketing set: a data table with a
row-header column, a citation list, a cascading menu built on native disclosure elements
(no script), a footer that doubles as the site map, and a page header with a standfirst and
labelled meta lines. Plain JSX, styled by site/site.css.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

from typing import Any, Dict, List

from pattern_library import Pattern
from site_text import BUTTON, _heading, _link, _req, _rich, _t

PUBLICATION_TYPE_MAPPING = {
    'data-table': 'S-12',
    'citations': 'S-13',
    'site-menu': 'S-14',
    'footer-sitemap': 'S-15',
    'page-header': 'S-16',
}


def data_table(p: Dict) -> str:
    _req(p, 'S-12', 'columns', 'rows')
    width = len(p['columns'])
    cap = f'<figcaption>{_rich(p["caption"])}</figcaption>' if p.get('caption') else ''
    head = ''.join(f'<th scope="col">{_rich(c)}</th>' for c in p['columns'])
    body = []
    for n, row in enumerate(p['rows']):
        if len(row) != width:
            raise ValueError(f'S-12 row {n + 1} has {len(row)} cells, the table has {width} columns')
        cells = ''.join(f'<td>{_rich(c)}</td>' for c in row[1:])
        body.append(f'<tr><th scope="row">{_rich(row[0])}</th>{cells}</tr>')
    note = f'<p className="site-table-note">{_rich(p["note"])}</p>' if p.get('note') else ''
    return (f'<figure className="site-table">{cap}<div className="site-table-scroll"><table><thead><tr>{head}</tr>'
            f'</thead><tbody>{"".join(body)}</tbody></table></div>{note}</figure>')


def citations(p: Dict) -> str:
    _req(p, 'S-13', 'heading', 'items')
    items = ''.join(f'<li>{_rich(i)}</li>' for i in p['items'])
    return f'<section className="site-citations">{_heading(p.get("level", 2), p["heading"])}<ol>{items}</ol></section>'


def _menu_items(items: List[Dict], pattern_id: str) -> str:
    out = []
    for item in items:
        children = item.get('children') or []
        if not children and not item.get('href'):
            raise ValueError(f'{pattern_id} menu item {item.get("label")!r} needs a link or children')
        if not children:
            out.append(f'<li>{_link(item)}</li>')
            continue
        own = ([{'label': item.get('page_label', item['label']), 'href': item['href']}] if item.get('href') else [])
        out.append(f'<li><details className="site-menu-group"><summary>{_t(item["label"])}</summary>'
                   f'<ul className="site-menu-sub">{_menu_items(own + children, pattern_id)}</ul></details></li>')
    return ''.join(out)


def site_menu(p: Dict) -> str:
    _req(p, 'S-14', 'brand', 'items')
    b = p['brand']
    logo = (f'<img className="site-menu-logo" src={_t(b["logo"]["src"])} alt={_t(b["logo"]["alt"])} />'
            if b.get('logo') else '')
    if not b.get('label') and not (b.get('logo') and b['logo'].get('alt')):
        raise ValueError('S-14 brand needs a label, or a logo with alt text')
    label = _t(b['label']) if b.get('label') else ''
    brand = f'<a className="site-menu-brand" href={_t(b.get("href", "/"))}>{logo}{label}</a>'
    cta = _link(p['cta'], BUTTON) if p.get('cta') else ''
    return (f'<nav className="site-menu" aria-label="Main">{brand}'
            f'<ul className="site-menu-list">{_menu_items(p["items"], "S-14")}</ul>{cta}</nav>')


def footer_sitemap(p: Dict) -> str:
    _req(p, 'S-15', 'columns', 'note')
    cols = []
    for c in p['columns']:
        links = ''.join(f'<li>{_link(l)}</li>' for l in c['links'])
        cols.append(f'<nav className="site-footer-column" aria-label={_t(c["heading"])}>'
                    f'{_heading(2, c["heading"])}<ul>{links}</ul></nav>')
    brand = f'<div className="site-footer-brand">{_t(p["brand"])}</div>' if p.get('brand') else ''
    return (f'<footer className="site-footer site-footer-map">{brand}<div className="site-footer-columns">'
            f'{"".join(cols)}</div><p className="site-footer-note">{_rich(p["note"])}</p></footer>')


def page_header(p: Dict) -> str:
    _req(p, 'S-16', 'title')
    stand = f'<p className="site-standfirst">{_rich(p["standfirst"])}</p>' if p.get('standfirst') else ''
    meta = ''
    if p.get('meta'):
        rows = ''.join(f'<div><dt>{_t(m["label"])}</dt><dd>{_rich(m["text"])}</dd></div>' for m in p['meta'])
        meta = f'<dl className="site-page-meta">{rows}</dl>'
    return f'<header className="site-page-header">{_heading(1, p["title"])}{stand}{meta}</header>'


PATTERNS: List[Pattern] = [
    Pattern('S-12', 'Data Table', 'site', 'Caption, header row, row-header column, optional note', data_table),
    Pattern('S-13', 'Citations', 'site', 'Heading and an ordered list of sources', citations),
    Pattern('S-14', 'Site Menu', 'site', 'Brand and cascading menu on native disclosure elements', site_menu),
    Pattern('S-15', 'Footer Site Map', 'site', 'Link columns mirroring the menu, brand and legal note', footer_sitemap),
    Pattern('S-16', 'Page Header', 'site', 'Title, standfirst and labelled meta lines', page_header),
]
