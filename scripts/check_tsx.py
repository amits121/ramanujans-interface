#!/usr/bin/env python3
"""
Type-check generated files: generate each specification for its target, write the files into a
scratch folder inside the static shell (which holds the TypeScript compiler and the React types)
and run the compiler in strict mode with no emit. A failure is a defect in a pattern, never in
the specification author's hands: generated code must compile as emitted.

    python scripts/check_tsx.py engine/specs/login-flow.yaml:react-static engine/specs/project-list.yaml:react-static

Targets whose component framework is not installed in the shell are skipped with a note.
Tooling only: generation itself stays pure inside engine/generate.py.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, 'engine')
SHELL = os.path.join(ROOT, 'scripts', 'static-shell')
SCRATCH = os.path.join(SHELL, '.typecheck')
sys.path.insert(0, ENGINE)

from generate import generate  # noqa: E402
from spec_parser import SpecParser  # noqa: E402

CHECKABLE = ('react-static',)   # targets whose imports resolve inside the shell's node_modules

TSCONFIG = {
    'compilerOptions': {
        'target': 'ES2020', 'lib': ['ES2020', 'DOM', 'DOM.Iterable'], 'module': 'ESNext',
        'moduleResolution': 'bundler', 'jsx': 'react-jsx', 'strict': True, 'skipLibCheck': True,
        'noEmit': True, 'isolatedModules': True, 'esModuleInterop': True, 'allowSyntheticDefaultImports': True,
        'types': ['react', 'react-dom'], 'typeRoots': ['../node_modules/@types'],
    },
    'include': ['*.tsx'],
}


def main(args):
    tsc = os.path.join(SHELL, 'node_modules', '.bin', 'tsc')
    if not os.path.exists(tsc):
        sys.exit('tsc not installed: run npm install in scripts/static-shell first')
    shutil.rmtree(SCRATCH, ignore_errors=True)
    os.makedirs(SCRATCH)
    parser = SpecParser()
    written = []
    for arg in args:
        path, _, target = arg.partition(':')
        target = target or 'react-static'
        if target not in CHECKABLE:
            print(f'  skip   {os.path.basename(path)} ({target}: framework types not installed in the shell)')
            continue
        spec = parser.parse(path)
        artifact = generate(spec, target)
        name = ''.join(w.capitalize() for w in spec['screen_id'].split('-')) + '.tsx'
        with open(os.path.join(SCRATCH, name), 'w', encoding='utf-8') as f:
            f.write(artifact.code)
        written.append(name)
    if not written:
        print('nothing to check')
        return 0
    with open(os.path.join(SCRATCH, 'tsconfig.json'), 'w', encoding='utf-8') as f:
        json.dump(TSCONFIG, f, indent=2)
    result = subprocess.run([tsc, '-p', os.path.join(SCRATCH, 'tsconfig.json'), '--pretty', 'false'],
                            capture_output=True, text=True, cwd=SHELL)
    for name in written:
        print(f'  {"PASS" if result.returncode == 0 else "FAIL"}   {name}')
    if result.returncode != 0:
        print(result.stdout.strip())
        print(result.stderr.strip())
        print('TYPE CHECK FAIL')
        return 4
    print('TYPE CHECK PASS')
    shutil.rmtree(SCRATCH, ignore_errors=True)
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
