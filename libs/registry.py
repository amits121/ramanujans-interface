#!/usr/bin/env python3
"""
Registry: catalogs and pattern packs.

    catalogs()                    -> {name: catalog dict}            (validated)
    taxonomy()                    -> the taxonomy dict
    load_pack(name)               -> the pack module (PATTERNS, TYPE_MAPPING, SAMPLES, register)
    register_packs(library, names) -> merged TYPE_MAPPING after registering each pack
    stats()                       -> counts per catalog (entries, core, generated)

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.
"""

import importlib
import os
import sys
from typing import Any, Dict, List

import yaml

LIBS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LIBS)
CATALOG_DIR = os.path.join(LIBS, 'catalog')
PACK_NAMES = ('amplify', 'next', 'material', 'firebase', 'mobile')

REQUIRED_KEYS = ('id', 'name', 'source', 'version', 'kind', 'category', 'tier', 'status')
TIERS = ('core', 'extended')
STATUSES = ('generated', 'catalogued')

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def taxonomy() -> Dict[str, Any]:
    with open(os.path.join(LIBS, 'taxonomy.yaml'), 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _validate(catalog: Dict[str, Any], categories: Dict[str, Any]) -> None:
    seen = set()
    for entry in catalog['entries']:
        for key in REQUIRED_KEYS:
            if key not in entry:
                raise ValueError(f'{catalog["catalog"]}: entry {entry.get("id")} missing "{key}"')
        if entry['id'] in seen:
            raise ValueError(f'{catalog["catalog"]}: duplicate id {entry["id"]}')
        seen.add(entry['id'])
        if entry['category'] not in categories:
            raise ValueError(f'{catalog["catalog"]}: {entry["id"]} has unknown category {entry["category"]}')
        if entry['tier'] not in TIERS or entry['status'] not in STATUSES:
            raise ValueError(f'{catalog["catalog"]}: {entry["id"]} has a bad tier or status')
        if entry['status'] == 'generated' and not entry.get('pattern'):
            raise ValueError(f'{catalog["catalog"]}: {entry["id"]} is generated but names no pattern')


def catalogs() -> Dict[str, Dict[str, Any]]:
    categories = taxonomy()['categories']
    out = {}
    for name in sorted(os.listdir(CATALOG_DIR)):
        if not name.endswith('.yaml'):
            continue
        with open(os.path.join(CATALOG_DIR, name), 'r', encoding='utf-8') as f:
            catalog = yaml.safe_load(f)
        _validate(catalog, categories)
        out[catalog['catalog']] = catalog
    return out


def load_pack(name: str):
    if name not in PACK_NAMES:
        raise KeyError(f'unknown pack: {name}')
    return importlib.import_module(f'libs.packs.{name}.patterns')


def register_packs(library, names: List[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for name in names:
        pack = load_pack(name)
        pack.register(library)
        mapping.update(pack.TYPE_MAPPING)
    return mapping


def pattern_ids() -> Dict[str, str]:
    """Every registered pattern id across all packs -> pack name."""
    out: Dict[str, str] = {}
    for name in PACK_NAMES:
        for pattern in load_pack(name).PATTERNS:
            out[pattern.pattern_id] = name
    return out


def stats() -> Dict[str, Dict[str, int]]:
    out = {}
    for name, catalog in catalogs().items():
        entries = catalog['entries']
        out[name] = {
            'entries': len(entries),
            'core': sum(e['tier'] == 'core' for e in entries),
            'generated': sum(e['status'] == 'generated' for e in entries),
        }
    return out


if __name__ == '__main__':
    total = {'entries': 0, 'core': 0, 'generated': 0}
    for name, row in stats().items():
        print(f'  {name:20s} entries={row["entries"]:4d}  core={row["core"]:3d}  generated={row["generated"]:3d}')
        for key in total:
            total[key] += row[key]
    print(f'  {"total":20s} entries={total["entries"]:4d}  core={total["core"]:3d}  generated={total["generated"]:3d}')
