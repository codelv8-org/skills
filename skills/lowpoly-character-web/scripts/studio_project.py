#!/usr/bin/env python3
"""Persist an agent-resolved Thai/English brief and assemble honest stage previews.

This is a deterministic project helper, NOT a natural-language parser, modeler,
art reviewer or production approval authority. Resolve whole user sentences to
request JSON first. Run --help and references/thai-orchestration.md for usage.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

SKILL = Path(__file__).resolve().parents[1]
SCHEMA = 'lowpoly-studio/5.0'
DEFAULTS = {
    'title': 'ตัวละครใหม่', 'language': 'th', 'style': 'STYLIZED_LOW_POLY',
    'detail': 'BALANCED', 'character_type': 'UNSPECIFIED', 'height_m': None,
    'rig': 'STATIC', 'clips': [], 'device': 'UNSPECIFIED', 'actor_count': 1,
    'runtime_tier': 'NPC', 'constraints': [], 'must_match': [], 'source_files': [],
}
ENUMS = {
    'language': {'th', 'en'}, 'detail': {'LOW', 'BALANCED', 'HIGH'},
    'rig': {'STATIC', 'DEFORMABLE_SKINNED', 'SEGMENTED_RIGID'},
    'device': {'UNSPECIFIED', 'MOBILE', 'DESKTOP', 'MIXED'},
    'runtime_tier': {'HERO', 'NPC', 'CROWD'},
}
ALIASES = {
    'language': {'ไทย': 'th', 'ภาษาไทย': 'th', 'อังกฤษ': 'en'},
    'detail': {'สมดุล': 'BALANCED', 'ต่ำ': 'LOW', 'สูง': 'HIGH'},
    'device': {'มือถือ': 'MOBILE', 'เดสก์ท็อป': 'DESKTOP', 'ทั้งสอง': 'MIXED'},
    'rig': {'นิ่ง': 'STATIC', 'สกิน': 'DEFORMABLE_SKINNED', 'แยกชิ้น': 'SEGMENTED_RIGID'},
}
THAI_DIGITS = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
DOMAINS = {'intake', 'shape', 'rig', 'animation', 'runtime', 'browser'}
STAGE_NAMES = ['HEAD', 'TORSO', 'ARMS_HANDS', 'LEGS_FEET', 'OUTFIT_GEAR', 'INTEGRATION']


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_file(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f'ไม่พบไฟล์: {path}')
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def writable_project(path):
    path = Path(path).resolve()
    if path == SKILL or SKILL in path.parents or path in SKILL.parents:
        raise ValueError('เก็บโครงการนอกโฟลเดอร์ skill / Project must be outside installed skill')
    return path


def load(project):
    project = Path(project).resolve()
    brief, state = read(project / 'studio_brief.json'), read(project / 'studio_state.json')
    if brief.get('schema') != SCHEMA or state.get('schema') != SCHEMA:
        raise ValueError('Unsupported studio schema; migrate explicitly')
    return brief, state


def history(project, event):
    with (project / 'studio_history.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'at': now(), **event}, ensure_ascii=False) + '\n')


def normalized(changes, base):
    if not isinstance(changes, dict) or set(changes) - set(DEFAULTS):
        raise ValueError('changes ต้องเป็น object และใช้เฉพาะ key ของบรีฟที่รองรับ')
    result = deepcopy(changes)
    for key, value in result.items():
        if key in ENUMS:
            if not isinstance(value, str):
                raise ValueError(f'{key}: expected text enum')
            value = ALIASES.get(key, {}).get(value, value.lower() if key == 'language' else value.upper())
            if value not in ENUMS[key]:
                raise ValueError(f'{key}: expected one of {sorted(ENUMS[key])}')
        elif key in {'actor_count', 'height_m'}:
            if value is None and key == 'height_m':
                pass
            else:
                if isinstance(value, bool):
                    raise ValueError(f'{key}: expected positive number')
                try:
                    value = float(str(value).translate(THAI_DIGITS))
                except (ValueError, TypeError):
                    raise ValueError(f'{key}: expected positive number')
                if not math.isfinite(value) or value <= 0:
                    raise ValueError(f'{key}: expected positive finite number')
                if key == 'actor_count':
                    if value != int(value):
                        raise ValueError('actor_count ต้องเป็นจำนวนเต็ม')
                    value = int(value)
        elif key in {'clips', 'constraints', 'must_match', 'source_files'}:
            if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                raise ValueError(f'{key}: expected list of nonempty strings; [] explicitly clears')
            if len(set(value)) != len(value):
                raise ValueError(f'{key}: duplicate values')
            if key == 'source_files':
                value = [record_file(base / item) for item in value]
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f'{key}: expected nonempty text')
        result[key] = value
    return result


def request_data(path):
    path = Path(path).resolve()
    request = read(path)
    if not isinstance(request, dict) or set(request) - {'raw_text', 'intent', 'changes', 'provenance'}:
        raise ValueError('Request keys: raw_text, intent, changes, provenance (optional)')
    if not isinstance(request.get('raw_text'), str) or not request['raw_text'].strip():
        raise ValueError('raw_text must preserve the original request')
    if request.get('intent') not in {'create', 'continue', 'refine', 'update', 'restart'}:
        raise ValueError('intent: create / continue / refine / update / restart')
    changes = normalized(request.get('changes', {}), path.parent)
    provenance = request.get('provenance', {})
    if not isinstance(provenance, dict) or set(provenance) - set(changes):
        raise ValueError('provenance keys must occur in changes')
    if any(value not in {'USER', 'PROJECT', 'ASSUMED'} for value in provenance.values()):
        raise ValueError('provenance values: USER / PROJECT / ASSUMED')
    return request, changes, provenance


def affected(changed):
    domains = set()
    if set(changed) & {'source_files', 'style', 'detail', 'character_type', 'height_m', 'constraints', 'must_match'}:
        domains |= DOMAINS
    if set(changed) & {'device', 'actor_count', 'runtime_tier'}:
        domains |= {'runtime', 'browser'}
    if 'clips' in changed:
        domains |= {'animation', 'runtime', 'browser'}
    if 'rig' in changed:
        domains |= {'rig', 'animation', 'runtime', 'browser'}
    return sorted(domains)


def apply_request(brief, state, path):
    request, changes, provenance = request_data(path)
    new_brief, new_state = deepcopy(brief), deepcopy(state)
    changed = [key for key, value in changes.items() if new_brief['values'].get(key) != value]
    for key, value in changes.items():
        new_brief['values'][key] = value
        new_brief['provenance'][key] = {'source': provenance.get(key, 'USER'), 'request': request['raw_text'], 'at': now()}
    values = new_brief['values']
    if values['rig'] == 'STATIC' and values['clips']:
        raise ValueError('มี clips แต่ rig เป็น STATIC: ให้ agent ระบุ rig ให้ตรงเจตนา โดยไม่ถามผู้ใช้ซ้ำ')
    invalidated = affected(changed)
    new_state['invalidated_domains'] = sorted(set(state.get('invalidated_domains', [])) | set(invalidated))
    if 'intake' in invalidated:
        new_state['intake'] = None
    if 'shape' in invalidated:
        # Old evidence remains on disk. It cannot silently approve a new brief.
        new_state['shape_brief_changed'] = True
    new_brief['updated_at'] = now()
    return new_brief, new_state, {'type': 'request', 'request': request, 'changed_fields': changed, 'invalidated_domains': invalidated}


def initialize_project(project, request, stage_project=None, reference_dir=None):
    from stage_pipeline import initialize
    project = writable_project(project)
    if (project / 'studio_brief.json').exists() or (project / 'studio_state.json').exists():
        raise FileExistsError('Project exists; use update / โครงการมีอยู่แล้ว ให้ใช้ update')
    stage_project = Path(stage_project).resolve() if stage_project else project / 'stages_project'
    if stage_project.exists() and not (stage_project / 'project.json').is_file():
        raise ValueError('stage-project exists without project.json')
    brief = {'schema': SCHEMA, 'created_at': now(), 'values': deepcopy(DEFAULTS),
             'provenance': {key: {'source': 'ASSUMED', 'reason': 'ค่าเริ่มต้นชั่วคราว ปรับได้จากบริบท'} for key in DEFAULTS}}
    state = {'schema': SCHEMA, 'stage_project': str(stage_project), 'intake': None,
             'shape_brief_changed': False, 'invalidated_domains': sorted(DOMAINS),
             'current': None, 'previous': None, 'checkpoints': [], 'scope': 'Project cache; never approval authority'}
    brief, state, event = apply_request(brief, state, request)
    # Initial/adopted brief is the baseline; intake binds its sources before work.
    state['shape_brief_changed'] = False
    project.mkdir(parents=True, exist_ok=True)
    if not (stage_project / 'project.json').is_file():
        initialize(stage_project, Path(reference_dir) if reference_dir else None)
    write(project / 'studio_brief.json', brief)
    write(project / 'studio_state.json', state)
    history(project, {'type': 'init', 'adopted_stage_project': bool(stage_project and stage_project != project / 'stages_project')})
    history(project, event)
    return plan(project)


def update(project, request):
    project = writable_project(project)
    brief, state = load(project)
    brief, state, event = apply_request(brief, state, request)
    if event['request']['intent'] == 'restart':
        raise ValueError('เริ่มใหม่ต้องใช้ restart --out โครงการใหม่ เพื่อเก็บงานเดิม')
    write(project / 'studio_brief.json', brief)
    write(project / 'studio_state.json', state)
    history(project, event)
    return plan(project)


def stale_files(brief):
    return [item['path'] for item in brief['values']['source_files']
            if not Path(item['path']).is_file() or sha(item['path']) != item['sha256']]


def intake(project, manifest):
    project = writable_project(project)
    brief, state = load(project)
    manifest = Path(manifest).resolve()
    content = read(manifest)
    if not isinstance(content, dict) or not isinstance(content.get('views'), list) or not content['views']:
        raise ValueError('intake manifest requires nonempty views list')
    if any(not isinstance(content.get(key), str) or not content[key].strip() for key in ('layout_notes', 'proportion_notes', 'camera_notes')):
        raise ValueError('intake requires layout_notes, proportion_notes, camera_notes')
    observed = {item['sha256'] for item in brief['values']['source_files']}
    if set(content.get('source_sha256', [])) != observed or stale_files(brief):
        raise ValueError('Intake must bind the exact current source hashes')
    names = set()
    for view in content['views']:
        if not isinstance(view, dict) or not isinstance(view.get('name'), str) or view['name'] in names:
            raise ValueError('Each intake view needs a unique name')
        names.add(view['name'])
        if view.get('basis') not in {'OBSERVED', 'INFERRED', 'UNKNOWN'} or not isinstance(view.get('notes'), str):
            raise ValueError('View requires basis OBSERVED/INFERRED/UNKNOWN and notes')
        crop = view.get('crop_px')
        if crop is not None and (not isinstance(crop, list) or len(crop) != 4 or
             any(type(x) is not int or x < 0 for x in crop) or crop[2] <= crop[0] or crop[3] <= crop[1]):
            raise ValueError('crop_px must be a nonempty pixel rectangle; no automatic cropping')
    state['intake'] = record_file(manifest)
    state['intake']['scope'] = 'Agent source reading; not camera or likeness approval'
    state['invalidated_domains'] = [x for x in state['invalidated_domains'] if x != 'intake']
    write(project / 'studio_state.json', state)
    history(project, {'type': 'intake', 'manifest': state['intake']})
    return plan(project)


def plan(project):
    from stage_pipeline import status_message
    brief, state = load(project)
    values = brief['values']
    stale = stale_files(brief)
    item = state.get('intake')
    intake_ok = bool(item and Path(item['path']).is_file() and sha(item['path']) == item['sha256'] and not stale)
    stages = status_message(Path(state['stage_project']))
    next_stage = stages['next_allowed_stage']
    if state.get('shape_brief_changed'):
        next_stage = 'HEAD'
    next_action = 'G0_REFERENCE_INTAKE' if not intake_ok else (next_stage or 'G2_TO_G7_PRODUCTION_QA')
    current = state.get('current')
    current_stale = bool(current and (not Path(current['model']['path']).is_file() or sha(current['model']['path']) != current['model']['sha256']))
    return {
        'schema': SCHEMA, 'title': values['title'], 'language': values['language'],
        'brief': values, 'assumed_fields': [key for key, item in brief['provenance'].items() if item['source'] == 'ASSUMED'],
        'next_action': next_action, 'next_allowed_stage': next_stage,
        'stage_status': stages['stage_status'], 'stale_source_files': stale,
        'current_artifact_changed': current_stale, 'invalidated_domains': state['invalidated_domains'],
        'clip_qa': 'NOT_APPLICABLE' if not values['clips'] else 'REQUIRED',
        'deformation_qa': 'REQUIRED' if values['rig'] == 'DEFORMABLE_SKINNED' else 'NOT_APPLICABLE',
        'runtime_status': 'NOT_TESTED', 'production_status': 'NOT_APPROVED_BY_THIS_HELPER',
        'preview': current.get('preview') if current else None,
        'message_th': ('อ่านและบันทึกภาพอ้างอิงก่อนเริ่มปรับรูปทรง' if not intake_ok else
                       f'ทำต่อที่ {next_stage} ตามหลักฐานล่าสุด ห้ามข้ามส่วนที่ยังไม่ผ่าน' if next_stage else
                       'ส่วนรูปทรงผ่านแล้ว ยังต้องตรวจ rig / animation / LOD / runtime / browser ตามบรีฟ'),
        'notice_th': 'ค่าเริ่มต้นและสถิติโมเดลไม่ใช่การรับรองความเหมือนหรือ FPS; ต้องตรวจหลักฐานจริง',
    }


def restart(project, out, request=None):
    project, out = Path(project).resolve(), writable_project(out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Restart output must be a new empty project')
    brief, _ = load(project)
    values = deepcopy(brief['values'])
    values['source_files'] = [x['path'] for x in values['source_files']]
    # Read changes before writing anything; retain original raw user request.
    extra, _, _ = request_data(request) if request else ({'raw_text': 'เริ่มใหม่ ใช้บรีฟเดิม', 'changes': {}}, {}, {})
    values.update(extra.get('changes', {}))
    if 'source_files' in extra.get('changes', {}):
        values['source_files'] = [str((Path(request).resolve().parent / x).resolve()) for x in extra['changes']['source_files']]
    explicit = extra.get('changes', {})
    provenance = {key: (extra.get('provenance', {}).get(key, 'USER') if key in explicit
                        else brief['provenance'][key]['source']) for key in values}
    payload = {'raw_text': extra['raw_text'], 'intent': 'create', 'changes': values,
               'provenance': provenance}
    out.mkdir(parents=True, exist_ok=True)
    seed = out / 'restart_request.json'
    write(seed, payload)
    initialize_project(out, seed)
    new_brief, _ = load(out)
    for key in values:
        if key not in explicit:
            new_brief['provenance'][key] = {**deepcopy(brief['provenance'][key]), 'inherited_from': str(project)}
    write(out / 'studio_brief.json', new_brief)
    history(out, {'type': 'restart', 'previous_project': str(project), 'request': extra,
                  'inherited_fields': [key for key in values if key not in explicit],
                  'gate_approvals_copied': False})
    return plan(out)


def checkpoint(project, model, stage, renders_dir, preview_out=None, qa=None,
               reference_dir=None, source_sheet=None, qa_report=None, review_content=None,
               diagnostic_board=None, side_angle=90, three_angle=-35, approximate_views=False,
               stage_project=None):
    from part_fidelity import _validate_mesh_snapshot
    from stage_pipeline import status_message, _directory
    project = writable_project(project)
    brief, state = load(project)
    if stage not in STAGE_NAMES:
        raise ValueError('Unsupported stage')
    model = Path(model).resolve()
    _validate_mesh_snapshot(model)
    model_info = record_file(model)
    renders_dir = Path(renders_dir).resolve()
    if not renders_dir.is_dir():
        raise ValueError('Actual reimport renders directory is required')
    if qa:
        qa = Path(qa).resolve()
        report = read(qa)
        if report.get('model_sha256') != model_info['sha256']:
            raise ValueError('QA must bind this actual GLB using model_sha256')
    else:
        qa = project / 'evidence' / model_info['sha256'] / 'structural_qa.json'
        from inspect_character_glb import inspect
        tier = brief['values']['runtime_tier']
        report = inspect(model, profile={'HERO': 'balanced', 'NPC': 'mobile', 'CROWD': 'icon'}[tier])
        report = {'model_sha256': model_info['sha256'], 'structural_inspection': report,
                  'fidelity_status': 'NOT_TESTED', 'runtime_status': 'NOT_TESTED',
                  'notice_th': 'ตรวจโครงสร้างไฟล์เท่านั้น ยังไม่รับรองความเหมือนหรือประสิทธิภาพ'}
        write(qa, report)
    if stage_project:
        state['stage_project'] = str(Path(stage_project).resolve())
    stage_root = Path(state['stage_project'])
    actual = status_message(stage_root)
    next_stage = 'HEAD' if state.get('shape_brief_changed') else actual['next_allowed_stage']
    if next_stage and STAGE_NAMES.index(stage) > STAGE_NAMES.index(next_stage):
        raise ValueError(f'ห้ามข้ามด่าน {next_stage} ไป {stage}')
    old = state.get('current')
    same = old and old['model']['sha256'] == model_info['sha256']
    previous = state.get('previous') if same else old
    if previous and (not Path(previous['model']['path']).is_file() or sha(previous['model']['path']) != previous['model']['sha256']):
        raise ValueError('Previous model changed; restore its immutable snapshot before comparing')
    count = len(state['checkpoints']) + (0 if same else 1)
    out = Path(preview_out).resolve() if preview_out else project / 'preview'
    command = [sys.executable, str(SKILL / 'scripts/build_stage_preview.py'), '--model', str(model),
               '--renders-dir', str(renders_dir), '--qa', str(qa), '--out', str(out), '--stage', stage,
               '--stage-title', f'ตรวจรูปทรง · {stage}', '--title', brief['values']['title'],
               '--iteration', str(count), '--side-angle', str(side_angle), '--three-angle', str(three_angle)]
    if previous:
        command += ['--previous', previous['model']['path']]
    for key, value in [('reference-dir', reference_dir), ('source-sheet', source_sheet), ('qa-report', qa_report),
                       ('review-content', review_content), ('diagnostic-board', diagnostic_board)]:
        if value:
            command += ['--' + key, str(Path(value).resolve())]
    if approximate_views:
        command.append('--approximate-views')
    built = subprocess.run(command, capture_output=True, text=True)
    if built.returncode:
        raise ValueError('Preview build failed: ' + (built.stderr or built.stdout).strip())
    # Only invalidate/bind the stage after all preview inputs were accepted.
    # Existing gates remain hash-bound and are never rewritten to PASS here.
    target = _directory(stage_root, stage) / 'model.glb'
    if model != target.resolve():
        shutil.copy2(model, target)
    if state.get('shape_brief_changed'):
        for candidate in stage_root.glob('stages/*/gate.json'):
            archive = candidate.with_name('gate.before-brief-change.' + sha(candidate)[:12] + '.json')
            if not archive.exists():
                shutil.copy2(candidate, archive)
            candidate.unlink()
        state['shape_brief_changed'] = False
    entry = {'at': now(), 'stage': stage, 'model': model_info, 'qa': record_file(qa),
             'renders': {p.name: record_file(p) for p in sorted(renders_dir.iterdir()) if p.suffix.lower() in {'.png', '.jpg', '.webp'}},
             'preview': str(out), 'browser_status': 'NOT_TESTED', 'fidelity_status': 'REVIEW_REQUIRED'}
    state['previous'], state['current'] = previous, entry
    if not same:
        state['checkpoints'].append(entry)
    state['invalidated_domains'] = sorted(set(state['invalidated_domains']) |
        ({'shape', 'rig', 'animation', 'runtime', 'browser'} if not same else {'browser'}))
    write(project / 'studio_state.json', state)
    history(project, {'type': 'checkpoint', 'model_sha256': model_info['sha256'], 'stage': stage, 'preview': str(out)})
    return plan(project)


def preflight():
    candidates = [shutil.which('blender'), '/usr/bin/blender', '/opt/blender/blender']
    blender = next((x for x in candidates if x and Path(x).is_file()), None)
    version = None
    if blender:
        try:
            result = subprocess.run([blender, '--version'], capture_output=True, text=True, timeout=10, check=True)
            version = result.stdout.splitlines()[0]
        except (OSError, subprocess.SubprocessError, IndexError):
            blender = None
    return {'blender': blender, 'blender_version': version,
            'python': sys.executable, 'dependencies': {x: bool(importlib.util.find_spec(x)) for x in ('numpy', 'PIL')},
            'browser': 'AGENT_MUST_CHECK_AVAILABLE_TOOLS', 'paid_generation': 'NOT_STARTED',
            'message_th': 'ใช้เครื่องมือที่มีอยู่ก่อน การตรวจนี้ไม่ติดตั้งโปรแกรมหรือเรียกบริการเสียเงิน'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'update', 'plan', 'intake', 'checkpoint', 'restart', 'preflight'])
    parser.add_argument('--project', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--stage-project', type=Path, help='Adopt an existing genuine stage_pipeline project')
    parser.add_argument('--reference-dir', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--model', type=Path)
    parser.add_argument('--stage', choices=STAGE_NAMES, default='HEAD')
    parser.add_argument('--renders-dir', type=Path)
    parser.add_argument('--qa', type=Path)
    parser.add_argument('--qa-report', type=Path)
    parser.add_argument('--source-sheet', type=Path)
    parser.add_argument('--review-content', type=Path)
    parser.add_argument('--diagnostic-board', type=Path)
    parser.add_argument('--side-angle', type=float, default=90)
    parser.add_argument('--three-angle', type=float, default=-35)
    parser.add_argument('--approximate-views', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'preflight':
            result = preflight()
        else:
            if args.project is None:
                raise ValueError('--project required')
            if args.command in {'init', 'update'} and args.request is None:
                raise ValueError('--request required; agent resolves user intent first')
            if args.command == 'init':
                result = initialize_project(args.project, args.request, args.stage_project, args.reference_dir)
            elif args.command == 'update':
                result = update(args.project, args.request)
            elif args.command == 'plan':
                result = plan(args.project)
            elif args.command == 'intake':
                if args.manifest is None:
                    raise ValueError('--manifest required')
                result = intake(args.project, args.manifest)
            elif args.command == 'restart':
                if args.out is None:
                    raise ValueError('--out new directory required')
                result = restart(args.project, args.out, args.request)
            else:
                if args.model is None or args.renders_dir is None:
                    raise ValueError('--model and --renders-dir required')
                result = checkpoint(args.project, args.model, args.stage, args.renders_dir, args.out, args.qa,
                                    args.reference_dir, args.source_sheet, args.qa_report, args.review_content,
                                    args.diagnostic_board, args.side_angle, args.three_angle, args.approximate_views,
                                    args.stage_project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
