#!/usr/bin/env python3
"""
Pattern Sets Module - per-tenant component sets.

A pattern set names the specification types a tenant may use. Generation under a set
refuses any other type, so two tenants on one engine get two different vocabularies
from one library, and the set id takes part in the cache key.

    pattern_set = load_pattern_set('engine/pattern-sets/site-only.yaml')
    artifact = generate(spec, 'react-static', pattern_set=pattern_set)

File access lives in load_pattern_set() only.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import os
from dataclasses import dataclass
from typing import FrozenSet

import yaml

SETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pattern-sets')


@dataclass(frozen=True)
class PatternSet:
    set_id: str
    types: FrozenSet[str]

    def allows(self, spec_type: str) -> bool:
        return spec_type in self.types


def load_pattern_set(path: str) -> PatternSet:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or 'id' not in data or not isinstance(data.get('types'), list) or not data['types']:
        raise ValueError(f'pattern set {path}: needs "id" and a non-empty "types" list')
    types = [str(t) for t in data['types']]
    if len(set(types)) != len(types):
        raise ValueError(f'pattern set {path}: duplicate type')
    return PatternSet(set_id=str(data['id']), types=frozenset(types))


def named_pattern_set(name: str) -> PatternSet:
    return load_pattern_set(os.path.join(SETS_DIR, f'{name}.yaml'))
