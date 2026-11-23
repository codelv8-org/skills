#!/usr/bin/env python3
"""Build a dependency-free reference/GLB stage review site from explicit inputs.

Examples:
  python scripts/build_stage_preview.py --model head.glb --previous old-head.glb \
    --reference-dir reference-head-crops --source-sheet source.png \
    --renders-dir qa-renders --qa qa.json --qa-report qa-report.html \
    --review-content review-content.json --out export/head-review

Optional review-content.json keys: focus and stateNotes (arrays of objects with
title and description), note, currentDescription, and previousDescription.
These are display text only and cannot override the canonical review status.

Only input artifacts are copied to the destination; private project data is never
written into the installed skill. Static evaluated opaque GLB meshes are expected.
WebGL is preferred; Canvas 2D software 3D keeps orbit/zoom available when WebGL
cannot initialize. Browser validation remains required; this command does not
approve likeness or GPU performance.
"""
from __future__ import annotations

import argparse
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
import struct
import webbrowser

SKILL = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL / 'assets' / 'stage-preview'
PREVIEW_FILES = ('index.html', 'style.css', 'viewer.js', 'gltf-viewer.js')
VIEWS = ('front', 'right', 'back', 'left')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
REPORT_CSP = "default-src 'none'; img-src data:; style-src 'unsafe-inline'; font-src data:; base-uri 'none'; form-action 'none'"


class ReportHTML(HTMLParser):
    """Require one static, self-contained report; never resolve linked assets."""

    def __init__(self):
        super().__init__()
        self.head_end = None
        self.in_style = False

    @staticmethod
    def check_css(value: str) -> None:
        if re.search(r'@import\b', value, re.I):
            raise ValueError('QA report must inline its CSS instead of using @import')
        for url in re.findall(r'url\(\s*[\'"]?([^\)\'"]+)', value, re.I):
            if not url.strip().lower().startswith(('data:', '#')):
                raise ValueError('QA report CSS must use embedded data URLs, not linked assets')

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attributes = dict(attrs)
        if tag in ('script', 'iframe', 'frame', 'frameset', 'object', 'embed', 'base', 'form'):
            raise ValueError(f'QA report must be static HTML; <{tag}> is not supported')
        if tag == 'meta' and (attributes.get('http-equiv') or '').lower() == 'refresh':
            raise ValueError('QA report must not redirect or refresh the page')
        if tag == 'head' and self.head_end is None:
            line, column = self.getpos()
            self.head_end = (line, column + len(self.get_starttag_text()))
        self.in_style |= tag == 'style'
        for name, value in attrs:
            value = value or ''
            if name.startswith('on') or name == 'srcdoc':
                raise ValueError('QA report must not contain executable HTML attributes')
            if name == 'style':
                self.check_css(value)
            if name == 'srcset':
                raise ValueError('QA report must use one embedded image src instead of srcset')
            if name in ('src', 'poster', 'background', 'xlink:href') or (name == 'href' and tag != 'a'):
                if value and not value.strip().lower().startswith(('data:', '#')):
                    raise ValueError('QA report must embed its images, fonts, and styles; linked assets are not copied')
            if name == 'href' and tag == 'a' and value:
                if not value.strip().lower().startswith(('#', 'https://', 'http://', 'mailto:')):
                    raise ValueError('QA report links must be page anchors or explicit HTTP(S)/mailto links')

    def handle_endtag(self, tag: str) -> None:
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.check_css(data)


def read_qa_report(path: Path | None) -> str | None:
    if path is None:
        return None
    existing_file(path, 'QA HTML report')
    if path.suffix.lower() not in ('.html', '.htm'):
        raise ValueError('--qa-report requires one self-contained .html or .htm file')
    markup = path.read_text(encoding='utf-8')
    parser = ReportHTML()
    parser.feed(markup)
    parser.close()
    if parser.head_end is None:
        raise ValueError('QA report must contain a <head> element')
    # The first policy also blocks any network dependency missed by the static
    # checks. Later report policies cannot relax it; user-clicked links still work.
    policy = f'<meta http-equiv="Content-Security-Policy" content="{REPORT_CSP}">'
    line, column = parser.head_end
    insert_at = sum(len(row) + 1 for row in markup.split('\n')[:line - 1]) + column
    return markup[:insert_at] + '\n' + policy + markup[insert_at:]


def read_review_content(path: Path | None) -> dict:
    if path is None:
        return {}
    existing_file(path, 'Review content JSON')
    content = json.loads(path.read_text(encoding='utf-8'))
    text_keys = {'note', 'currentDescription', 'previousDescription'}
    list_keys = {'focus', 'stateNotes'}
    if not isinstance(content, dict) or set(content) - text_keys - list_keys:
        raise ValueError('Review content must be an object containing only focus, stateNotes, note, currentDescription, previousDescription')
    for key, value in content.items():
        if key in text_keys:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f'Review content {key} must be a nonempty text string')
        elif not isinstance(value, list) or any(
            not isinstance(item, dict) or set(item) != {'title', 'description'}
            or any(not isinstance(item[field], str) or not item[field].strip() for field in ('title', 'description'))
            for item in value
        ):
            raise ValueError(f'Review content {key} must be an array of objects with nonempty title and description strings')
    return content


def existing_file(path: Path | None, kind: str) -> Path | None:
    if path is not None and not path.is_file():
        raise ValueError(f'{kind} file does not exist: {path}')
    return path


def validate_glb(path: Path) -> dict:
    """Check container/JSON and report static-export risks without fabricating QA."""
    existing_file(path, 'GLB')
    if path.suffix.lower() != '.glb':
        raise ValueError(f'Expected a .glb file: {path}')
    data = path.read_bytes()
    if len(data) < 20 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
        raise ValueError(f'Invalid glTF 2.0 binary header: {path}')
    offset, document = 12, None
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated GLB chunk header')
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if length % 4 or offset + length > len(data):
            raise ValueError('Invalid GLB chunk length')
        if kind == 0x4E4F534A:
            document = json.loads(data[offset:offset + length])
        offset += length
    if not document:
        raise ValueError('GLB JSON chunk missing')
    nodes = document.get('nodes', [])
    if any('skin' in node for node in nodes):
        raise ValueError('Stage viewer needs a static evaluated export; apply skin deformation before exporting')
    if any(p.get('targets') for m in document.get('meshes', []) for p in m.get('primitives', [])):
        raise ValueError('Stage viewer needs morph targets applied before export')
    unsupported = set(document.get('extensionsRequired', [])) - {'KHR_materials_unlit'}
    if unsupported:
        raise ValueError(f'Unsupported required glTF extensions: {sorted(unsupported)}')
    if any(m.get('alphaMode', 'OPAQUE') != 'OPAQUE' for m in document.get('materials', [])):
        raise ValueError('Stage viewer currently requires opaque materials')
    return {'source': path.name, 'bytes': len(data), 'animations_present': bool(document.get('animations'))}


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)


def copy_views(source: Path | None, destination: Path, folder: str) -> dict:
    if source is None:
        return {}
    if not source.is_dir():
        raise ValueError(f'Image directory does not exist: {source}')
    result = {}
    for view in VIEWS:
        candidates = [source / f'{view}{ext}' for ext in IMAGE_EXTENSIONS]
        candidate = next((p for p in candidates if p.is_file()), None)
        if candidate:
            name = f'{view}{candidate.suffix.lower()}'
            copy_file(candidate, destination / folder / name)
            result[view] = f'./{folder}/{name}'
    if not result:
        raise ValueError(f'No front/right/back/left image files found in {source}')
    return result


def build(args: argparse.Namespace) -> dict:
    model_info = validate_glb(args.model)
    previous_info = validate_glb(args.previous) if args.previous else None
    content = read_review_content(getattr(args, 'review_content', None))
    qa_report = read_qa_report(getattr(args, 'qa_report', None))
    for name in ('source_sheet', 'qa', 'diagnostic_board'):
        existing_file(getattr(args, name), name.replace('_', ' '))
    if args.qa:
        with args.qa.open(encoding='utf-8') as handle:
            json.load(handle)
    out = args.out.resolve()
    if out == SKILL.resolve() or SKILL.resolve() in out.parents or out in SKILL.resolve().parents:
        raise ValueError('Output must not overwrite the installed skill or its parent directories')
    if out in [args.model.resolve(), args.previous.resolve() if args.previous else None]:
        raise ValueError('Output directory cannot be a source model file')
    out.mkdir(parents=True, exist_ok=True)
    for name in PREVIEW_FILES:
        copy_file(TEMPLATE / name, out / name)
    copy_file(args.model, out / 'head.glb')
    if args.previous:
        copy_file(args.previous, out / 'previous-head.glb')
    references = copy_views(args.reference_dir, out, 'reference')
    renders = copy_views(args.renders_dir, out, 'renders')
    source_sheet = None
    if args.source_sheet:
        if args.source_sheet.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError('Source sheet must be PNG, JPG, or WEBP')
        source_sheet = './reference/source' + args.source_sheet.suffix.lower()
        copy_file(args.source_sheet, out / source_sheet.removeprefix('./'))
    qa_url = None
    if args.qa:
        qa_url = './qa.json'
        copy_file(args.qa, out / 'qa.json')
    qa_report_url = None
    if qa_report is not None:
        qa_report_url = './qa-report.html'
        (out / 'qa-report.html').write_text(qa_report, encoding='utf-8')
    diagnostic = None
    if args.diagnostic_board:
        if args.diagnostic_board.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValueError('Diagnostic board must be PNG, JPG, or WEBP')
        diagnostic = './diagnostic-board' + args.diagnostic_board.suffix.lower()
        copy_file(args.diagnostic_board, out / diagnostic.removeprefix('./'))
    config = {
        'title': args.title, 'subtitle': args.subtitle, 'stage': args.stage.upper(),
        'stageTitle': args.stage_title, 'iteration': args.iteration, 'status': 'REVIEW_REQUIRED',
        'current': {'url': './head.glb', 'label': args.current_label, 'description': content.get('currentDescription', 'ต้นแบบโมเดลนิ่ง · รอตรวจความเหมือน'), 'tag': f'รุ่นปัจจุบัน / V{args.iteration}'},
        'previous': {'url': './previous-head.glb', 'label': args.previous_label, 'description': content.get('previousDescription', 'รุ่นก่อนหน้าสำหรับเทียบรูปทรง'), 'tag': 'รุ่นก่อนหน้า'} if args.previous else None,
        'references': references, 'referenceKind': args.reference_kind,
        'sourceSheet': source_sheet, 'renders': renders, 'qaUrl': qa_url, 'qaReportUrl': qa_report_url, 'diagnosticBoard': diagnostic,
        'cameraPresets': {'front': 0, 'right': args.side_angle, 'back': 180, 'left': -args.side_angle, 'three': args.three_angle},
        'approximateViews': args.approximate_views,
        'note': content.get('note', 'สถานะนี้ยังไม่รับรองความเหมือน โปรดตรวจทั้งด้านหน้า ด้านข้าง และด้านหลัง ก่อนผ่านไปทำส่วนถัดไป'),
        'stateNotes': content.get('stateNotes', []),
    }
    if 'focus' in content:
        config['focus'] = content['focus']
    (out / 'review-config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = {
        'schema': 'stage-preview/1.0', 'site': str(out), 'current': model_info, 'previous': previous_info,
        'status': 'REVIEW_REQUIRED', 'human_approved': False,
        'geometry_statistics_source': 'Browser parser counts selected-scene triangle primitives and vertex records from GLB',
        'camera_convention': 'glTF +Y up, +Z front; left/right are reference-defined negative/positive yaw',
        'renderer': 'Bundled WebGL 2 / WebGL 1 with Canvas 2D software 3D fallback; no network runtime dependencies',
        'limitations': ['Static evaluated opaque geometry only; no skin or morph deformation', 'Approximate studio lighting; no IBL, cast shadows, or normal-map shading', 'Software fallback uses per-pixel depth-tested opaque triangles and wireframe; flat lighting/vertex colors only; no GPU/PBR validation', 'Web preview is not human likeness approval or target-device performance validation'],
    }
    (out / 'preview_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True, type=Path)
    p.add_argument('--previous', type=Path)
    p.add_argument('--reference-dir', type=Path)
    p.add_argument('--source-sheet', type=Path)
    p.add_argument('--renders-dir', type=Path)
    p.add_argument('--qa', type=Path, help='Machine-readable QA JSON; remains separate from the human-readable report')
    p.add_argument('--qa-report', type=Path, help='One static self-contained HTML report with inline CSS/data images; no scripts or linked assets')
    p.add_argument('--review-content', type=Path, help='Display-only JSON: focus/stateNotes [{title,description}], note, currentDescription, previousDescription')
    p.add_argument('--diagnostic-board', type=Path)
    p.add_argument('--out', type=Path, default=Path('stage-review'))
    p.add_argument('--title', default='ตรวจรูปทรงศีรษะ')
    p.add_argument('--subtitle', default='เทียบภาพอ้างอิงกับโมเดล 3D เพื่อปรับรูปทรงก่อนผ่านขั้นตอนถัดไป')
    p.add_argument('--stage', default='HEAD')
    p.add_argument('--stage-title', default='ตรวจรูปทรงศีรษะ')
    p.add_argument('--iteration', default='02')
    p.add_argument('--current-label', default='โมเดลที่ปรับล่าสุด')
    p.add_argument('--previous-label', default='โมเดลรุ่นก่อนหน้า')
    p.add_argument('--reference-kind', default='ภาพอ้างอิงเฉพาะส่วน')
    p.add_argument('--side-angle', type=float, default=90.0, help='Reference-defined right = +yaw; left = -yaw in degrees')
    p.add_argument('--three-angle', type=float, default=-35.0)
    p.add_argument('--approximate-views', action='store_true', help='Label reference camera matching as approximate')
    p.add_argument('--serve', action='store_true')
    p.add_argument('--open', action='store_true')
    p.add_argument('--port', type=int, default=8765)
    a = p.parse_args(argv)
    if a.open and not a.serve:
        p.error('--open requires --serve')
    if not (0 < a.side_angle <= 180):
        p.error('--side-angle must be greater than 0 and at most 180')
    try:
        result = build(a)
    except (ValueError, OSError, json.JSONDecodeError, struct.error) as error:
        p.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if a.serve:
        server = ThreadingHTTPServer(('127.0.0.1', a.port), partial(SimpleHTTPRequestHandler, directory=str(a.out.resolve())))
        print(f'Preview URL: http://localhost:{server.server_address[1]}/', flush=True)
        if a.open:
            webbrowser.open(f'http://localhost:{server.server_address[1]}/')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
