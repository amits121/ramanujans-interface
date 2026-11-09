#!/usr/bin/env python3
"""
Generate Module - the one pure entry point of the engine.

    artifact = generate(spec, target)
    artifact = generate(spec, target, pattern_set=tenant_set)

Pure: the result depends only on the validated specification, the pattern
library version, the target and, when given, the tenant's pattern set. No clock, no randomness, no environment,
no file or network access inside this call. Reading the specification from
disk is the caller's job (see SpecParser or the command-line section below).

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import hashlib
import json
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from component_mapper import ComponentMapper  # noqa: E402
from pattern_library import PatternLibrary, PATTERN_LIBRARY_VERSION  # noqa: E402
from site_patterns import register_site_patterns, SITE_TYPE_MAPPING  # noqa: E402
from behavior_patterns import register_behavior_patterns, BEHAVIOR_TYPE_MAPPING  # noqa: E402
from pattern_sets import PatternSet  # noqa: E402
from libs.registry import register_packs  # noqa: E402
from libs.packs.mobile.patterns import MODULE as MOBILE_MODULE, WRAPPER as MOBILE_WRAPPER  # noqa: E402

# target -> how the file is shaped: which packs register, the layout container, the imports it needs.
TARGET_CONFIG: Dict[str, Dict[str, Any]] = {
    'react-amplify': {'packs': ['amplify'], 'site': True, 'behavior': True, 'container': 'View', 'use_amplify': True},
    'react-static': {'packs': [], 'site': True, 'behavior': True, 'container': 'div', 'use_amplify': False},
    'next': {'packs': ['next'], 'site': True, 'behavior': True, 'container': 'div', 'use_amplify': False},
    'material': {'packs': ['material'], 'site': True, 'behavior': True, 'container': 'div', 'use_amplify': False},
    'firebase': {'packs': ['firebase'], 'site': True, 'behavior': True, 'container': 'div', 'use_amplify': False},
    'react-native': {'packs': ['mobile'], 'site': False, 'behavior': False, 'container': 'View', 'use_amplify': False,
                     'container_import': ('react-native', ['SafeAreaView', 'ScrollView', 'StyleSheet', 'View']),
                     'wrapper': MOBILE_WRAPPER, 'base_module': MOBILE_MODULE},
}
TARGETS = tuple(TARGET_CONFIG)


@dataclass(frozen=True)
class Artifact:
    """What a generation returns. Both hashes are stable for identical inputs."""
    code: str
    content_hash: str          # sha256 of the output bytes
    spec_key: str              # sha256 of canonical(spec) + pattern library version + target [+ pattern set id]
    pattern_lib_version: str
    target: str
    pattern_set: str = ''      # the tenant's pattern set id, '' when generation was unrestricted


def canonical_spec(spec: Dict[str, Any]) -> str:
    """One byte-for-byte form of a specification: sorted keys, no whitespace, UTF-8."""
    return json.dumps(spec, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def spec_key(spec: Dict[str, Any], target: str, version: str = PATTERN_LIBRARY_VERSION, pattern_set_id: str = '') -> str:
    """The cache key: identical specification, version, target and pattern set give the same key."""
    material = canonical_spec(spec) + '\n' + version + '\n' + target
    if pattern_set_id:
        material += '\n' + pattern_set_id
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def generate(spec: Dict[str, Any], target: str = 'react-amplify', pattern_set: Optional[PatternSet] = None) -> Artifact:
    """
    Generate the artifact for a validated specification.

    Args:
        spec: Specification dictionary, already validated against the schema.
        target: 'react-amplify' (component screens), 'react-static' (hosted sites, no Amplify), or another
                registered target.
        pattern_set: the tenant's pattern set; any type outside it is refused. None = unrestricted.

    Returns:
        Artifact with the code and its hashes.

    Raises:
        ValueError: unknown target, unknown type, type outside the pattern set, or a declaration collision.
    """
    if target not in TARGETS:
        raise ValueError(f'Unknown target: {target}')

    cfg = TARGET_CONFIG[target]
    library = PatternLibrary()
    mapper = ComponentMapper(library, container=cfg['container'], use_amplify=cfg['use_amplify'],
                             container_import=cfg.get('container_import'), flat_wrapper=cfg.get('wrapper'),
                             base_module=cfg.get('base_module'))
    if cfg['site']:
        register_site_patterns(library)
        mapper.register_types(SITE_TYPE_MAPPING)
    if cfg['behavior']:
        register_behavior_patterns(library)
        mapper.register_types(BEHAVIOR_TYPE_MAPPING)
    mapper.register_types(register_packs(library, cfg['packs']))   # packs win over site names on their target
    if pattern_set is not None:
        mapper.restrict_types(pattern_set.types, pattern_set.set_id)
    code = mapper.generate(spec)
    set_id = pattern_set.set_id if pattern_set is not None else ''
    return Artifact(
        code=code,
        content_hash=hashlib.sha256(code.encode('utf-8')).hexdigest(),
        spec_key=spec_key(spec, target, library.version, set_id),
        pattern_lib_version=library.version,
        target=target,
        pattern_set=set_id,
    )


if __name__ == '__main__':
    # Command-line use only. File reading happens here, outside generate().
    import sys
    from spec_parser import SpecParser

    from pattern_sets import load_pattern_set

    if len(sys.argv) < 2:
        print('Usage: python generate.py <spec.yaml> [--static | --target <name>] [--pattern-set <set.yaml>] [--hash-only]')
        sys.exit(1)

    target = 'react-static' if '--static' in sys.argv else 'react-amplify'
    if '--target' in sys.argv:
        target = sys.argv[sys.argv.index('--target') + 1]
    chosen_set = load_pattern_set(sys.argv[sys.argv.index('--pattern-set') + 1]) if '--pattern-set' in sys.argv else None
    artifact = generate(SpecParser().parse(sys.argv[1]), target, pattern_set=chosen_set)
    if '--hash-only' in sys.argv:
        print(f'{artifact.content_hash}  {artifact.spec_key}  {artifact.pattern_lib_version}')
    else:
        sys.stdout.write(artifact.code)
