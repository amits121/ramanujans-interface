#!/usr/bin/env python3
"""
Build one hosted site from a specification: generate (react-static target),
emit the theme from tokens, copy the base stylesheet, run the static shell build.

    python scripts/build_site.py engine/specs/sample-landing.yaml sample-landing \
        [--tokens engine/tokens/default.yaml] [--title "..."] [--description "..."]

Output: build/<site>/ (static files) and a printed record of the hashes.
Tooling only: generation itself stays pure inside engine/generate.py.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, 'engine')
SHELL = os.path.join(ROOT, 'scripts', 'static-shell')
sys.path.insert(0, ENGINE)

from cache import ArtifactCache  # noqa: E402
from gate import run_gate  # noqa: E402
from generate import generate  # noqa: E402
from preview import capture, compare  # noqa: E402
from quality import check_site  # noqa: E402
from spec_parser import SpecParser  # noqa: E402
from tokens import css_from_tokens, load_tokens  # noqa: E402


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def prerender(out_dir, env):
    """Render the page to static markup, inline it into index.html, drop the script bundle."""
    ssr_dir = os.path.join(SHELL, '.ssr')
    subprocess.run(['npx', 'vite', 'build', '--ssr', 'src/entry-server.tsx', '--outDir', ssr_dir],
                   cwd=SHELL, check=True, env=env, stdout=subprocess.DEVNULL)
    markup = subprocess.run(
        ['node', '-e', "import('./.ssr/entry-server.js').then(m => process.stdout.write(m.render()))"],
        cwd=SHELL, check=True, capture_output=True, text=True).stdout
    index = os.path.join(out_dir, 'index.html')
    with open(index, 'r', encoding='utf-8') as f:
        html = f.read()
    html = re.sub(r'\s*<script type="module"[^>]*></script>', '', html)
    html = html.replace(' crossorigin', '')
    html = html.replace('<div id="root"></div>', '<div id="root">' + markup + '</div>')
    with open(index, 'w', encoding='utf-8') as f:
        f.write(html)
    for name in os.listdir(os.path.join(out_dir, 'assets')):
        if name.endswith('.js'):
            os.remove(os.path.join(out_dir, 'assets', name))
    shutil.rmtree(ssr_dir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('site')
    ap.add_argument('--tokens', default=os.path.join(ENGINE, 'tokens', 'default.yaml'))
    ap.add_argument('--title', default='')
    ap.add_argument('--description', default='')
    ap.add_argument('--skip-npm', action='store_true', help='do not run the shell build, only generate')
    ap.add_argument('--no-prerender', action='store_true', help='keep the client bundle instead of static HTML')
    ap.add_argument('--assets', default='', help='folder of site assets (default engine/specs/assets/<screen_id>)')
    ap.add_argument('--preview', action='store_true', help='capture phone and desktop screenshots after the build')
    ap.add_argument('--baseline', default='', help='directory of baseline screenshots to compare against')
    args = ap.parse_args()

    spec = SpecParser().parse(args.spec)
    gate = run_gate(spec, 'react-static', spec_path=args.spec)
    print('gate', 'PASS' if gate['ok'] else 'FAIL', gate['checks'])
    if not gate['ok']:
        print('andon: determinism gate failed, nothing built')
        sys.exit(2)
    artifact = generate(spec, 'react-static')
    print('cache', ArtifactCache().put(artifact))
    component = ''.join(w.capitalize() for w in spec['screen_id'].split('-'))

    gen_dir = os.path.join(SHELL, 'src', 'generated')
    os.makedirs(gen_dir, exist_ok=True)
    for stale in os.listdir(gen_dir):
        os.remove(os.path.join(gen_dir, stale))
    with open(os.path.join(gen_dir, f'{component}.tsx'), 'w', encoding='utf-8') as f:
        f.write(artifact.code)
    with open(os.path.join(gen_dir, 'Page.tsx'), 'w', encoding='utf-8') as f:
        f.write(f"export {{ default }} from './{component}';\n")
    with open(os.path.join(gen_dir, 'theme.css'), 'w', encoding='utf-8') as f:
        f.write(css_from_tokens(load_tokens(args.tokens)))
    shutil.copyfile(os.path.join(ENGINE, 'site', 'site.css'), os.path.join(gen_dir, 'site.css'))

    public_assets = os.path.join(SHELL, 'public', 'assets')
    shutil.rmtree(public_assets, ignore_errors=True)
    assets = args.assets or os.path.join(ENGINE, 'specs', 'assets', spec['screen_id'])
    if os.path.isdir(assets):
        shutil.copytree(assets, public_assets)
        print(f'assets {assets} -> public/assets')

    print(f'generated {component}.tsx  content_hash={artifact.content_hash}')
    print(f'spec_key={artifact.spec_key}  pattern_library={artifact.pattern_lib_version}')
    if args.skip_npm:
        return

    env = dict(os.environ, VITE_SITE_TITLE=args.title or spec['screen_id'],
               VITE_SITE_DESCRIPTION=args.description)
    if not os.path.isdir(os.path.join(SHELL, 'node_modules')):
        subprocess.run(['npm', 'install', '--no-audit', '--no-fund'], cwd=SHELL, check=True)
    out_dir = os.path.join(ROOT, 'build', args.site)
    subprocess.run(['npx', 'vite', 'build', '--outDir', out_dir], cwd=SHELL, check=True, env=env)
    if not args.no_prerender:
        prerender(out_dir, env)

    quality = check_site(out_dir)
    for name, (ok, detail) in quality['checks'].items():
        print(f'  {"PASS" if ok else "FAIL"}  {name:24s} {detail}')
    print('quality', 'PASS' if quality['ok'] else 'FAIL')
    if args.preview:
        shots = capture(out_dir)
        for name, ratio in compare(shots, args.baseline or None).items():
            print(f'  preview {name:8s} {shots[name]}' + ('' if ratio is None else f'  {ratio * 100:.3f}% changed'))
    if not quality['ok']:
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
