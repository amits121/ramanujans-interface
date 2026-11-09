#!/usr/bin/env python3
"""
Per-tenant pattern sets: generation under a set succeeds for allowed types, refuses others,
the set id takes part in the cache key, and malformed sets are refused.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import os
import subprocess
import sys
import tempfile
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from generate import generate  # noqa: E402
from pattern_sets import PatternSet, load_pattern_set, named_pattern_set  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

LANDING = os.path.join(ENGINE, 'specs', 'sample-landing.yaml')
LOGIN = os.path.join(ENGINE, 'specs', 'login-screen.yaml')
SITE_ONLY = os.path.join(ENGINE, 'pattern-sets', 'site-only.yaml')


class PatternSetTest(unittest.TestCase):

    def test_site_tenant_generates_the_site_and_the_key_carries_the_set(self):
        spec = SpecParser().parse(LANDING)
        site_only = named_pattern_set('site-only')
        restricted = generate(spec, 'react-static', pattern_set=site_only)
        unrestricted = generate(spec, 'react-static')
        self.assertEqual(restricted.code, unrestricted.code)
        self.assertEqual(restricted.content_hash, unrestricted.content_hash)
        self.assertNotEqual(restricted.spec_key, unrestricted.spec_key)
        self.assertEqual(restricted.pattern_set, 'site-only')
        self.assertEqual(unrestricted.pattern_set, '')

    def test_type_outside_the_set_is_refused(self):
        spec = SpecParser().parse(LOGIN)
        with self.assertRaises(ValueError) as caught:
            generate(spec, 'react-amplify', pattern_set=named_pattern_set('site-only'))
        self.assertIn('pattern set "site-only"', str(caught.exception))
        self.assertIn('text-input', str(caught.exception))

    def test_two_tenants_two_keys(self):
        spec = SpecParser().parse(LANDING)
        a = generate(spec, 'react-static', pattern_set=PatternSet('tenant-a', frozenset(load_pattern_set(SITE_ONLY).types)))
        b = generate(spec, 'react-static', pattern_set=PatternSet('tenant-b', frozenset(load_pattern_set(SITE_ONLY).types)))
        self.assertEqual(a.code, b.code)
        self.assertNotEqual(a.spec_key, b.spec_key)

    def test_malformed_sets_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            for text in ('id: x\n', 'types: [a]\n', 'id: x\ntypes: []\n', 'id: x\ntypes: [a, a]\n'):
                path = os.path.join(d, 'set.yaml')
                with open(path, 'w') as f:
                    f.write(text)
                with self.assertRaises(ValueError):
                    load_pattern_set(path)

    def test_command_line_takes_a_pattern_set(self):
        ok = subprocess.run([sys.executable, os.path.join(ENGINE, 'generate.py'), LANDING, '--static',
                             '--pattern-set', SITE_ONLY, '--hash-only'], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        refused = subprocess.run([sys.executable, os.path.join(ENGINE, 'generate.py'), LOGIN,
                                  '--pattern-set', SITE_ONLY, '--hash-only'], capture_output=True, text=True)
        self.assertNotEqual(refused.returncode, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
