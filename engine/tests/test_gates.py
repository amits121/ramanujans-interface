#!/usr/bin/env python3
"""
Determinism gate, quality gates and cache tests.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
"""

import os
import sys
import tempfile
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from cache import ArtifactCache  # noqa: E402
from gate import run_gate  # noqa: E402
from generate import generate  # noqa: E402
from quality import check_html, check_site  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

SAMPLE = os.path.join(ENGINE, 'specs', 'sample-landing.yaml')

GOOD_HTML = """<!doctype html><html lang="en"><head><title>T</title>
<meta name="viewport" content="width=device-width"></head><body>
<nav aria-label="Main"><a href="/">Home</a></nav><h1>One</h1><h2>Two</h2><h3>Three</h3>
<img src="a.jpg" alt="A photo"><form><label for="n">Name</label><input id="n" type="text">
<button type="submit">Send</button></form></body></html>"""

BAD_HTML = """<html><head></head><body><nav><a href="/"></a></nav><h1>A</h1><h1>B</h1><h3>skip</h3>
<img src="a.jpg"><input id="x" type="text"><button></button><script></script></body></html>"""


class GateTest(unittest.TestCase):

    def test_gate_passes_for_the_sample_in_both_modes(self):
        spec = SpecParser().parse(SAMPLE)
        report = run_gate(spec, 'react-static', spec_path=SAMPLE)
        self.assertTrue(report['ok'], report)
        self.assertTrue(report['checks']['fresh_process_byte_equal'])

    def test_gate_fails_on_wrong_expected_hash(self):
        spec = SpecParser().parse(SAMPLE)
        report = run_gate(spec, 'react-static', expect='0' * 64)
        self.assertFalse(report['ok'])
        self.assertFalse(report['checks']['matches_expected_hash'])


class QualityTest(unittest.TestCase):

    def test_good_html_passes_every_check(self):
        checks = check_html(GOOD_HTML)
        failed = [k for k, (ok, _) in checks.items() if not ok]
        self.assertEqual(failed, [])

    def test_bad_html_fails_the_right_checks(self):
        checks = check_html(BAD_HTML)
        failed = sorted(k for k, (ok, _) in checks.items() if not ok)
        self.assertEqual(failed, sorted([
            'html_lang', 'title', 'viewport_meta', 'single_h1', 'heading_order', 'images_have_alt',
            'controls_have_labels', 'nav_labelled', 'links_have_text', 'buttons_have_text', 'no_script']))

    def test_site_budget(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, 'index.html'), 'w') as f:
                f.write(GOOD_HTML)
            os.makedirs(os.path.join(d, 'assets'))
            with open(os.path.join(d, 'assets', 'a.css'), 'w') as f:
                f.write('body{}')
            self.assertTrue(check_site(d)['ok'])
            self.assertFalse(check_site(d, html_max=10)['ok'])


class CacheTest(unittest.TestCase):

    def test_round_trip_by_spec_key(self):
        spec = SpecParser().parse(SAMPLE)
        artifact = generate(spec, 'react-static')
        with tempfile.TemporaryDirectory() as d:
            cache = ArtifactCache(d)
            self.assertIsNone(cache.get(artifact.spec_key))
            cache.put(artifact)
            hit = cache.get(artifact.spec_key)
            self.assertEqual(hit, artifact)
            self.assertEqual(cache.stats()['entries'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
