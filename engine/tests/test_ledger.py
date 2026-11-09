#!/usr/bin/env python3
"""
Hash-chained ledger: entries link, tampering and reordering break the chain, the file
round-trips, and an entry is a pure function of its inputs.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import copy
import os
import sys
import tempfile
import unittest

ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ENGINE)

from generate import generate  # noqa: E402
from ledger import GENESIS, Ledger, chain_entry, verify_chain  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

SPECS = [os.path.join(ENGINE, 'specs', n) for n in ('login-screen.yaml', 'dashboard-screen.yaml', 'nested-cards.yaml')]


def artifacts():
    parser = SpecParser()
    return [(generate(parser.parse(p)), parser.parse(p)) for p in SPECS]


def chain():
    entries, previous = [], GENESIS
    for i, (artifact, spec) in enumerate(artifacts()):
        entry = chain_entry(previous, artifact, spec['screen_id'], spec['version'], i)
        entries.append(entry)
        previous = entry['entry_hash']
    return entries


class LedgerTest(unittest.TestCase):

    def test_chain_verifies_and_links(self):
        entries = chain()
        ok, detail = verify_chain(entries)
        self.assertTrue(ok, detail)
        self.assertEqual(entries[0]['previous_hash'], GENESIS)
        self.assertEqual(entries[1]['previous_hash'], entries[0]['entry_hash'])
        self.assertNotIn('timestamp', entries[0])

    def test_entry_is_pure(self):
        artifact, spec = artifacts()[0]
        a = chain_entry(GENESIS, artifact, spec['screen_id'], spec['version'], 0)
        b = chain_entry(GENESIS, artifact, spec['screen_id'], spec['version'], 0)
        self.assertEqual(a, b)

    def test_tampering_breaks_the_chain(self):
        entries = chain()
        tampered = copy.deepcopy(entries)
        tampered[1]['content_hash'] = 'f' * 64
        self.assertFalse(verify_chain(tampered)[0])
        reordered = [entries[1], entries[0], entries[2]]
        self.assertFalse(verify_chain(reordered)[0])
        truncated = entries[1:]
        self.assertFalse(verify_chain(truncated)[0])

    def test_file_round_trip_and_broken_file_refuses_append(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'ledger.jsonl')
            ledger = Ledger(path)
            self.assertEqual(ledger.head(), GENESIS)
            for artifact, spec in artifacts():
                ledger.append(artifact, spec['screen_id'], spec['version'])
            ok, detail = ledger.verify()
            self.assertTrue(ok, detail)
            self.assertEqual(len(ledger.entries()), 3)
            with open(path, 'a', encoding='utf-8') as f:
                f.write('{"sequence": 3, "previous_hash": "x", "entry_hash": "y"}\n')
            self.assertFalse(ledger.verify()[0])
            artifact, spec = artifacts()[0]
            with self.assertRaises(ValueError):
                ledger.append(artifact, spec['screen_id'], spec['version'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
