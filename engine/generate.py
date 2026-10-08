#!/usr/bin/env python3
"""
Generate Module - the one pure entry point of the engine.

    artifact = generate(spec, target)

Pure: the result depends only on the validated specification, the pattern
library version and the target. No clock, no randomness, no environment,
no file or network access inside this call. Reading the specification from
disk is the caller's job (see SpecParser or the command-line section below).

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict

from component_mapper import ComponentMapper
from pattern_library import PatternLibrary, PATTERN_LIBRARY_VERSION
from site_patterns import register_site_patterns, SITE_TYPE_MAPPING

TARGETS = ('react-amplify', 'react-static')


@dataclass(frozen=True)
class Artifact:
    """What a generation returns. Both hashes are stable for identical inputs."""
    code: str
    content_hash: str          # sha256 of the output bytes
    spec_key: str              # sha256 of canonical(spec) + pattern library version + target
    pattern_lib_version: str
    target: str


def canonical_spec(spec: Dict[str, Any]) -> str:
    """One byte-for-byte form of a specification: sorted keys, no whitespace, UTF-8."""
    return json.dumps(spec, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def spec_key(spec: Dict[str, Any], target: str, version: str = PATTERN_LIBRARY_VERSION) -> str:
    """The cache key: identical specification, version and target give the same key."""
    material = canonical_spec(spec) + '\n' + version + '\n' + target
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def generate(spec: Dict[str, Any], target: str = 'react-amplify') -> Artifact:
    """
    Generate the artifact for a validated specification.

    Args:
        spec: Specification dictionary, already validated against the schema.
        target: 'react-amplify' (component screens) or 'react-static' (hosted sites, no Amplify).

    Returns:
        Artifact with the code and its hashes.

    Raises:
        ValueError: unknown target.
    """
    if target not in TARGETS:
        raise ValueError(f'Unknown target: {target}')

    library = PatternLibrary()
    register_site_patterns(library)
    static = target == 'react-static'
    mapper = ComponentMapper(library, container='div' if static else 'View', use_amplify=not static)
    mapper.register_types(SITE_TYPE_MAPPING)
    code = mapper.generate(spec)
    return Artifact(
        code=code,
        content_hash=hashlib.sha256(code.encode('utf-8')).hexdigest(),
        spec_key=spec_key(spec, target, library.version),
        pattern_lib_version=library.version,
        target=target,
    )


if __name__ == '__main__':
    # Command-line use only. File reading happens here, outside generate().
    import sys
    from spec_parser import SpecParser

    if len(sys.argv) < 2:
        print('Usage: python generate.py <spec.yaml> [--static] [--hash-only]')
        sys.exit(1)

    target = 'react-static' if '--static' in sys.argv else 'react-amplify'
    artifact = generate(SpecParser().parse(sys.argv[1]), target)
    if '--hash-only' in sys.argv:
        print(f'{artifact.content_hash}  {artifact.spec_key}  {artifact.pattern_lib_version}')
    else:
        sys.stdout.write(artifact.code)
