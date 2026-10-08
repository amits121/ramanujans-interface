#!/usr/bin/env python3
"""
Golden byte-equality test (determinism step 4).

The same specification must produce identical bytes and a stable content hash
in the same process, in a fresh process, and against the recorded golden hash.

Run:  python -m unittest discover -s engine/tests -v
      (from the repository root, or any directory: paths are resolved here)

Copyright (c) 2025 Intelligent Cloud Lab Inc.
"""

import os
import re
import subprocess
import sys
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from spec_parser import SpecParser  # noqa: E402
from generate import generate, spec_key  # noqa: E402

SPECS = ('login-screen', 'dashboard-screen')
GOLDEN = os.path.join(ENGINE, 'tests', 'golden')
FORBIDDEN = re.compile(r'\b(19|20)\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}')  # any timestamp


def spec_path(name):
    return os.path.join(ENGINE, 'specs', f'{name}.yaml')


class DeterminismTest(unittest.TestCase):

    def test_same_process_twice_is_byte_equal(self):
        parser = SpecParser()
        for name in SPECS:
            with self.subTest(spec=name):
                spec = parser.parse(spec_path(name))
                a, b = generate(spec), generate(spec)
                self.assertEqual(a.code, b.code)
                self.assertEqual(a.content_hash, b.content_hash)
                self.assertEqual(a.spec_key, b.spec_key)

    def test_fresh_process_is_byte_equal(self):
        for name in SPECS:
            with self.subTest(spec=name):
                runs = [
                    subprocess.run([sys.executable, os.path.join(ENGINE, 'generate.py'), spec_path(name), '--target', 'react-amplify'],
                                   capture_output=True, text=True, check=True).stdout
                    for _ in range(2)
                ]
                self.assertEqual(runs[0], runs[1])
                self.assertEqual(runs[0], generate(SpecParser().parse(spec_path(name))).code)

    def test_output_carries_no_timestamp(self):
        for name in SPECS:
            with self.subTest(spec=name):
                code = generate(SpecParser().parse(spec_path(name))).code
                self.assertIsNone(FORBIDDEN.search(code))
                self.assertIn('Pattern library: 1.2.0', code)

    def test_generation_does_not_mutate_the_spec(self):
        parser = SpecParser()
        for name in SPECS:
            with self.subTest(spec=name):
                spec = parser.parse(spec_path(name))
                before = repr(spec)
                generate(spec)
                self.assertEqual(before, repr(spec))

    def test_spec_key_ignores_key_order(self):
        spec = SpecParser().parse(spec_path('login-screen'))
        reordered = {k: spec[k] for k in reversed(list(spec))}
        self.assertEqual(spec_key(spec, 'react-amplify'), spec_key(reordered, 'react-amplify'))

    def test_matches_recorded_golden_hash(self):
        """First run records the golden hashes; every later run must match them."""
        os.makedirs(GOLDEN, exist_ok=True)
        for name in SPECS:
            with self.subTest(spec=name):
                artifact = generate(SpecParser().parse(spec_path(name)))
                path = os.path.join(GOLDEN, f'{name}.sha256')
                line = f'{artifact.content_hash}  {name}  pattern-library-{artifact.pattern_lib_version}\n'
                if not os.path.exists(path):
                    with open(path, 'w') as f:
                        f.write(line)
                    self.skipTest(f'golden hash recorded for {name}; rerun to assert')
                with open(path) as f:
                    self.assertEqual(f.read(), line)


if __name__ == '__main__':
    unittest.main(verbosity=2)
