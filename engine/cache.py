#!/usr/bin/env python3
"""
Deterministic Cache Module (step 7 of the determinism sequence, local tier).

Content-addressed store keyed by spec_key = sha256(canonical(spec) + pattern
library version + target). Because generation is a pure function, a hit is
exactly what a fresh generation would produce; the key is trusted only because
the GA-5 gate is green. The edge and parent tiers of the design wrap this same
interface later.

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import json
import os
from typing import Any, Dict, Optional

from generate import Artifact

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build', '.cache')


class ArtifactCache:
    def __init__(self, directory: str = DEFAULT_DIR):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.directory, f'{key}.json')

    def get(self, key: str) -> Optional[Artifact]:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data: Dict[str, Any] = json.load(f)
        return Artifact(**data)

    def put(self, artifact: Artifact) -> str:
        path = self._path(artifact.spec_key)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(artifact.__dict__, f, sort_keys=True, ensure_ascii=False)
        return path

    def stats(self) -> Dict[str, int]:
        return {'entries': len([n for n in os.listdir(self.directory) if n.endswith('.json')])}
