#!/usr/bin/env python3
"""
Build a multi-page hosted site from a site manifest: every page is generated (react-static
target) through the determinism gate, recorded in the hash-chained ledger, pre-rendered to
plain HTML at its URL path, and checked by the quality gates. One stylesheet serves all pages.

    python scripts/build_pages.py engine/sites/techinnovations.yaml [--preview] [--skip-npm]

Manifest keys: site, tokens, assets (folder copied to /assets), pages: [{path, spec, title,
description}]. Output: build/<site>/<path>/index.html. Tooling only: generation itself stays
pure inside engine/generate.py; this script orchestrates scripts/build_site.py's pieces.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import argparse
import html as html_lib
import os
import re
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, 'engine')
SHELL = os.path.join(ROOT, 'scripts', 'static-shell')
sys.path.insert(0, ENGINE)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

from build_site import link_font_stylesheet, sha256_file  # noqa: E402
from cache import ArtifactCache  # noqa: E402
from gate import run_gate  # noqa: E402
from generate import generate  # noqa: E402
from ledger import Ledger  # noqa: E402
from preview import capture  # noqa: E402
from quality import check_html, CSS_MAX, HTML_MAX  # noqa: E402
from spec_parser import SpecParser  # noqa: E402
from tokens import css_from_tokens, load_tokens  # noqa: E402


def component_name(screen_id):
    return ''.join(w.capitalize() for w in screen_id.split('-'))


def page_dir(out_dir, path):
    return os.path.join(out_dir, *[p for p in path.strip('/').split('/') if p])


def generate_pages(manifest, manifest_dir, gen_dir, ledger):
    """Gate, generate and record every page; write the generated components. Returns [(page, component)]."""
    os.makedirs(gen_dir, exist_ok=True)
    for stale in os.listdir(gen_dir):
        os.remove(os.path.join(gen_dir, stale))
    parser, cache, rows = SpecParser(), ArtifactCache(), []
    for page in manifest['pages']:
        spec_path = os.path.join(manifest_dir, page['spec']) if not os.path.isabs(page['spec']) else page['spec']
        spec = parser.parse(spec_path)
        gate = run_gate(spec, 'react-static', spec_path=spec_path)
        if not gate['ok']:
            sys.exit(f'andon: determinism gate failed for {page["path"]}: {gate["checks"]}')
        artifact = generate(spec, 'react-static')
        cache.put(artifact)
        entry = ledger.append(artifact, spec['screen_id'], spec['version'])
        name = component_name(spec['screen_id'])
        with open(os.path.join(gen_dir, f'{name}.tsx'), 'w', encoding='utf-8') as f:
            f.write(artifact.code)
        print(f'  {page["path"]:40s} {name}.tsx  {artifact.content_hash[:16]}  ledger {entry["sequence"]}')
        rows.append((page, name))
    imports = ''.join(f"import {name} from './{name}';\n" for _, name in rows)
    table = ''.join(f"  {path_literal(p['path'])}: {name},\n" for p, name in rows)
    with open(os.path.join(gen_dir, 'Pages.tsx'), 'w', encoding='utf-8') as f:
        f.write(imports + '\nexport const PAGES: Record<string, () => JSX.Element> = {\n' + table + '};\n')
    with open(os.path.join(gen_dir, 'Page.tsx'), 'w', encoding='utf-8') as f:
        f.write(f"export {{ default }} from './{rows[0][1]}';\n")
    return rows


def path_literal(path):
    return "'" + path.replace("'", "\\'") + "'"


def render_pages(rows, out_dir, shell_index, env):
    """Pre-render each page into <out_dir>/<path>/index.html from the shell's built index.html."""
    ssr_dir = os.path.join(SHELL, '.ssr')
    subprocess.run(['npx', 'vite', 'build', '--ssr', 'src/entry-pages.tsx', '--outDir', ssr_dir],
                   cwd=SHELL, check=True, env=env, stdout=subprocess.DEVNULL)
    for page, _ in rows:
        markup = subprocess.run(
            ['node', '-e', "import('./.ssr/entry-pages.js').then(m => process.stdout.write(m.render(process.argv[1])))",
             page['path']], cwd=SHELL, check=True, capture_output=True, text=True).stdout
        html = shell_index.replace('<div id="root"></div>', '<div id="root">' + markup + '</div>')
        depth = len([p for p in page['path'].strip('/').split('/') if p])
        rel = ('../' * depth or './') + 'assets/'
        html = html.replace('href="/assets/', 'href="' + rel).replace('src="/assets/', 'src="' + rel)   # relative: works on disk and on the host
        html = html.replace('%%TITLE%%', html_lib.escape(page['title'], quote=True))
        html = html.replace('%%DESCRIPTION%%', html_lib.escape(page.get('description', ''), quote=True))
        target = page_dir(out_dir, page['path'])
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    shutil.rmtree(ssr_dir, ignore_errors=True)


def quality(rows, out_dir):
    """Accessibility checks per page, size budgets per page and for the shared stylesheet."""
    ok = True
    css_bytes = sum(os.path.getsize(os.path.join(d, n)) for d, _, fs in os.walk(out_dir) for n in fs if n.endswith('.css'))
    js_bytes = sum(os.path.getsize(os.path.join(d, n)) for d, _, fs in os.walk(out_dir) for n in fs if n.endswith('.js'))
    for page, _ in rows:
        index = os.path.join(page_dir(out_dir, page['path']), 'index.html')
        with open(index, 'r', encoding='utf-8') as f:
            result = check_html(f.read())
        size = os.path.getsize(index)
        failed = [f'{k} ({v[1]})' for k, v in result.get('checks', result).items() if not v[0]]
        if size > HTML_MAX:
            failed.append(f'html_within_budget ({size} of {HTML_MAX} bytes)')
        print(f'  {"PASS" if not failed else "FAIL"}  {page["path"]:40s} {size:6d} bytes' + ('  ' + '; '.join(failed) if failed else ''))
        ok = ok and not failed
    print(f'  {"PASS" if css_bytes <= CSS_MAX else "FAIL"}  stylesheet {css_bytes} of {CSS_MAX} bytes; {js_bytes} bytes of js')
    return ok and css_bytes <= CSS_MAX and js_bytes == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--skip-npm', action='store_true', help='generate only, no shell build')
    ap.add_argument('--preview', action='store_true', help='capture phone and desktop screenshots of the pages marked preview')
    args = ap.parse_args()

    with open(args.manifest, 'r', encoding='utf-8') as f:
        manifest = yaml.safe_load(f)
    manifest_dir = ROOT
    site = manifest['site']
    out_dir = os.path.join(ROOT, 'build', site)
    gen_dir = os.path.join(SHELL, 'src', 'generated')
    ledger = Ledger(os.path.join(ROOT, 'build', 'ledger.jsonl'))

    print(f'site {site}: {len(manifest["pages"])} pages')
    rows = generate_pages(manifest, manifest_dir, gen_dir, ledger)

    tokens = load_tokens(os.path.join(ROOT, manifest['tokens']))
    with open(os.path.join(gen_dir, 'theme.css'), 'w', encoding='utf-8') as f:
        f.write(css_from_tokens(tokens))
    shutil.copyfile(os.path.join(ENGINE, 'site', 'site.css'), os.path.join(gen_dir, 'site.css'))
    public_assets = os.path.join(SHELL, 'public', 'assets')
    shutil.rmtree(public_assets, ignore_errors=True)
    assets = os.path.join(ROOT, manifest.get('assets', ''))
    if manifest.get('assets') and os.path.isdir(assets):
        shutil.copytree(assets, public_assets)
    if args.skip_npm:
        return

    env = dict(os.environ, VITE_SITE_TITLE='%%TITLE%%', VITE_SITE_DESCRIPTION='%%DESCRIPTION%%')
    if not os.path.isdir(os.path.join(SHELL, 'node_modules')):
        subprocess.run(['npm', 'install', '--no-audit', '--no-fund'], cwd=SHELL, check=True)
    shutil.rmtree(out_dir, ignore_errors=True)
    subprocess.run(['npx', 'vite', 'build', '--base', '/', '--outDir', out_dir], cwd=SHELL, check=True, env=env)
    shell_index_path = os.path.join(out_dir, 'index.html')
    with open(shell_index_path, 'r', encoding='utf-8') as f:
        shell_index = f.read()
    shell_index = re.sub(r'\s*<script type="module"[^>]*></script>', '', shell_index).replace(' crossorigin', '')
    for name in os.listdir(os.path.join(out_dir, 'assets')):
        if name.endswith('.js'):
            os.remove(os.path.join(out_dir, 'assets', name))
    render_pages(rows, out_dir, shell_index, env)
    if tokens['font'].get('stylesheet'):
        for page, _ in rows:
            link_font_stylesheet(page_dir(out_dir, page['path']), tokens['font']['stylesheet'])

    ok = quality(rows, out_dir)
    print('quality', 'PASS' if ok else 'FAIL')
    if args.preview:
        for page, _ in rows:
            if page.get('preview'):
                shots = capture(page_dir(out_dir, page['path']))
                for name, png in shots.items():
                    print(f'  preview {page["path"]:30s} {name:8s} {png}')
    if not ok:
        sys.exit(3)
    print(f'built {out_dir}')
    for dirpath, _, files in sorted(os.walk(out_dir)):
        if os.path.basename(dirpath) == 'preview':
            continue
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            print(f'  {sha256_file(path)[:16]}  {os.path.relpath(path, out_dir)}  {os.path.getsize(path)} bytes')


if __name__ == '__main__':
    main()
