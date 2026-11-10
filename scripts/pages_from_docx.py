#!/usr/bin/env python3
"""
Turn the founder's page documents (Word) into page specifications and a site manifest, word for word.

    python scripts/pages_from_docx.py <content folder> engine/specs/techinnovations engine/sites/techinnovations.yaml

Document format (one Word file per page, plain paragraphs): first line "<site> page document: <title>",
then "url path:", "target audience:", "primary technical thesis:", "primary authentic research source:";
after that, a heading is a line without closing punctuation, paragraphs follow it, a table takes the
heading before it as its caption, and the heading "authentic research sources and citations" starts the
citation list. Bold runs in Word become emphasis. The casing pass applies sentence case and the proper
nouns of casing.yaml; the emphasis rules bold enumerated lead-ins and the "ten-year milestone:" label.
The menu and footer come from menu.yaml, limited to the pages that have a document.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import yaml

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
META_KEYS = {'url path': 'path', 'target audience': 'audience',
             'primary technical thesis': 'thesis', 'primary authentic research source': 'source',
             'hero headline': 'hero_title', 'hero line': 'hero_kicker', 'hero actions': 'hero_actions',
             'image': 'image'}
# "hero headline:" turns the page header into a hero (S-04): the headline as the title, "hero line:" as the kicker above it,
# the thesis as the subtitle and "hero actions: <label> -> <path>; <label> -> <path>" as up to two buttons.
# "image: <file> | <alt text> | <caption>" places the file from the assets folder under the header, or inside the hero.
# A body paragraph "contact form: <action url>" places the contact form (S-07) at that point, headed by the heading before it.
CITATIONS_HEADING = 'authentic research sources and citations'
ORDINALS = ('first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth')
LEAD_WORDS = ('vector', 'sector', 'layer', 'stream', 'branch', 'phase', 'step')
NUMBER_WORDS = ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                'eleven', 'twelve', 'thirteen', 'fourteen')


# ---- reading Word -------------------------------------------------------------------------------

def read_docx(path):
    """Yield ('p', text with **bold** runs) and ('table', rows) in document order; no dependency beyond the library."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
    body = root.find(W + 'body')
    for child in body:
        if child.tag == W + 'p':
            text = paragraph_text(child)
            if text.strip():
                yield 'p', text.strip()
        elif child.tag == W + 'tbl':
            rows = []
            for tr in child.iter(W + 'tr'):
                rows.append([' '.join(paragraph_text(p).strip() for p in tc.iter(W + 'p')).strip()
                             for tc in tr.findall(W + 'tc')])
            yield 'table', rows


def paragraph_text(p):
    parts = []
    for r in p.iter(W + 'r'):
        text = ''.join(t.text or '' for t in r.iter(W + 't'))
        if not text:
            continue
        rpr = r.find(W + 'rPr')
        bold = rpr is not None and rpr.find(W + 'b') is not None and rpr.find(W + 'b').get(W + 'val') not in ('0', 'false')
        parts.append((text, bold))
    out, open_bold = [], False
    for text, bold in parts:
        if bold != open_bold:
            out.append('**')
            open_bold = bold
        out.append(text)
    if open_bold:
        out.append('**')
    return ''.join(out).replace('** **', ' ')


# ---- casing and emphasis ------------------------------------------------------------------------

class Caser:
    def __init__(self, phrases):
        self.rules = [(re.compile(r'(?<![\w-])' + re.escape(k) + r'(?![\w-])'), v)
                      for k, v in sorted(phrases.items(), key=lambda kv: -len(kv[0]))]

    def __call__(self, text):
        for pattern, cased in self.rules:
            text = pattern.sub(cased, text)
        return sentence_case(text)


DOMAIN = re.compile(r'^[a-z0-9-]+\.[a-z]{2,}')


def sentence_case(text):
    out, up = [], True
    for i, ch in enumerate(text):
        if up and ch.isalpha():
            if DOMAIN.match(text[i:].split(' ', 1)[0]):     # a domain name keeps its case
                up = False
            else:
                ch, up = ch.upper(), False
        elif ch in '.!?' and (i + 1 == len(text) or text[i + 1] == ' '):
            up = True
        elif up and ch not in ' *"\'(':
            up = False
        out.append(ch)
    return ''.join(out)


def emphasise(text):
    low = text.lower()
    m = re.match(r'^(' + '|'.join(ORDINALS) + r'),\s', low)
    if m:
        colon = text.find(':')
        end = colon + 1 if 0 < colon <= 60 else len(m.group(1))
        return '**' + text[:end] + '**' + text[end:]
    m = re.match(r'^(' + '|'.join(LEAD_WORDS) + r') (' + '|'.join(NUMBER_WORDS) + r')\b', low)
    if m:
        return '**' + text[:m.end()] + '**' + text[m.end():]
    if low.startswith('ten-year milestone:'):
        n = len('ten-year milestone:')
        return '**' + text[:n] + '**' + text[n:]
    return text


def is_heading(text):
    return len(text) <= 120 and not text.rstrip('*').endswith(('.', '!', '?', ';'))


# ---- one page -----------------------------------------------------------------------------------

def parse_page(path, case):
    blocks = list(read_docx(path))
    kind, first = blocks[0]
    if kind != 'p' or 'page document:' not in first:
        sys.exit(f'{path}: the first line must read "<site> page document: <title>"')
    page = {'title': case(first.split('page document:', 1)[1].strip()), 'meta': {}, 'sections': [], 'citations': []}
    i = 1
    while i < len(blocks) and blocks[i][0] == 'p' and ':' in blocks[i][1]:
        key, value = blocks[i][1].split(':', 1)
        if key.strip().lower() not in META_KEYS:
            break
        page['meta'][META_KEYS[key.strip().lower()]] = value.strip()
        i += 1
    if 'path' not in page['meta']:
        sys.exit(f'{path}: no "url path:" line')
    current, pending_heading, in_citations = None, None, False
    for kind, item in blocks[i:]:
        if kind == 'table':
            page['sections'].append({'table': {'caption': case(pending_heading) if pending_heading else '',
                                               'columns': [case(c) for c in item[0]],
                                               'rows': [[case(c) for c in row] for row in item[1:]]}})
            pending_heading, current, in_citations = None, None, False
            continue
        if in_citations and not (is_heading(item) and item.lower() != CITATIONS_HEADING and len(page['citations']) == 0):
            page['citations'].append(case(item))
            continue
        if item.lower() == CITATIONS_HEADING:
            in_citations, pending_heading, current = True, None, None
            continue
        if item.lower().startswith('contact form:'):      # "contact form: <action>" places the form here
            page['sections'].append({'form': {'action': item.split(':', 1)[1].strip(),
                                              'heading': case(pending_heading) if pending_heading else ''}})
            pending_heading, current = None, None
            continue
        if is_heading(item):
            if pending_heading:                       # two headings in a row: the first stands alone
                page['sections'].append({'heading': case(pending_heading), 'paragraphs': []})
            pending_heading, current = item, None
            continue
        if current is None:
            current = {'heading': case(pending_heading) if pending_heading else '', 'paragraphs': []}
            page['sections'].append(current)
            pending_heading = None
        current['paragraphs'].append(emphasise(case(item)))
    if pending_heading:
        page['sections'].append({'heading': case(pending_heading), 'paragraphs': []})
    return page


def slug(path):
    return 'home' if path == '/' else re.sub(r'[^a-z0-9]+', '-', path.strip('/').lower()).strip('-')


def image_props(value, case):
    parts = [x.strip() for x in value.split('|')]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        sys.exit(f'image line needs "<file> | <alt text>", got: {value}')
    props = {'src': '/assets/' + parts[0], 'alt': case(parts[1])}
    if len(parts) > 2 and parts[2]:
        props['caption'] = case(parts[2])
    return props


def hero_props(page, case):
    meta = page['meta']
    props = {'title': case(meta['hero_title'])}
    if meta.get('hero_kicker'):
        props['kicker'] = case(meta['hero_kicker'])
    if meta.get('thesis'):
        props['subtitle'] = case(meta['thesis'])
    actions = [a for a in (x.strip() for x in meta.get('hero_actions', '').split(';')) if a]
    for key, action in zip(('primary_cta', 'secondary_cta'), actions):
        if '->' not in action:
            sys.exit(f'hero action needs "<label> -> <path>", got: {action}')
        label, href = (x.strip() for x in action.split('->', 1))
        props[key] = {'label': case(label), 'href': href}
    if meta.get('image'):
        img = image_props(meta['image'], case)
        props['image'] = {'src': img['src'], 'alt': img['alt']}
    return props


def spec_for(page, menu_props, footer_props, case):
    meta = page['meta']
    components = [{'id': 'menu', 'type': 'site-menu', 'props': menu_props}]
    if meta.get('hero_title'):
        components.append({'id': 'hero', 'type': 'hero', 'props': hero_props(page, case)})
    else:
        # the audience and source lines are the founder's internal notes (ruling 2026-11-10); they never reach the page
        components.append({'id': 'header', 'type': 'page-header', 'props': {
            'title': page['title'],
            'standfirst': case(meta['thesis']) if meta.get('thesis') else '',
            'meta': []}})
        if meta.get('image'):
            components.append({'id': 'image', 'type': 'image', 'props': image_props(meta['image'], case)})
    n = 0
    for section in page['sections']:
        n += 1
        if 'table' in section:
            components.append({'id': f'table-{n}', 'type': 'data-table', 'props': section['table']})
        elif 'form' in section:
            props = {'action': section['form']['action']}
            if section['form']['heading']:
                props['heading'] = section['form']['heading']
            components.append({'id': f'form-{n}', 'type': 'contact-form', 'props': props})
        elif section['paragraphs'] or section['heading']:
            props = {'paragraphs': section['paragraphs'] or ['']}
            if section['heading']:
                props['heading'] = section['heading']
                props['level'] = 2
            if not section['paragraphs']:
                props['paragraphs'] = []
            components.append({'id': f'section-{n}', 'type': 'text-block', 'props': props})
    if page['citations']:
        components.append({'id': 'citations', 'type': 'citations',
                           'props': {'heading': case(CITATIONS_HEADING), 'items': page['citations']}})
    components.append({'id': 'footer', 'type': 'footer-sitemap', 'props': footer_props})
    for c in components:                                       # a heading with no paragraphs renders as a heading only
        if c['type'] == 'text-block' and not c['props']['paragraphs']:
            c['props']['paragraphs'] = [c['props'].pop('heading')]
            c['props']['level'] = 2
            c['props']['heading'] = c['props']['paragraphs'].pop()
            c['props']['paragraphs'] = [' ']
    return {'screen_id': slug(meta['path']), 'version': '1.0', 'layout': 'page', 'components': components,
            'accessibility': {'focusOrder': [c['id'] for c in components], 'ariaLabels': True, 'keyboardNav': True}}


# ---- menu and footer ----------------------------------------------------------------------------

def prune(items, existing):
    out = []
    for item in items:
        kids = prune(item.get('children') or [], existing)
        own = item.get('href') in existing
        if not own and not kids:
            continue
        node = {'label': item['label']}
        if own:
            node['href'] = item['href']
            if item.get('page_label'):
                node['page_label'] = item['page_label']
        if kids:
            node['children'] = kids
        out.append(node)
    return out


def flatten(items):
    for item in items:
        if item.get('href'):
            yield {'label': item.get('page_label', item['label']), 'href': item['href']}
        yield from flatten(item.get('children') or [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('content_dir')
    ap.add_argument('spec_dir')
    ap.add_argument('manifest')
    ap.add_argument('--site', default='techinnovations')
    ap.add_argument('--tokens', default='engine/tokens/techinnovations.yaml')
    ap.add_argument('--assets', default='engine/specs/assets/techinnovations')
    ap.add_argument('--preview', default='/', help='comma separated paths to capture in previews')
    args = ap.parse_args()

    with open(os.path.join(args.spec_dir, 'casing.yaml'), encoding='utf-8') as f:
        case = Caser(yaml.safe_load(f))
    with open(os.path.join(args.spec_dir, 'menu.yaml'), encoding='utf-8') as f:
        menu = yaml.safe_load(f)

    docs = sorted(os.path.join(d, n) for d, _, fs in os.walk(args.content_dir) for n in fs
                  if n.endswith('.docx') and not n.startswith('~$') and 'site tree' not in n.lower().replace('_', ' '))
    pages = []
    for path in docs:                                   # only page documents; other Word files in the folder are left alone
        kind, first = next(read_docx(path), ('p', ''))
        if kind != 'p' or 'page document:' not in first:
            print(f'skipped (not a page document): {os.path.relpath(path, args.content_dir)}')
            continue
        pages.append(parse_page(path, case))
    existing = {p['meta']['path'] for p in pages}
    if len(existing) != len(pages):
        sys.exit('two documents share one url path')
    items = prune(menu['items'], existing)
    menu_props = {'brand': menu['brand'], 'items': items}
    columns = [{'heading': item['label'], 'links': list(flatten([item]))} for item in items if item['label'] != 'Home']
    footer_props = {'brand': menu['brand']['label'], 'columns': columns, 'note': menu['footer_note']}

    os.makedirs(args.spec_dir, exist_ok=True)
    manifest = {'site': args.site, 'tokens': args.tokens, 'assets': args.assets, 'pages': []}
    previews = set(args.preview.split(','))
    for page in sorted(pages, key=lambda p: p['meta']['path']):
        spec = spec_for(page, menu_props, footer_props, case)
        rel = os.path.join(args.spec_dir, spec['screen_id'] + '.yaml')
        with open(rel, 'w', encoding='utf-8') as f:
            f.write(f'# Generated by scripts/pages_from_docx.py from the founder\'s page document; edit the document, not this file.\n')
            yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=120)
        entry = {'path': page['meta']['path'], 'spec': rel, 'title': page['title'],
                 'description': case(page['meta'].get('thesis', ''))}
        if page['meta']['path'] in previews:
            entry['preview'] = True
        manifest['pages'].append(entry)
        print(f'  {page["meta"]["path"]:36s} {len(page["sections"]):2d} blocks  {len(page["citations"])} citations  -> {rel}')
    with open(args.manifest, 'w', encoding='utf-8') as f:
        f.write('# Generated by scripts/pages_from_docx.py; the page list follows the content folder.\n')
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True, width=120)
    print(f'{len(pages)} pages, {sum(1 for _ in flatten(items))} menu links -> {args.manifest}')


if __name__ == '__main__':
    main()
