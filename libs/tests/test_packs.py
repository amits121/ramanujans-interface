#!/usr/bin/env python3
"""
Library tests: catalogs are valid and complete, every pattern renders from its sample,
golden hashes per pack and per target sample, escaping, and determinism across targets.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
"""

import hashlib
import os
import sys
import unittest

LIBS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(LIBS)
ENGINE = os.path.join(ROOT, 'engine')
for path in (ROOT, ENGINE):
    if path not in sys.path:
        sys.path.insert(0, path)

from libs import registry  # noqa: E402
from generate import generate, TARGETS  # noqa: E402
from pattern_library import PatternLibrary  # noqa: E402
from site_patterns import register_site_patterns  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

GOLDEN = os.path.join(LIBS, 'tests', 'golden')
SPECS = os.path.join(LIBS, 'specs')
TARGET_SPECS = {
    'react-amplify': 'sample-amplify.yaml', 'next': 'sample-next.yaml', 'material': 'sample-material.yaml',
    'firebase': 'sample-firebase.yaml', 'react-native': 'sample-mobile.yaml',
}


def golden(path, line, test):
    os.makedirs(GOLDEN, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(line)
        test.skipTest(f'golden recorded: {os.path.basename(path)}; rerun to assert')
    with open(path) as f:
        test.assertEqual(f.read(), line)


class CatalogTest(unittest.TestCase):

    def test_catalogs_load_and_validate(self):
        stats = registry.stats()
        self.assertEqual(sorted(stats), ['amplify-ui-react', 'firebase', 'material-web', 'nextjs', 'react-core', 'react-native-expo', 'typescript'])
        self.assertGreater(sum(r['entries'] for r in stats.values()), 400)

    def test_every_generated_entry_resolves_to_a_registered_pattern(self):
        lib = PatternLibrary()
        register_site_patterns(lib)
        ids = set(registry.pattern_ids()) | set(lib.list_patterns())
        missing = []
        for name, catalog in registry.catalogs().items():
            for entry in catalog['entries']:
                if entry['status'] == 'generated' and entry['pattern'] not in ids:
                    missing.append(f'{name}:{entry["id"]}->{entry["pattern"]}')
        self.assertEqual(missing, [])

    def test_core_tier_is_the_minority(self):
        for name, row in registry.stats().items():
            with self.subTest(catalog=name):
                self.assertLess(row['core'], row['entries'])


class PackTest(unittest.TestCase):

    def test_every_pattern_has_a_sample_and_renders(self):
        for name in registry.PACK_NAMES:
            pack = registry.load_pack(name)
            with self.subTest(pack=name):
                self.assertEqual(sorted(pack.SAMPLES), sorted(p.pattern_id for p in pack.PATTERNS))
                for pattern in pack.PATTERNS:
                    out = pattern.generate(pack.SAMPLES[pattern.pattern_id])
                    self.assertIsInstance(out, str)
                for spec_type, pattern_id in pack.TYPE_MAPPING.items():
                    self.assertTrue(any(p.pattern_id == pattern_id for p in pack.PATTERNS), f'{name}: {spec_type} -> {pattern_id}')

    def test_pack_golden_hashes(self):
        for name in registry.PACK_NAMES:
            pack = registry.load_pack(name)
            with self.subTest(pack=name):
                rendered = '\n'.join(p.pattern_id + '\n' + p.generate(pack.SAMPLES[p.pattern_id]) for p in pack.PATTERNS)
                digest = hashlib.sha256(rendered.encode('utf-8')).hexdigest()
                golden(os.path.join(GOLDEN, f'pack-{name}.sha256'), f'{digest}  pack-{name}\n', self)

    def test_missing_required_props_raise(self):
        pack = registry.load_pack('amplify')
        with self.assertRaises(ValueError):
            pack.PATTERNS[0].generate({})

    def test_text_is_escaped_in_every_pack(self):
        probes = {
            'amplify': ('AMP-02', {'text': 'a {b} <c> "d"'}),
            'next': ('NXT-02', {'href': '/x', 'text': 'a {b} <c> "d"'}),
            'material': ('MAT-01', {'label': 'a {b} <c> "d"'}),
            'firebase': ('FB-03', {'label': 'a {b} <c> "d"'}),
            'mobile': ('MOB-03', {'text': 'a {b} <c> "d"'}),
        }
        for name, (pid, props) in probes.items():
            with self.subTest(pack=name):
                pattern = next(p for p in registry.load_pack(name).PATTERNS if p.pattern_id == pid)
                self.assertIn('{"a {b} <c> \\"d\\""}', pattern.generate(props))


class TargetTest(unittest.TestCase):

    def test_every_target_generates_its_sample_deterministically(self):
        parser = SpecParser()
        for target, name in TARGET_SPECS.items():
            with self.subTest(target=target):
                self.assertIn(target, TARGETS)
                spec = parser.parse(os.path.join(SPECS, name))
                a, b = generate(spec, target), generate(spec, target)
                self.assertEqual(a.code, b.code)
                self.assertNotIn('TODO', a.code.split('return (')[1])
                golden(os.path.join(GOLDEN, f'target-{target}.sha256'),
                       f'{a.content_hash}  {name}  {target}  pattern-library-{a.pattern_lib_version}\n', self)

    def test_unknown_type_is_refused(self):
        spec = {'screen_id': 'x', 'version': '1.0', 'layout': 'page', 'components': [{'id': 'a', 'type': 'no-such-thing', 'props': {}}]}
        with self.assertRaises(ValueError):
            generate(spec, 'react-static')

    def test_mobile_file_carries_one_stylesheet_block(self):
        spec = SpecParser().parse(os.path.join(SPECS, 'sample-mobile.yaml'))
        code = generate(spec, 'react-native').code
        self.assertEqual(code.count('StyleSheet.create('), 1)
        self.assertIn("from 'react-native';", code)
        self.assertNotIn('className', code)

    def test_firebase_file_carries_handler_bodies_and_effects(self):
        spec = SpecParser().parse(os.path.join(SPECS, 'sample-firebase.yaml'))
        code = generate(spec, 'firebase').code
        self.assertIn('signInWithEmailAndPassword(getAuth(), email, password)', code)
        self.assertIn('useEffect(() => {', code)
        self.assertIn("import React, { useEffect, useState } from 'react';", code)
        self.assertIn('export const firebaseApp = initializeApp({', code)
        self.assertIn('const handleGoogleSignIn = async () => {', code)
        self.assertIn('const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {', code)


if __name__ == '__main__':
    unittest.main(verbosity=2)
