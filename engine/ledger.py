#!/usr/bin/env python3
"""
Ledger Module - the hash-chained generation log.

Every generation is recorded as an entry whose hash covers the previous entry's hash,
so the log cannot be edited or reordered without breaking the chain. The entry carries
no clock: it is a pure function of the previous hash and the artifact, which keeps the
ledger reproducible. The engine host signs entry_hash (a signature field is reserved;
verification of the chain ignores it); the consuming server verifies the signature,
recomputes the content hash of the code it received and compares both.

    entry = chain_entry(previous_hash, artifact, screen_id, spec_version, sequence)
    ok, detail = verify_chain(entries)

File access lives in the Ledger class only; the functions above are pure.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Tuple

GENESIS = '0' * 64
FIELDS = ('sequence', 'previous_hash', 'screen_id', 'spec_version', 'spec_key', 'content_hash',
          'pattern_lib_version', 'target', 'pattern_set')


def _canonical(entry: Dict[str, Any]) -> str:
    body = {k: entry[k] for k in FIELDS}
    return json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def entry_hash(entry: Dict[str, Any]) -> str:
    """sha256 over the previous hash and the canonical body of this entry."""
    material = entry['previous_hash'] + '\n' + _canonical(entry)
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


def chain_entry(previous_hash: str, artifact, screen_id: str, spec_version: str, sequence: int) -> Dict[str, Any]:
    """The next entry of the chain for one artifact. Pure."""
    entry = {
        'sequence': int(sequence),
        'previous_hash': previous_hash,
        'screen_id': screen_id,
        'spec_version': spec_version,
        'spec_key': artifact.spec_key,
        'content_hash': artifact.content_hash,
        'pattern_lib_version': artifact.pattern_lib_version,
        'target': artifact.target,
        'pattern_set': artifact.pattern_set,
    }
    entry['entry_hash'] = entry_hash(entry)
    return entry


def verify_chain(entries: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Every entry hashes to its recorded value and links to the one before it."""
    previous = GENESIS
    for index, entry in enumerate(entries):
        if entry.get('sequence') != index:
            return False, f'entry {index}: sequence {entry.get("sequence")} out of order'
        if entry.get('previous_hash') != previous:
            return False, f'entry {index}: previous_hash does not link to entry {index - 1}'
        try:
            expected = entry_hash(entry)
        except KeyError as missing:
            return False, f'entry {index}: field {missing} missing'
        if entry.get('entry_hash') != expected:
            return False, f'entry {index}: entry_hash does not match its content'
        previous = entry['entry_hash']
    return True, f'{len(entries)} entries verified'


class Ledger:
    """Append-only JSON lines file, one chain per file."""

    def __init__(self, path: str):
        self.path = path

    def entries(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]

    def head(self) -> str:
        entries = self.entries()
        return entries[-1]['entry_hash'] if entries else GENESIS

    def append(self, artifact, screen_id: str, spec_version: str) -> Dict[str, Any]:
        entries = self.entries()
        ok, detail = verify_chain(entries)
        if not ok:
            raise ValueError(f'ledger {self.path} is broken: {detail}')
        entry = chain_entry(self.head(), artifact, screen_id, spec_version, len(entries))
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, sort_keys=True, ensure_ascii=False) + '\n')
        return entry

    def verify(self) -> Tuple[bool, str]:
        return verify_chain(self.entries())


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print('Usage: python ledger.py <ledger.jsonl>   (verifies the chain)')
        sys.exit(1)
    ok, detail = Ledger(sys.argv[1]).verify()
    print(('LEDGER OK  ' if ok else 'LEDGER BROKEN  ') + detail)
    sys.exit(0 if ok else 2)
