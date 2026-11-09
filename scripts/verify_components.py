#!/usr/bin/env python3
"""
Monthly component verification: are the proven components still exported, still supported,
and still the ones production uses? Compares the installed packages of the given source trees
(and, with --latest, the registry's latest versions) with the catalogs in libs/catalog and the
proven registers in libs/proven, scans the trees for real imports, writes a dated report and
stamps the registers. Exit 5 when a proven component is missing or deprecated.

    python scripts/verify_components.py --tree <app> [--tree <app> ...] [--latest] [--no-scan]
                                        [--report-dir libs/proven/reports]

Tooling only: nothing here touches the engine or generates code.
Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Set

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROVEN = os.path.join(ROOT, 'libs', 'proven')
CATALOG = os.path.join(ROOT, 'libs', 'catalog')
SKIP_DIRS = {'node_modules', 'build', 'dist', '.expo', 'android', 'ios', '.git'}
IMPORT = re.compile(r"import\s+(?:type\s+)?(\{[^}]*\}|[\w$]+(?:\s*,\s*\{[^}]*\})?|\*\s+as\s+[\w$]+)\s+from\s+['\"]([^'\"]+)['\"]", re.S)
DEPRECATED = re.compile(r'@deprecated[^*]*\*/\s*(?:export\s+)?(?:declare\s+)?(?:const|function|interface|type|class|let|var)?\s*([A-Za-z_$][\w$]*)')


def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_yaml(path, data):
    """Rewrite a register, keeping its leading comment block."""
    header = ''
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            header = ''.join(line for line in f.read().splitlines(True) if line.startswith('#'))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=120)


DECLARED = re.compile(r'\b(?:class|interface|type|const|function|let|var|enum|namespace)\s+([A-Za-z_$][\w$]*)')


def declared_names(tree: str, package: str) -> Set[str]:
    """Names declared in a package's type declarations: the fallback when it cannot load in plain Node."""
    names: Set[str] = set()
    for path in glob.glob(os.path.join(tree, 'node_modules', package, '**', '*.d.ts'), recursive=True):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                names.update(DECLARED.findall(f.read()))
        except OSError:
            continue
    return names


def installed_version(tree: str, package: str):
    path = os.path.join(tree, 'node_modules', package, 'package.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f).get('version')


def latest_version(package: str):
    try:
        return subprocess.run(['npm', 'view', package, 'version'], capture_output=True, text=True, timeout=60,
                              check=True).stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def runtime_exports(tree: str, module: str):
    """Names the installed module exports at runtime (Node). None when it cannot be loaded."""
    script = 'const m = require(process.argv[1]); process.stdout.write(JSON.stringify(Object.keys(m)));'
    result = subprocess.run(['node', '-e', script, module], cwd=tree, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return None
    return set(json.loads(result.stdout or '[]'))


def resolves(tree: str, module: str) -> bool:
    result = subprocess.run(['node', '-e', 'require.resolve(process.argv[1])', module], cwd=tree, capture_output=True, timeout=60)
    return result.returncode == 0


def deprecated_names(tree: str, packages: List[str]) -> Set[str]:
    names: Set[str] = set()
    paths = []
    for package in packages:
        paths += glob.glob(os.path.join(tree, 'node_modules', package, '**', '*.d.ts'), recursive=True)
    for path in paths:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                names.update(DEPRECATED.findall(f.read()))
        except OSError:
            continue
    return names


def scan_imports(tree: str, prefixes: List[str]) -> Dict[str, Dict[str, int]]:
    """{module: {name: files}} for every import whose module starts with one of the prefixes."""
    found: Dict[str, Dict[str, int]] = {}
    for dirpath, dirnames, filenames in os.walk(tree):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(('.js', '.jsx', '.ts', '.tsx')):
                continue
            try:
                with open(os.path.join(dirpath, name), 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except OSError:
                continue
            seen: Set[tuple] = set()
            for match in IMPORT.finditer(text):
                module = match.group(2)
                if not module.startswith(tuple(prefixes)):
                    continue
                inner = re.search(r'\{([^}]*)\}', match.group(1))
                parts = [re.sub(r'\s+', ' ', n).strip().split(' as ')[0].strip() for n in inner.group(1).split(',')] if inner else []
                head = match.group(1).strip()
                if head.startswith('*'):
                    parts.append('namespace:' + head.split('as')[-1].strip())
                elif not head.startswith('{'):
                    parts.append('default:' + re.match(r'^[\w$]+', head).group(0))
                for part in parts:
                    if part and (module, part) not in seen:
                        seen.add((module, part))
                        found.setdefault(module, {}).setdefault(part, 0)
                        found[module][part] += 1
    return found


def check_register(register: Dict[str, Any], trees: List[str], do_scan: bool, do_latest: bool, today: str) -> Dict[str, Any]:
    report: Dict[str, Any] = {'register': register['register'], 'versions': {}, 'latest': {}, 'exports': {}, 'catalog': {},
                              'proven_failures': [], 'new_usage': [], 'unused': [], 'type_deprecations': {}}
    by_name = {c['name']: c for c in register['components']}
    for tree in trees:
        for pkg in register['packages']:
            version = installed_version(tree, pkg['name'])
            if version:
                report['versions'].setdefault(os.path.basename(tree), {})[pkg['name']] = version
    if do_latest:
        for pkg in register['packages']:
            report['latest'][pkg['name']] = latest_version(pkg['name'])
    # exports and deprecations, per enumerable package; the catalog may list a package's API under
    # sub-path sources (firebase/auth), each enumerated on its own
    for pkg in register['packages']:
        if not pkg.get('enumerate', True):
            continue
        tree = next((t for t in trees if installed_version(t, pkg['name'])), None)
        if not tree:
            report['exports'][pkg['name']] = {'checked': False}
            continue
        catalog = read_yaml(os.path.join(CATALOG, pkg['catalog'] + '.yaml')) if pkg.get('catalog') else {'entries': []}
        entries = [e for e in catalog['entries'] if e['source'] == pkg['name'] or e['source'].startswith(pkg['name'] + '/')]
        sources = sorted({e['source'] for e in entries} | {pkg['name']} | {c['module'] for c in register['components'] if c['package'] == pkg['name']})
        exports_by_source = {src: runtime_exports(tree, src) for src in sources}
        typed_sources = [src for src, x in exports_by_source.items() if x is None]
        for src in typed_sources:                       # not loadable in plain Node (needs a browser): use the declarations
            exports_by_source[src] = declared_names(tree, src.split('/')[0] if not src.startswith('@') else '/'.join(src.split('/')[:2])) or None
        all_exports = set().union(*(x for x in exports_by_source.values() if x))
        runtime_only = set().union(*(x for src, x in exports_by_source.items() if x and src not in typed_sources))
        deprecated = deprecated_names(tree, pkg.get('types_packages', [pkg['name']]))
        checked = any(x is not None for x in exports_by_source.values())
        report['type_deprecations'][pkg['name']] = len(deprecated - runtime_only)
        row = {'checked': checked, 'tree': os.path.basename(tree), 'count': len(runtime_only),
               'sources': {src: ((f'{len(x)} declared' if src in typed_sources else len(x)) if x is not None else 'not loadable')
                           for src, x in exports_by_source.items()},
               'deprecated_runtime': sorted(deprecated & runtime_only)}
        if checked:
            missing = []
            for e in entries:
                if e['kind'] == 'module':
                    present = resolves(tree, f'{e["source"]}/{e["name"]}')
                else:
                    exports = exports_by_source.get(e['source'])
                    present = (e['name'] in exports) if exports is not None else resolves(tree, f'{e["source"]}/{e["name"]}')
                if not present:
                    missing.append(e['id'])
            known = {e['name'] for e in entries}
            row['catalog_missing'] = missing
            row['not_in_catalog'] = sorted(n for n in runtime_only if n not in known and n[0].isupper())
            for comp in register['components']:
                if comp['package'] == pkg['name']:
                    exports = exports_by_source.get(comp.get('module', pkg['name']))
                    comp['export_present'] = (comp['name'] in exports) if exports is not None else None
                    comp['deprecated'] = comp['name'] in deprecated
                    if comp.get('status') == 'proven' and (comp['export_present'] is False or comp['deprecated']):
                        report['proven_failures'].append(f'{pkg["name"]} {comp["name"]}: '
                                                         + ('deprecated' if comp['deprecated'] else 'no longer exported'))
        report['exports'][pkg['name']] = row
    # real usage
    if do_scan:
        apps = {a['tree']: a['label'] for a in register.get('applications', [])}
        totals: Dict[tuple, int] = {}
        for tree in trees:
            if os.path.basename(tree) not in apps:
                continue
            for module, names in scan_imports(tree, register['scan_prefixes']).items():
                for name, files in names.items():
                    totals[(module, name)] = totals.get((module, name), 0) + files
        for (module, name), files in sorted(totals.items()):
            base = module.split('/')[0] if not module.startswith('@') else '/'.join(module.split('/')[:2])
            comp = by_name.get(name)
            if comp is None:
                register['components'].append({'name': name, 'package': base, 'module': module, 'pattern': 'none yet',
                                               'files': files, 'status': 'proven', 'since': today})
                report['new_usage'].append(f'{module} {name} ({files} files)')
            else:
                comp['files'] = files
        for comp in register['components']:
            if (comp.get('module', comp['package']), comp['name']) not in totals and comp.get('status') == 'proven' and totals:
                report['unused'].append(f'{comp["package"]} {comp["name"]}')
    register['last_verified'] = today
    register['versions'] = {'installed': report['versions'], 'latest': report['latest']}
    return report


def write_report(reports: List[Dict[str, Any]], path: str, today: str, trees: List[str]) -> None:
    lines = [f'# Components report {today}', '', f'Trees: {", ".join(os.path.basename(t) for t in trees)}', '']
    for r in reports:
        lines += [f'## {r["register"]}', '']
        for tree, pkgs in r['versions'].items():
            lines.append(f'- installed in {tree}: ' + ', '.join(f'{p} {v}' for p, v in pkgs.items()))
        if r['latest']:
            lines.append('- latest published: ' + ', '.join(f'{p} {v or "unknown"}' for p, v in r['latest'].items()))
        for pkg, row in r['exports'].items():
            if not row.get('checked'):
                lines.append(f'- {pkg}: exports not checked (not installed in any tree, or not loadable)')
                continue
            per_source = ', '.join(f'{src} {n}' for src, n in row['sources'].items())
            lines.append(f'- {pkg} ({row["tree"]}): {row["count"]} runtime exports ({per_source}); runtime deprecations: '
                         f'{", ".join(row["deprecated_runtime"]) or "none"}; type-only deprecations: {r["type_deprecations"].get(pkg, 0)}')
            lines.append(f'  - catalogued but no longer exported: {", ".join(row.get("catalog_missing", [])) or "none"}')
            lines.append(f'  - exported but not catalogued: {", ".join(row.get("not_in_catalog", [])) or "none"}')
        lines.append(f'- proven failures: {"; ".join(r["proven_failures"]) or "none"}')
        lines.append(f'- new usage added to the register: {"; ".join(r["new_usage"]) or "none"}')
        lines.append(f'- proven but no longer imported: {"; ".join(r["unused"]) or "none"}')
        lines.append('')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', action='append', default=[], help='a source tree with node_modules (repeatable)')
    ap.add_argument('--latest', action='store_true', help='ask the registry for the latest versions (network)')
    ap.add_argument('--no-scan', action='store_true', help='skip the import scan of the trees')
    ap.add_argument('--report-dir', default=os.path.join(PROVEN, 'reports'))
    args = ap.parse_args()
    trees = [os.path.abspath(t) for t in args.tree]
    today = datetime.date.today().isoformat()
    reports = []
    for path in sorted(glob.glob(os.path.join(PROVEN, '*.yaml'))):
        register = read_yaml(path)
        reports.append(check_register(register, trees, not args.no_scan, args.latest, today))
        write_yaml(path, register)
    os.makedirs(args.report_dir, exist_ok=True)
    out = os.path.join(args.report_dir, today[:7] + '.md')
    write_report(reports, out, today, trees)
    with open(out, 'r', encoding='utf-8') as f:
        print(f.read())
    failures = [f for r in reports for f in r['proven_failures']]
    print('COMPONENTS FAIL: ' + '; '.join(failures) if failures else 'COMPONENTS OK')
    return 5 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
