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

from generate import generate  # noqa: E402
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
    args = ap.parse_args()

    spec = SpecParser().parse(args.spec)
    artifact = generate(spec, 'react-static')
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

    print(f'built {out_dir}')
    for dirpath, _, files in sorted(os.walk(out_dir)):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            print(f'  {sha256_file(path)[:16]}  {os.path.relpath(path, out_dir)}  {os.path.getsize(path)} bytes')


if __name__ == '__main__':
    main()
