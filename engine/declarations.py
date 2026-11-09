#!/usr/bin/env python3
"""
Declarations Module

Everything the patterns used by one generation declare outside their JSX: imports,
module-level code, handlers, effects and state variables. Merged once per key.

Rule: the same key with the same code is emitted once; the same key with different
code is refused. Nothing is ever silently overwritten by the last use (defect D-19).

Pipeline Position:
    ComponentMapper -> [Declarations] -> assembled file sections

Copyright (c) 2026 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

from typing import Any, Dict, Iterable, List, Set


class Declarations:
    """Merged declarations of one generation, in first-use order."""

    def __init__(self, base_module: Dict[str, str] = None):
        self.imports: Dict[str, Set[str]] = {}
        self.module: Dict[str, str] = dict(base_module or {})     # the target's own blocks come first and win
        self.handlers: Dict[str, str] = {}
        self.effects: List[str] = []
        self.state: Dict[str, str] = {}                           # variable -> full right-hand side of its useState
        self.references: Set[str] = set()                         # handler names that must exist (stubbed if nobody declares them)

    def add_pattern(self, pattern, origin: str) -> None:
        """The static declarations of a pattern record (identical on every use)."""
        self.add({'imports': pattern.imports, 'module': pattern.module, 'handlers': pattern.handlers,
                  'effects': pattern.effects}, origin)

    def add(self, declared: Dict[str, Any], origin: str) -> None:
        """One use's declarations. origin names the pattern and component for the refusal message."""
        for module, names in declared.get('imports', {}).items():
            self.imports.setdefault(module, set()).update(names)
        self._merge(self.module, declared.get('module', {}), 'module block', origin)
        self._merge(self.handlers, declared.get('handlers', {}), 'handler', origin)
        for code in declared.get('effects', []):
            if code not in self.effects:
                self.effects.append(code)
        self._merge(self.state, declared.get('state', {}), 'state variable', origin)
        self.references.update(declared.get('references', ()))

    @staticmethod
    def _merge(target: Dict[str, str], incoming: Dict[str, str], kind: str, origin: str) -> None:
        for key, code in incoming.items():
            if key in target and target[key] != code:
                raise ValueError(f'{kind} "{key}" is declared twice with different code ({origin})')
            target.setdefault(key, code)

    def state_names(self) -> Iterable[str]:
        return self.state.keys()
