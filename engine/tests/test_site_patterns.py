#!/usr/bin/env python3
"""
Site patterns: render, required-property and accessibility checks, plus the
golden byte-equality test for the static target.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
"""

import os
import re
import sys
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from generate import generate  # noqa: E402
from pattern_library import PatternLibrary  # noqa: E402
from site_patterns import register_site_patterns, SITE_TYPE_MAPPING  # noqa: E402
from spec_parser import SpecParser  # noqa: E402
from tokens import css_from_tokens, load_tokens  # noqa: E402

GOLDEN = os.path.join(ENGINE, 'tests', 'golden')
SAMPLE = os.path.join(ENGINE, 'specs', 'sample-landing.yaml')
TOKENS = os.path.join(ENGINE, 'tokens', 'default.yaml')

MINIMAL = {
    'S-01': {'src': '/a.jpg', 'alt': 'A photo'},
    'S-02': {'paragraphs': ['One.', 'Two.']},
    'S-03': {'brand': 'B', 'links': [{'label': 'Home', 'href': '/'}]},
    'S-04': {'title': 'T'},
    'S-05': {'items': [{'title': 'a', 'text': 'b'}]},
    'S-06': {'brand': 'B', 'note': 'n'},
    'S-07': {'action': '/x'},
    'S-08': {'title': 'T', 'cta': {'label': 'Go', 'href': '/'}},
    'S-09': {'quote': 'q', 'author': 'a'},
    'S-10': {'items': [{'q': 'Q?', 'a': 'A.'}]},
}


def library():
    lib = PatternLibrary()
    register_site_patterns(lib)
    return lib


class SitePatternTest(unittest.TestCase):

    def test_every_site_type_maps_to_a_registered_pattern(self):
        lib = library()
        for spec_type, pattern_id in SITE_TYPE_MAPPING.items():
            with self.subTest(type=spec_type):
                self.assertEqual(lib.get(pattern_id).pattern_id, pattern_id)

    def test_minimal_props_render(self):
        lib = library()
        for pattern_id, props in MINIMAL.items():
            with self.subTest(pattern=pattern_id):
                self.assertTrue(lib.generate(pattern_id, props).startswith('<'))

    def test_missing_required_prop_raises(self):
        lib = library()
        for pattern_id in MINIMAL:
            with self.subTest(pattern=pattern_id):
                with self.assertRaises(ValueError):
                    lib.generate(pattern_id, {})

    def test_text_is_escaped_as_string_literals(self):
        lib = library()
        out = lib.generate('S-02', {'heading': 'Use {braces} & <tags> "quoted"', 'paragraphs': ['x']})
        self.assertIn('{"Use {braces} & <tags> \\"quoted\\""}', out)
        self.assertNotIn('<tags>', out.replace('{"Use {braces} & <tags>', ''))

    def test_accessibility_basics(self):
        lib = library()
        self.assertIn('alt=', lib.generate('S-01', MINIMAL['S-01']))
        self.assertIn('aria-label="Main"', lib.generate('S-03', MINIMAL['S-03']))
        hero = lib.generate('S-04', MINIMAL['S-04'])
        self.assertEqual(hero.count('<h1>'), 1)
        form = lib.generate('S-07', MINIMAL['S-07'])
        for field in ('contact-name', 'contact-email', 'contact-message'):
            self.assertIn(f'htmlFor="{field}"', form)
            self.assertIn(f'id="{field}"', form)
        faq = lib.generate('S-10', MINIMAL['S-10'])
        self.assertIn('<details', faq)
        self.assertIn('<summary>', faq)

    def test_static_target_has_no_framework_imports(self):
        code = generate(SpecParser().parse(SAMPLE), 'react-static').code
        self.assertNotIn('@aws-amplify', code)
        self.assertNotIn('<View', code)
        self.assertTrue(code.lstrip('/* \n').startswith('SampleLanding.tsx') or 'const SampleLanding' in code)
        self.assertIn('<div className="page">', code)
        self.assertEqual(code.count('<h1>'), 1)

    def test_static_target_is_deterministic_against_golden(self):
        spec = SpecParser().parse(SAMPLE)
        a, b = generate(spec, 'react-static'), generate(spec, 'react-static')
        self.assertEqual(a.code, b.code)
        os.makedirs(GOLDEN, exist_ok=True)
        path = os.path.join(GOLDEN, 'sample-landing.react-static.sha256')
        line = f'{a.content_hash}  sample-landing  react-static  pattern-library-{a.pattern_lib_version}\n'
        if not os.path.exists(path):
            with open(path, 'w') as f:
                f.write(line)
            self.skipTest('golden hash recorded; rerun to assert')
        with open(path) as f:
            self.assertEqual(f.read(), line)

    def test_tokens_emit_sorted_deterministic_css(self):
        tokens = load_tokens(TOKENS)
        css = css_from_tokens(tokens)
        self.assertEqual(css, css_from_tokens(tokens))
        self.assertIn('--color-primary: #3B5BDB;', css)
        self.assertIn('--font-size-h1: 28px;', css)
        self.assertIn('--font-size-h1: 36px;', css.split('@media')[1])
        names = re.findall(r'--color-[a-z-]+', css.split('@media')[0])
        self.assertEqual(names, sorted(names))


if __name__ == '__main__':
    unittest.main(verbosity=2)
