#!/usr/bin/env python3
"""Build a zero-dependency local 3D GLB viewer and optionally serve/open it.

Usage:
  python scripts/build_preview_site.py export/character.glb --out export/preview --serve --open
  python scripts/build_preview_site.py export/character.glb --out export/preview

The HTML uses a bundled WebGL2 viewer, not a CDN. It supports ordinary GLB
meshes, base-color materials, JOINTS_0/WEIGHTS_0 (<=64 bones per skin), and
translation/rotation/scale animation clips. It is not a reference PBR renderer.
"""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import html
from pathlib import Path
import shutil
import sys
import webbrowser

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PREVIEW_FILES = ('index.html', 'style.css', 'viewer.js')


def build(model: Path, dest: Path):
    if not model.is_file():
        raise FileNotFoundError(f'GLB does not exist: {model}')
    if model.suffix.lower() != '.glb':
        raise ValueError('Web preview expects a self-contained binary glTF .glb')
    if dest.resolve() == model.resolve().parent:
        raise ValueError('Output directory must not be the same as model parent')
    tpl = SKILL / 'assets' / 'preview'
    dest.mkdir(parents=True, exist_ok=True)
    for filename in PREVIEW_FILES:
        if filename == 'index.html':
            label=html.escape(model.stem.replace('_',' ').replace('-',' '))
            content=(tpl / filename).read_text(encoding='utf-8').replace('Character preview</h1>',label+'</h1>')
            (dest / filename).write_text(content, encoding='utf-8')
        else:
            shutil.copy2(tpl / filename, dest / filename)
    shutil.copy2(model, dest / 'model.glb')
    result = {'model': model.name, 'model_bytes': model.stat().st_size,
              'site': str(dest.resolve()),
              'viewer': 'Standalone WebGL2 (no external runtime dependencies)',
              'limitations': [
                  'Requires HTTP for automatic model fetch. Local file import works without server where browser permits.',
                  'Does not implement every glTF extension, sparse accessor, PBR lighting or >64-joint skins.',
                  'Web preview does not certify animation poses, weight painting or performance on target devices.',
              ]}
    (dest / 'preview_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def serve(dest: Path, host: str, port: int, open_browser=False):
    handler = partial(SimpleHTTPRequestHandler, directory=str(dest))
    class ReusableHTTP(ThreadingHTTPServer):
        allow_reuse_address=True
    with ReusableHTTP((host, port), handler) as http:
        url = f'http://localhost:{http.server_address[1]}/'
        print('Preview URL:', url, flush=True)
        if open_browser:
            opened = webbrowser.open(url)
            if not opened:
                print('Could not auto-launch a browser. Open the URL above manually.', flush=True)
        try:
            http.serve_forever(poll_interval=.2)
        except KeyboardInterrupt:
            print('Preview server stopped.', flush=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('model', type=Path)
    p.add_argument('--out', type=Path, default=Path('preview'))
    p.add_argument('--serve', action='store_true', help='Serve generated site using localhost HTTP')
    p.add_argument('--open', action='store_true', help='Open default browser; requires --serve')
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8765, help='0 selects free ephemeral port')
    a = p.parse_args(argv)
    if a.open and not a.serve:
        p.error('--open requires --serve')
    try:
        result = build(a.model, a.out)
    except (ValueError, FileNotFoundError) as e:
        p.error(str(e))
    print(json.dumps(result, indent=2), flush=True)
    if a.serve:
        serve(a.out, a.host, a.port, a.open)


if __name__ == '__main__':
    main()
