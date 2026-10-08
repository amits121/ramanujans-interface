#!/usr/bin/env python3
"""
GA-5 Determinism Gate (step 6 of the determinism sequence).

Before any artifact ships: canonicalize the specification, compute its key,
generate twice in this process and once in a fresh process, and verify every
copy is byte-equal with a stable content hash. Any mismatch is an andon stop:
the gate reports FAIL and the caller must halt and roll back.

    python gate.py <spec.yaml> [--static] [--expect <content_hash>]

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import json
import os
import subprocess
import sys
from typing import Any, Dict, Optional

from generate import generate, spec_key

ENGINE = os.path.dirname(os.path.abspath(__file__))


def run_gate(spec: Dict[str, Any], target: str = 'react-amplify', spec_path: Optional[str] = None,
             expect: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the gate. Pure apart from the optional fresh-process check, which
    re-runs generate.py on spec_path with the same interpreter.
    """
    first, second = generate(spec, target), generate(spec, target)
    checks = {
        'same_process_byte_equal': first.code == second.code,
        'same_process_hash_stable': first.content_hash == second.content_hash,
        'spec_key_recomputes': first.spec_key == spec_key(spec, target),
    }
    if spec_path:
        cmd = [sys.executable, os.path.join(ENGINE, 'generate.py'), spec_path, '--target', target]
        fresh = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        checks['fresh_process_byte_equal'] = fresh == first.code
    if expect is not None:
        checks['matches_expected_hash'] = first.content_hash == expect
    return {
        'ok': all(checks.values()),
        'checks': checks,
        'content_hash': first.content_hash,
        'spec_key': first.spec_key,
        'pattern_lib_version': first.pattern_lib_version,
        'target': target,
    }


if __name__ == '__main__':
    from spec_parser import SpecParser

    if len(sys.argv) < 2:
        print('Usage: python gate.py <spec.yaml> [--static] [--expect <content_hash>]')
        sys.exit(1)
    path = sys.argv[1]
    target = 'react-static' if '--static' in sys.argv else 'react-amplify'
    expect = sys.argv[sys.argv.index('--expect') + 1] if '--expect' in sys.argv else None
    report = run_gate(SpecParser().parse(path), target, spec_path=path, expect=expect)
    print(json.dumps(report, indent=2))
    print('GATE PASS' if report['ok'] else 'GATE FAIL - andon: halt, do not ship, roll back')
    sys.exit(0 if report['ok'] else 2)
