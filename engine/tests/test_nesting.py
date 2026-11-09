#!/usr/bin/env python3
"""
Nested components: children fill the slots of their container, refusals for leaves and
unknown slots, empty slots render nothing, nested handlers and imports are collected.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import copy
import os
import sys
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from generate import generate  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

NESTED = os.path.join(ENGINE, 'specs', 'nested-cards.yaml')


def screen(components, layout='grid-12', state=None):
    spec = {'screen_id': 'nest-test', 'version': '1.0', 'layout': layout, 'components': components}
    if state:
        spec['state'] = state
    return spec


class NestingTest(unittest.TestCase):

    def test_children_render_inside_their_container_in_order(self):
        code = generate(SpecParser().parse(NESTED)).code
        grid = code.index('className="card-grid"')
        first_card = code.index('<Heading level={4}>Newsletter</Heading>')
        alert = code.index('<Alert variation="info">')
        button = code.index('onClick={handleCreateNewsletter}')
        second_card = code.index('<Heading level={4}>Announcement</Heading>')
        self.assertTrue(grid < first_card < alert < button < second_card)
        self.assertNotIn('{children}', code)

    def test_nested_handlers_and_imports_are_collected(self):
        code = generate(SpecParser().parse(NESTED)).code
        self.assertIn('const handleCreateNewsletter = ', code)
        self.assertIn('const handleCreateAnnouncement = ', code)
        self.assertIn('import { Alert, Button, Card, Heading, View } from', code)

    def test_parser_lists_nested_components(self):
        parser = SpecParser()
        spec = parser.parse(NESTED)
        ids = [c['id'] for c in parser.get_components(spec)]
        self.assertEqual(ids, ['cards', 'newsletter-card', 'newsletter-note', 'create-newsletter',
                               'announcement-card', 'create-announcement'])

    def test_leaf_refuses_children(self):
        spec = screen([{'id': 'b', 'type': 'button', 'props': {'text': 'Go'},
                        'children': [{'id': 'c', 'type': 'alert', 'props': {'message': 'x'}}]}])
        with self.assertRaises(ValueError) as caught:
            generate(spec)
        self.assertIn('takes no children', str(caught.exception))

    def test_unknown_slot_is_refused(self):
        spec = screen([{'id': 'grid', 'type': 'card-grid', 'props': {},
                        'children': [{'id': 'c', 'type': 'alert', 'slot': 'sidebar', 'props': {'message': 'x'}}]}])
        with self.assertRaises(ValueError) as caught:
            generate(spec)
        self.assertIn('slot "sidebar"', str(caught.exception))

    def test_named_slots_place_children(self):
        spec = screen([{'id': 'frame', 'type': 'header-body-footer', 'props': {}, 'children': [
            {'id': 'f', 'type': 'alert', 'slot': 'footer', 'props': {'message': 'foot'}},
            {'id': 'h', 'type': 'alert', 'slot': 'header', 'props': {'message': 'head'}},
        ]}])
        code = generate(spec).code
        self.assertIn('<View className="header"><Alert variation="info">head</Alert></View>', code)
        self.assertIn('<View className="body"></View>', code)
        self.assertIn('<View className="footer"><Alert variation="info">foot</Alert></View>', code)

    def test_empty_slots_render_nothing(self):
        spec = screen([{'id': 'grid', 'type': 'card-grid', 'props': {}},
                       {'id': 'c', 'type': 'card', 'props': {'title': 'Empty'}}])
        code = generate(spec).code
        self.assertNotIn('{children}', code)
        self.assertIn('<Card padding="medium"><Heading level={4}>Empty</Heading></Card>', code)

    def test_placeholder_text_in_a_prop_is_refused(self):
        spec = screen([{'id': 'c', 'type': 'card', 'props': {'title': 'Say {children} here'}}])
        with self.assertRaises(ValueError) as caught:
            generate(spec)
        self.assertIn('placeholder', str(caught.exception))

    def test_nesting_does_not_mutate_the_spec(self):
        spec = SpecParser().parse(NESTED)
        before = copy.deepcopy(spec)
        generate(spec)
        self.assertEqual(before, spec)

    def test_static_section_holds_children(self):
        spec = screen([{'id': 's', 'type': 'section', 'props': {'heading': 'Part', 'anchor': 'part'}, 'children': [
            {'id': 't', 'type': 'text-block', 'props': {'paragraphs': ['One.']}}]}], layout='page')
        code = generate(spec, 'react-static').code
        self.assertIn('<section className="site-section" id={"part"}><h2>{"Part"}</h2><section className="site-text"><p>{"One."}</p></section></section>', code)


if __name__ == '__main__':
    unittest.main(verbosity=2)
