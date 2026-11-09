#!/usr/bin/env python3
"""
Behaviour patterns: every pattern renders and declares from its sample, state references are
checked (declare before use), declaration collisions are refused, identical declarations merge
once, the samples are deterministic against goldens, and the generated files type-check.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import copy
import os
import subprocess
import sys
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(ENGINE)
sys.path.insert(0, ENGINE)

from behavior_patterns import BEHAVIOR_TYPE_MAPPING, PATTERNS, SAMPLES  # noqa: E402
from generate import generate  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

GOLDEN = os.path.join(ENGINE, 'tests', 'golden')
LOGIN = os.path.join(ENGINE, 'specs', 'login-flow.yaml')
PROJECTS = os.path.join(ENGINE, 'specs', 'project-list.yaml')
CONTEXT = {'component_id': 'test', 'screen_id': 'test', 'state': frozenset({'email', 'password', 'homes', 'status'})}


def golden(path, line, test):
    os.makedirs(GOLDEN, exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(line)
        test.skipTest(f'golden recorded: {os.path.basename(path)}; rerun to assert')
    with open(path) as f:
        test.assertEqual(f.read(), line)


class BehaviorPatternTest(unittest.TestCase):

    def test_every_pattern_renders_and_declares_from_its_sample(self):
        self.assertEqual(sorted(SAMPLES), sorted(p.pattern_id for p in PATTERNS))
        for pattern in PATTERNS:
            with self.subTest(pattern=pattern.pattern_id):
                props = dict(SAMPLES[pattern.pattern_id], name=SAMPLES[pattern.pattern_id].get('name', 'x'))
                self.assertIsInstance(pattern.generate(props), str)
                self.assertIsInstance(pattern.declare(props, CONTEXT), dict)

    def test_type_mapping_resolves(self):
        ids = {p.pattern_id for p in PATTERNS}
        for spec_type, pattern_id in BEHAVIOR_TYPE_MAPPING.items():
            self.assertIn(pattern_id, ids, spec_type)
        self.assertEqual(len(BEHAVIOR_TYPE_MAPPING), 10)
        self.assertEqual(sorted({p.category for p in PATTERNS}), ['A', 'D', 'E', 'F', 'I', 'S', 'V', 'X'])

    def test_undeclared_state_variable_is_refused(self):
        spec = SpecParser().parse(LOGIN)
        del spec['state']['password']
        with self.assertRaises(ValueError) as caught:
            generate(spec, 'react-static')
        self.assertIn('"password"', str(caught.exception))

    def test_declare_before_use(self):
        spec = {'screen_id': 'order', 'version': '1.0', 'layout': 'page', 'state': {'x': ''}, 'components': [
            {'id': 'w', 'type': 'show-if', 'props': {'state': 'status', 'equals': 'done'},
             'children': [{'id': 't', 'type': 'template-text', 'props': {'template': 'ok'}}]},
            {'id': 's', 'type': 'async-status'}]}
        with self.assertRaises(ValueError):
            generate(spec, 'react-static')
        spec['components'].reverse()
        self.assertIn("useState<AsyncStatus>('idle')", generate(spec, 'react-static').code)

    def test_declaration_collision_is_refused(self):
        spec = {'screen_id': 'clash', 'version': '1.0', 'layout': 'page', 'state': {'email': ''}, 'components': [
            {'id': 'a', 'type': 'validator', 'props': {'name': 'validate', 'fields': [
                {'field': 'email', 'rules': [{'type': 'required', 'message': 'A'}]}]}},
            {'id': 'b', 'type': 'validator', 'props': {'name': 'validate', 'fields': [
                {'field': 'email', 'rules': [{'type': 'required', 'message': 'B'}]}]}}]}
        with self.assertRaises(ValueError) as caught:
            generate(spec, 'react-static')
        self.assertIn('declared twice with different code', str(caught.exception))

    def test_identical_declarations_merge_once(self):
        code = generate(SpecParser().parse(LOGIN), 'react-static').code
        self.assertEqual(code.count("type AsyncStatus = "), 1)
        self.assertEqual(code.count("const [status, setStatus]"), 1)
        self.assertEqual(code.count("const [errorMessage, setErrorMessage]"), 1)

    def test_form_handler_validates_then_acts(self):
        code = generate(SpecParser().parse(LOGIN), 'react-static').code
        handler = code[code.index('const handleLogin'):code.index('const submitLogin')]
        self.assertIn('e.preventDefault();', handler)
        self.assertTrue(handler.index('if (!validateLogin()) return;') < handler.index('submitLogin();'))
        self.assertIn('<form className="form" aria-label={"Sign in"} onSubmit={handleLogin} noValidate>', code)

    def test_unknown_rule_and_method_are_refused(self):
        base = {'screen_id': 'bad', 'version': '1.0', 'layout': 'page', 'state': {'email': ''}}
        rule = dict(base, components=[{'id': 'v', 'type': 'validator', 'props': {'name': 'v', 'fields': [
            {'field': 'email', 'rules': [{'type': 'shouty', 'message': 'x'}]}]}}])
        with self.assertRaises(ValueError):
            generate(rule, 'react-static')
        method = dict(base, components=[{'id': 'r', 'type': 'submit-request',
                                         'props': {'name': 'send', 'endpoint': '/x', 'method': 'GET'}}])
        with self.assertRaises(ValueError):
            generate(method, 'react-static')

    def test_template_text_escapes_and_binds(self):
        spec = {'screen_id': 't', 'version': '1.0', 'layout': 'page', 'state': {'n': 'a'}, 'components': [
            {'id': 'x', 'type': 'template-text', 'props': {'template': 'Hi {n}, use "quotes" & <tags>'}}]}
        code = generate(spec, 'react-static').code
        self.assertIn('<p>{"Hi " + String(n) + ", use \\"quotes\\" & <tags>"}</p>', code)

    def test_generation_does_not_mutate_the_spec(self):
        for path in (LOGIN, PROJECTS):
            spec = SpecParser().parse(path)
            before = copy.deepcopy(spec)
            generate(spec, 'react-static')
            self.assertEqual(before, spec)

    def test_samples_are_deterministic_against_goldens(self):
        parser = SpecParser()
        for path, target in ((LOGIN, 'react-static'), (LOGIN, 'react-amplify'), (PROJECTS, 'react-static')):
            with self.subTest(spec=os.path.basename(path), target=target):
                spec = parser.parse(path)
                a, b = generate(spec, target), generate(spec, target)
                self.assertEqual(a.code, b.code)
                self.assertNotIn('{children}', a.code)
                name = spec['screen_id']
                golden(os.path.join(GOLDEN, f'{name}.{target}.sha256'),
                       f'{a.content_hash}  {name}  {target}  pattern-library-{a.pattern_lib_version}\n', self)

    def test_generated_static_files_type_check(self):
        tsc = os.path.join(ROOT, 'scripts', 'static-shell', 'node_modules', '.bin', 'tsc')
        if not os.path.exists(tsc):
            self.skipTest('tsc not installed in scripts/static-shell')
        result = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'check_tsx.py'),
                                 f'{LOGIN}:react-static', f'{PROJECTS}:react-static'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
