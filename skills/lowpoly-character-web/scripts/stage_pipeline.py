#!/usr/bin/env python3
"""Enforce Head -> Torso -> Arms/Hands -> Legs/Feet -> Outfit/Gear -> Integration.

Does NOT model geometry or auto-approve appearance. Each stage must present a
real saved mesh snapshot, camera-matched masked views, landmark annotations,
reviewer-rated visual evidence and a PASS report from part_fidelity.py.
Integration must re-pass ALL earlier parts against the final assembled model.

Usage:
  python scripts/stage_pipeline.py init --out character_project --reference-dir reference_pack
  python scripts/stage_pipeline.py next --project character_project
  python scripts/stage_pipeline.py evaluate --project character_project --stage HEAD
  python scripts/stage_pipeline.py status --project character_project
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from part_fidelity import evaluate, PART_CHECKS

STAGES=(
    ('HEAD',['cranium_and_jaw_shape','hair_volume_front_back_profiles','eyebrows_eyes_nose_ears','head_to_body_proportion'],.84,.09,5),
    ('TORSO',['shoulder_width_depth','neck_chest_waist_ratios','uniform_hem_collar','side_and_back_torso'],.82,.10,3),
    ('ARMS_HANDS',['upper_arm_forearm_lengths','shoulder_elbow_wrist_position','hand_palm_thumb_fingers','sleeve_cuffs'],.78,.12,4),
    ('LEGS_FEET',['thigh_shin_proportions','hip_knee_ankle_alignment','shoe_silhouette_profiles','foot_ground_contact'],.80,.11,4),
    ('OUTFIT_GEAR',['badge_belt_positions','shoulder_bag_side_and_depth','strap_path_front_back','faceted_garment_language'],.76,.13,2),
    ('INTEGRATION',['total_character_silhouette','neck_shoulder_hip_seams','ref_landmark_consistency','visible_face_and_gear'],.84,.09,5),
)
VIEWS=('front','back','left','right')


def _dump(path: Path, data: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def _safe_name(stage: str) -> str:
    val=stage.upper()
    if val not in [s[0] for s in STAGES]:raise ValueError(f'Unknown stage {stage}')
    return val


def _directory(project:Path,stage:str):
    index=[s[0] for s in STAGES].index(stage)
    return project/'stages'/f'{index+1:02d}_{stage.lower()}'


def initialize(out:Path,reference_dir:Path|None=None):
    if (out/'project.json').exists():raise FileExistsError(f'Project already exists at {out}')
    out.mkdir(parents=True,exist_ok=True)
    refout=out/'reference';refout.mkdir(exist_ok=True)
    original_hashes={}
    for view in VIEWS:
        if reference_dir and (reference_dir/f'{view}.png').is_file():
            file=reference_dir/f'{view}.png'
            shutil.copyfile(file,refout/f'{view}.png')
            original_hashes[view]=hashlib.sha256(file.read_bytes()).hexdigest()
    _dump(out/'project.json',{
        'name':out.name,'version':'4.1','purpose':'Part-by-part modeled reference fidelity with hard gates',
        'stage_order':[s[0] for s in STAGES],
        'source_reference_sha256':original_hashes,
        'notices':['No automatic modeling, camera calibration or likeness judgement is implied',
                   'Do not advance if earlier part is not PASS',
                   'Integration must re-test all parts against the final assembled mesh',
                   'After integration still perform skin, animation and WebGL runtime acceptance'],
    })
    for idx,(name,checks,min_iou,max_err,nlandmarks) in enumerate(STAGES):
        checks=PART_CHECKS[name]
        base=_directory(out,name)
        (base/'renders').mkdir(parents=True,exist_ok=True)
        (base/'masks').mkdir(exist_ok=True)
        (base/'review').mkdir(exist_ok=True)
        sub='../..'
        asmt={
            'part':name,'model_asset':'model.glb','model_author':None,
            'required_views':list(VIEWS),
            'camera_calibration':{'verified':False,'projection':None,'method':None,
                                  'reference_basis':'OBSERVED_REFERENCE','diagnostic_only':False,
                                  'notice':'Reconcile source perspective and rendering camera before verifying'},
            'thresholds':{'min_silhouette_iou':min_iou,'max_bbox_size_error_ratio':max_err,
                          'max_bbox_center_error_ref_height':.07,
                          'max_mean_landmark_error_ref_height':.06,
                          'min_landmarks_total':nlandmarks},
            'views':{v:{
                 'reference_image':f'{sub}/reference/{v}.png',
                 'render_image':f'renders/{v}.png',
                 'reference_mask':f'{sub}/reference_masks/{name.lower()}/{v}.png',
                 'render_mask':f'masks/{v}.png',
                 'landmarks':{},
            } for v in VIEWS},
            'review':{'reviewer':None,'reviewer_type':None,'independent_from_author':False,
                  'approved':False,'notes':None,'render_model_sha256':None,'context_sha256':None,'weighted_min':4.3,
                  'checks':[{'id':x,'critical':True,'weight':5,'rating':None,
                             'evidence':'review/comparison.png','notes':None} for x in checks]}
        }
        _dump(base/'assessment.json',asmt)
        if name=='INTEGRATION':
            # Regression reports must be generated from current integrated GLB,
            # not copied from earlier isolated snapshots.
            _dump(base/'regression_manifest.json',{
                'source_model':'model.glb',
                'required_previous_stages':[s[0] for s in STAGES if s[0]!='INTEGRATION'],
                'regression_gate_paths':{s[0]:f'regression/{s[0].lower()}_gate.json' for s in STAGES[:-1]},
                'instruction':'Re-run each prior part_fidelity assessment using THIS integration model.glb, calibrated images/masks and new reviewer evidence.'
            })
            (base/'regression').mkdir(exist_ok=True)
    return out


def _hash_file(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _source_issues(project:Path):
    """Honor original reference hashes when a project was initialized from a pack."""
    config=json.loads((project/'project.json').read_text(encoding='utf-8'))
    hashes=config.get('source_reference_sha256',{})
    if not isinstance(hashes,dict):raise ValueError('Invalid source reference hash manifest')
    return [f'Original reference changed or missing: {view}' for view,expected in hashes.items()
            if view not in VIEWS or _hash_file(project/'reference'/f'{view}.png')!=expected]


def _assessment_issues(base:Path, stage:str, conf:dict):
    if not isinstance(conf,dict):return ['Assessment must be a JSON object']
    if conf.get('part')!=stage:return ['Assessment part does not match requested stage']
    model=conf.get('model_asset')
    if not isinstance(model,str) or (base/model).resolve()!=(base/'model.glb').resolve():
        return ['Stage must evaluate its own model.glb snapshot']
    return []


def _report_matches(report:dict, recomputed:dict):
    """A saved PASS is reproducible evidence, never an authority by itself."""
    keys=('part','status','assessment_path','assessment_sha256','model_asset','model_sha256',
          'evidence_sha256','view_metrics','camera_calibration','thresholds','reviewer_type',
          'reviewer','reviewer_approved','reviewer_weighted_rating_0to5','fidelity_scope',
          'review_context_sha256','required_review_context_sha256')
    return (bool(recomputed.get('evidence_sha256')) and
            all(key in report and report[key]==recomputed.get(key) for key in keys))


def read_gate(project:Path,stage:str):
    base=_directory(project,stage)
    gate=base/'gate.json'
    assessment=base/'assessment.json'
    if not gate.is_file():return {'part':stage,'status':'NOT_TESTED','reason':'No gate report created'}
    try:
        r=json.loads(gate.read_text(encoding='utf-8'))
        conf=json.loads(assessment.read_text(encoding='utf-8'))
        if not isinstance(r,dict):raise ValueError('Gate must be an object')
        issues=_source_issues(project)+_assessment_issues(base,stage,conf)
        if issues:return {'part':stage,'status':'REVIEW_REQUIRED','reason':'; '.join(issues)}
        if r.get('part')!=stage:
            return {'part':stage,'status':'REVIEW_REQUIRED','reason':'Report from wrong stage; re-evaluate'}
        if r.get('status')!='PASS':return r
        fresh=evaluate(assessment)
        if fresh.get('status')!='PASS' or not _report_matches(r,fresh):
            return {'part':stage,'status':'REVIEW_REQUIRED',
                    'reason':'Saved PASS cannot be reproduced from current model, assessment and complete evidence; re-evaluate'}
        if stage=='INTEGRATION' and r.get('status')=='PASS':
            issues=check_regressions(project,base,r.get('model_sha256'))
            if issues:
                return {'part':stage,'status':'REVIEW_REQUIRED','reason':'Integrated-part regression evidence changed/failed',
                        'regression_issues':issues}
        return r
    except (OSError,ValueError,KeyError,TypeError,AttributeError):
        return {'part':stage,'status':'BLOCKED','reason':'Invalid gate/assessment JSON'}


def all_status(project:Path):
    return {x[0]:read_gate(project,x[0]) for x in STAGES}


def check_regressions(project:Path, integration_dir:Path, current_sha:str|None):
    """Recompute every prior part from *new integrated-model* visual evidence.

    Copying/editing old PASS reports cannot bypass this check. The fresh
    assessment and render images/masks must be inside integration workspace.
    """
    issues=[]
    manifest=integration_dir/'regression_manifest.json'
    if not manifest.is_file():return ['Missing integration regression manifest']
    try:
        man=json.loads(manifest.read_text(encoding='utf-8'))
        if not isinstance(man,dict) or not isinstance(man.get('regression_gate_paths'),dict):
            raise ValueError('Regression manifest must map expected stages to report paths')
    except (ValueError,OSError) as exc:
        return [f'Invalid integration regression manifest: {exc}']
    regression_root=(integration_dir/'regression').resolve()
    for stage in [s[0] for s in STAGES[:-1]]:
        assessment=regression_root/f'{stage.lower()}_assessment.json'
        try:
            report_path=man['regression_gate_paths'].get(stage)
            if not isinstance(report_path,str):raise ValueError('Missing regression gate path')
            path=(integration_dir/report_path).resolve()
            if not path.is_relative_to(regression_root):
                raise ValueError('Regression gate must be inside integration/regression/')
            if not assessment.is_file() or not path.is_file():
                issues.append(f'Missing fresh integrated-model assessment/gate for {stage}')
                continue
            config=json.loads(assessment.read_text(encoding='utf-8'))
            if not isinstance(config,dict) or config.get('part')!=stage:
                raise ValueError('Regression assessment part does not match expected stage')
            # The source model must be the integrated model, and new renders/masks
            # must not come from the already approved isolated part snapshots.
            model=(assessment.parent/config.get('model_asset','')).resolve()
            if model!=(integration_dir/'model.glb').resolve():
                issues.append(f'{stage}: regression is not referencing assembled model.glb')
                continue
            current_render_dir=(integration_dir/'regression').resolve()
            for view in config.get('required_views',[]):
                item=config.get('views',{}).get(view,{})
                for k in ('render_image','render_mask'):
                    name=item.get(k)
                    if not name or not (assessment.parent/name).resolve().is_relative_to(current_render_dir):
                        raise ValueError(f'{stage}.{view}.{k}: must be newly captured in integration/regression/')
            recomputed=evaluate(assessment)
            report=json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(report,dict) or report.get('part')!=stage:
                raise ValueError('Regression gate part does not match expected stage')
            if recomputed['status']!='PASS' or report.get('status')!='PASS':
                issues.append(f'{stage}: integrated geometry evidence not approved')
            if recomputed.get('model_sha256')!=current_sha or report.get('model_sha256')!=current_sha:
                issues.append(f'{stage}: score does not correspond to current integration model SHA')
            if not _report_matches(report,recomputed):
                issues.append(f'{stage}: score report/visual evidence modified or recycled from old stage')
        except (ValueError, OSError, KeyError, TypeError,AttributeError) as exc:
            issues.append(f'{stage}: regression invalid: {exc}')
    return issues


def run_stage(project:Path,stage:str):
    stage=_safe_name(stage)
    stages=[s[0] for s in STAGES]
    index=stages.index(stage)
    blockers=[name for name in stages[:index] if read_gate(project,name).get('status')!='PASS']
    base=_directory(project,stage)
    out=base/'gate.json'
    if blockers:
        r={'part':stage,'status':'BLOCKED','reason':'Previous stages not PASS; stop before modeling next part','blocked_by':blockers}
        return r  # do not replace stored evidence for a forbidden stage
    try:
        conf=json.loads((base/'assessment.json').read_text(encoding='utf-8'))
        issues=_source_issues(project)+_assessment_issues(base,stage,conf)
    except (ValueError,OSError,TypeError,AttributeError) as exc:
        issues=[f'Invalid project/stage assessment: {exc}']
    if issues:
        result={'part':stage,'status':'BLOCKED','reason':'; '.join(issues)}
        _dump(out,result)
        return result
    result=evaluate(base/'assessment.json',base/'review'/'comparison_board.png')
    if stage=='INTEGRATION':
        issues=check_regressions(project,base,result.get('model_sha256'))
        if issues:
            result['status']='REVIEW_REQUIRED' if result['status']=='PASS' else result['status']
            result['regression_issues']=issues
    _dump(out,result)
    return result


def status_message(project:Path):
    results=all_status(project)
    eligible=next((stage for stage,r in results.items() if r.get('status')!='PASS'),None)
    return {'stage_status':{name:{'status':r['status'],'reason':r.get('reason'),'failures':r.get('failures'),
                                  'regression_issues':r.get('regression_issues')} for name,r in results.items()},
            'next_allowed_stage':eligible,
            'shape_stages_approved':eligible is None,
            'modeling_is_finished':eligible is None,
            'scope_notice':'modeling_is_finished refers only to shape stages; it is not production, rig or runtime approval',
            'post_stage_obligations':['deformation pose QA','skin/clip QA','LOD WebGL crowd QA','browser preview QA']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['init','evaluate','status','next'])
    p.add_argument('--project',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--reference-dir',type=Path)
    p.add_argument('--stage',choices=[s[0] for s in STAGES])
    a=p.parse_args()
    if a.command=='init':
        if not a.out:p.error('init requires --out')
        initialize(a.out,a.reference_dir)
        print(json.dumps({'created':str(a.out),'next_allowed_stage':'HEAD'},ensure_ascii=False))
        return
    if not a.project or not (a.project/'project.json').is_file():p.error('Valid --project required')
    if a.command=='evaluate':
        if not a.stage:p.error('evaluate requires --stage')
        result=run_stage(a.project,a.stage)
        print(json.dumps(result,indent=2,ensure_ascii=False))
        if result['status']=='BLOCKED':raise SystemExit(2)
    else:
        info=status_message(a.project)
        print(json.dumps(info if a.command=='status' else {'next_allowed_stage':info['next_allowed_stage']},
                         indent=2,ensure_ascii=False))

if __name__=='__main__':main()
