#!/usr/bin/env python3
"""Build before/after 4-view comparison board and honest artist-review scorecard.

No CV 'fidelity score' is faked: PASS requires explicit reviewed ratings and
named visual evidence for all critical checks. The board itself is NOT PASS.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

VIEWS=('front','back','left','right')
DEFAULT_CHECKS = [
    ('front_silhouette', True, 5),('back_silhouette',True,4),
    ('left_profile',True,4),('right_profile',True,4),
    ('face_landmarks',True,5),('hair_volume_4views',True,5),
    ('proportion_head_torso_legs',True,5),('hands_ears_shoes',True,4),
    ('uniform_color_materials',False,3),('straps_bag_badge',False,4),
    ('facet_style',True,5),('deformation_45_90_degree',True,5),
]

def build_board(ref_dir: Path, render_dir: Path, out: Path, width=380, height=680) -> None:
    if width<80 or height<80:
        raise ValueError('Board cell too small')
    bg=Image.new('RGB',(width*4, (height+52)*2),(234,237,242))
    draw=ImageDraw.Draw(bg)
    for i, view in enumerate(VIEWS):
        for row, source in enumerate((ref_dir,render_dir)):
            path=source / (view+'.png')
            if not path.is_file():
                raise FileNotFoundError(f'Missing view {path}')
            im=ImageOps.exif_transpose(Image.open(path)).convert('RGB')
            im.thumbnail((width-16,height-12),Image.Resampling.LANCZOS)
            pad=Image.new('RGB',(width,height),(245,246,249))
            pad.paste(im,((width-im.width)//2,(height-im.height)//2))
            bg.paste(pad,(i*width,row*(height+52)+42))
            draw.text((i*width+12,row*(height+52)+13),
                      ('REFERENCE' if row==0 else 'MODEL RENDER')+'  /  '+view.upper(),
                      fill=(27,38,63))
    out.parent.mkdir(parents=True,exist_ok=True)
    bg.save(out)


def make_scorecard(out: Path) -> dict:
    obj={
        'status':'NOT_TESTED',
        'scoring_notice':'Human-in-the-loop fidelity evaluation, NOT machine perception or likeness guarantee.',
        'review_conditions':{'critical_check_min':4.0, 'weighted_average_min':4.3,
                             'rating_scale':'0=wrong/missing 1=poor 2=weak 3=partial 4=good 5=excellent'},
        'checks':[{'id':id,'critical':critical,'weight':weight,'rating':None,'evidence':None,'correction':None}
                  for id,critical,weight in DEFAULT_CHECKS],
        'artist_name_or_role':None,
        'reference_camera_alignment_verified':False,
        'notes':'Annotate each critical point; do not complete PASS from file validity or model-generation counts.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
    return obj


def score_review(obj: dict, evidence_root: Path | None = None) -> dict:
    checks=obj.get('checks',[])
    if not checks:
        return {'status':'NOT_TESTED','error':'Missing checks'}
    missing=[c.get('id') for c in checks if not isinstance(c.get('rating'),(int,float)) or c.get('evidence') in (None,'')]
    invalid_evidence=[]
    if evidence_root is not None:
        for c in checks:
            if c.get('evidence'):
                path=Path(c['evidence'])
                file=path if path.is_absolute() else evidence_root/path
                if not file.is_file() or file.stat().st_size==0:
                    invalid_evidence.append(c.get('id'))
    if missing or invalid_evidence or not obj.get('reference_camera_alignment_verified') or not obj.get('artist_name_or_role'):
        return {'status':'REVIEW_REQUIRED','unreviewed_or_missing_evidence':missing,
                'evidence_files_not_found': invalid_evidence,
                'reviewer_supplied': bool(obj.get('artist_name_or_role')),
                'camera_alignment_verified':bool(obj.get('reference_camera_alignment_verified'))}
    invalid=[c['id'] for c in checks if not 0<=c['rating']<=5]
    if invalid:
        return {'status':'BLOCKED','invalid_ratings':invalid}
    weighted=sum(c['rating']*c.get('weight',1) for c in checks)/sum(c.get('weight',1) for c in checks)
    failed=[c['id'] for c in checks if c.get('critical') and c['rating']<4]
    return {'status':'PASS' if weighted>=4.3 and not failed else 'REVIEW_REQUIRED',
            'weighted_average_0to5':round(weighted,3),'failed_critical_checks':failed}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ref',type=Path)
    ap.add_argument('--renders',type=Path)
    ap.add_argument('--board',type=Path)
    ap.add_argument('--new-scorecard',type=Path)
    ap.add_argument('--score',type=Path)
    ap.add_argument('--json',type=Path)
    args=ap.parse_args()
    if args.board:
        if not args.ref or not args.renders:ap.error('--board needs --ref and --renders')
        build_board(args.ref,args.renders,args.board)
    if args.new_scorecard: make_scorecard(args.new_scorecard)
    if args.score:
        result=score_review(json.loads(args.score.read_text(encoding='utf-8')), evidence_root=args.score.parent)
        if args.json:
            args.json.parent.mkdir(parents=True,exist_ok=True)
            args.json.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    if not (args.board or args.new_scorecard or args.score): ap.error('Nothing requested')

if __name__=='__main__':main()
