#!/usr/bin/env python3
"""
Verify-Preview Module - headless Chrome render and visual diff.

Captures a built site at phone and desktop widths, and compares each capture
with a baseline when one exists, reporting the share of pixels that changed.

    python preview.py <build-dir> [--baseline <dir>] [--chrome <path>]

Copyright (c) 2025 Intelligent Cloud Lab Inc.
All rights reserved.

Author: Amit Sarkar
Version: 1.0.0
"""

import os
import subprocess
import sys
from typing import Dict, Optional

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
VIEWPORTS = (('mobile', 375, 812), ('desktop', 1280, 800))
CDP_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview_cdp.mjs')


def screenshot(index_html: str, out_png: str, width: int, height: int, chrome: str = CHROME) -> Dict[str, int]:
    """Full-page capture with device emulation (phone when width < 600). Returns the metrics."""
    import json
    mode = 'mobile' if width < 600 else 'desktop'
    env = dict(os.environ, CHROME=chrome)
    out = subprocess.run(['node', CDP_SCRIPT, os.path.abspath(index_html), out_png, str(width), str(height), mode],
                         check=True, capture_output=True, text=True, env=env).stdout
    return json.loads(out)


def capture(out_dir: str, chrome: str = CHROME) -> Dict[str, str]:
    """Write preview/<viewport>.png for each viewport; return the paths."""
    preview_dir = os.path.join(out_dir, 'preview')
    os.makedirs(preview_dir, exist_ok=True)
    paths = {}
    for name, width, height in VIEWPORTS:
        png = os.path.join(preview_dir, f'{name}.png')
        metrics = screenshot(os.path.join(out_dir, 'index.html'), png, width, height, chrome)
        if metrics['scrollWidth'] > width:
            print(f'  preview {name}: page overflows the viewport ({metrics["scrollWidth"]} > {width} px)')
        paths[name] = png
    return paths


def diff_ratio(a_png: str, b_png: str) -> float:
    """Share of pixels that differ between two captures (0.0 identical, 1.0 all)."""
    from PIL import Image, ImageChops

    a = Image.open(a_png).convert('RGB')
    b = Image.open(b_png).convert('RGB')
    if a.size != b.size:
        return 1.0
    bbox_image = ImageChops.difference(a, b).convert('L').point(lambda v: 255 if v else 0)
    changed = sum(1 for v in bbox_image.getdata() if v)
    return changed / float(a.size[0] * a.size[1])


def compare(paths: Dict[str, str], baseline_dir: Optional[str]) -> Dict[str, Optional[float]]:
    """Compare each capture with baseline_dir/<viewport>.png when present."""
    result: Dict[str, Optional[float]] = {}
    for name, png in paths.items():
        base = os.path.join(baseline_dir, f'{name}.png') if baseline_dir else None
        result[name] = diff_ratio(base, png) if base and os.path.exists(base) else None
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python preview.py <build-dir> [--baseline <dir>] [--chrome <path>]')
        sys.exit(1)
    argv = sys.argv
    chrome = argv[argv.index('--chrome') + 1] if '--chrome' in argv else CHROME
    baseline = argv[argv.index('--baseline') + 1] if '--baseline' in argv else None
    captured = capture(argv[1], chrome)
    diffs = compare(captured, baseline)
    for name, png in captured.items():
        ratio = diffs[name]
        note = 'no baseline' if ratio is None else f'{ratio * 100:.3f}% pixels changed vs baseline'
        print(f'  {name:8s} {png}  ({note})')
