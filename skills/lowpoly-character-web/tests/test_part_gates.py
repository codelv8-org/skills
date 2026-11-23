"""Unit tests for real stop-the-line stage enforcement and reproducible evidence metrics."""
from __future__ import annotations
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from part_fidelity import compute_metrics,evaluate,_validate_mesh_snapshot
from part_region_crop import prepare as crop_part
from stage_pipeline import initialize,run_stage,read_gate,status_message,STAGES,_directory
import numpy as np

SKILL=Path(__file__).resolve().parents[1]
SOURCE=SKILL/'assets/examples/skinned_demo.glb'


def mask(path, bbox, size=(140,160)):
    im=Image.new('L',size,0)
    ImageDraw.Draw(im).rectangle(bbox,fill=255)
    im.save(path)


def pin_review_context(path):
    """Synthetic reviewer action for fixtures; never a real artistic approval."""
    conf=json.loads(path.read_text())
    result=evaluate(path)
    if 'required_review_context_sha256' not in result:
        raise AssertionError(result)
    conf.get('review',conf.get('human_review'))['context_sha256']=result['required_review_context_sha256']
    path.write_text(json.dumps(conf))


def configure_stage(proj, stage, offset=0, reviewer=True, valid_cam=True, missing_render=False):
    d=_directory(proj,stage)
    conf_path=d/'assessment.json'
    conf=json.loads(conf_path.read_text())
    (d/'model.glb').write_bytes(SOURCE.read_bytes())
    sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    for view in conf['required_views']:
        refmask=proj/'reference_masks'/stage.lower()/f'{view}.png'
        refmask.parent.mkdir(parents=True,exist_ok=True)
        mask(refmask,(40,20,110,130))
        render=d/'renders'/f'{view}.png'
        image=Image.new('RGB',(140,160),(230,232,235))
        ImageDraw.Draw(image).rectangle((40+offset,20,110+offset,130),fill=(160,130,85))
        image.save(render)
        if not missing_render:
            mask(d/'masks'/f'{view}.png',(40+offset,20,110+offset,130))
        ref=proj/'reference'/f'{view}.png'
        image=Image.new('RGB',(140,160),(230,232,235))
        ImageDraw.Draw(image).rectangle((40,20,110,130),fill=(190,140,90))
        image.save(ref)
        conf['views'][view]['landmarks']={}
    for i in range(conf['thresholds']['min_landmarks_total']):
        conf['views']['front']['landmarks'][f'p{i}']={'reference':[.35+i*.08,.5],'render':[.35+i*.08+offset/140,.5]}
    conf['camera_calibration']={'verified':valid_cam,'projection':'ORTHOGRAPHIC','method':'Synthetic locked camera; unit test only'}
    conf['model_author']='SYNTHETIC_BUILDER_ONLY'
    conf['review']['reviewer']='SYNTHETIC_REVIEWER_ONLY'
    conf['review']['reviewer_type']='AI'
    conf['review']['independent_from_author']=True
    conf['review']['approved']=reviewer
    conf['review']['render_model_sha256']=sha
    conf['review']['notes']='Synthetic evidence; not a real artistic acceptance'
    review=d/'review'/'comparison.png'
    board=Image.new('RGB',(280,160),'white')
    with Image.open(proj/'reference/front.png') as image:board.paste(image,(0,0))
    with Image.open(d/'renders/front.png') as image:board.paste(image,(140,0))
    board.save(review)
    for c in conf['review']['checks']:
        c['rating']=5
        c['notes']='Synthetic test supplied'
    conf_path.write_text(json.dumps(conf))
    pin_review_context(conf_path)
    return conf_path

class StageTests(unittest.TestCase):
    def test_null_masks_render_placeholder_without_creating_approval(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            config=configure_stage(p,'HEAD',valid_cam=False)
            data=json.loads(config.read_text())
            for item in data['views'].values():
                item['reference_mask']=None
                item['render_mask']=None
            data['views']['back']['render_image']=None
            config.write_text(json.dumps(data))
            board=p/'diagnostic.png'
            result=evaluate(config,board)
            self.assertEqual(result['status'],'NOT_TESTED')
            self.assertTrue(board.is_file())
            with Image.open(board) as im:self.assertEqual(im.size,(1320,900))

    def test_part_crop_synchronizes_roi_without_independent_model_fitting(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t); ref=p/'source'; render=p/'render';ref.mkdir();render.mkdir()
            for n in ('front','back','left','right'):
                a=Image.new('RGB',(200,100),'white');ImageDraw.Draw(a).rectangle((80,10,120,40),fill='red')
                a.save(ref/f'{n}.png')
                b=Image.new('RGB',(200,100),'white');ImageDraw.Draw(b).rectangle((100,10,140,40),fill='red')
                b.save(render/f'{n}.png')
            spec={'part':'HEAD','global_alignment_verified':False,'reference_dir':str(ref),'render_dir':str(render),
                  'roi_normalized':{v:[.25,0,.75,.6] for v in ('front','back','left','right')}}
            cfg=p/'crop.json';cfg.write_text(json.dumps(spec))
            result=crop_part(cfg,p/'out')
            self.assertEqual(result['status'],'CROP_READY_ALIGNMENT_REVIEW_NEEDED')
            self.assertEqual(result['views']['front']['roi_px'],[50,0,150,60])
            with Image.open(p/'out/front/render.png') as x:self.assertEqual(x.size,(100,60))
            with Image.open(p/'out/front/reference.png') as x:self.assertEqual(x.size,(100,60))

    def test_mask_iou_identical_and_displaced(self):
        a=np.zeros((60,60),dtype=bool);a[10:50,10:30]=1
        b=a.copy();c=np.zeros_like(a);c[10:50,30:50]=1
        self.assertEqual(compute_metrics(a,b)['silhouette_iou'],1.0)
        self.assertEqual(compute_metrics(a,c)['silhouette_iou'],0)
        with self.assertRaises(ValueError):compute_metrics(a,c[:20,:])

    def test_stop_at_head_before_torso(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            res=run_stage(p,'TORSO')
            self.assertEqual(res['status'],'BLOCKED')
            self.assertEqual(res['blocked_by'],['HEAD'])
            self.assertEqual(status_message(p)['next_allowed_stage'],'HEAD')

    def test_good_synthetic_head_can_pass_and_advance(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            configure_stage(p,'HEAD')
            res=run_stage(p,'HEAD')
            self.assertEqual(res['status'],'PASS',res)
            self.assertEqual(res['view_metrics']['front']['silhouette_iou'],1)
            self.assertEqual(res['reviewer_type'],'AI')
            self.assertFalse(res['human_approved'])
            self.assertIsNone(res['human_weighted_rating_0to5'])
            self.assertEqual(status_message(p)['next_allowed_stage'],'TORSO')
            r=run_stage(p,'TORSO')
            self.assertNotEqual(r['status'],'BLOCKED')

    def test_mismatched_head_cannot_advance(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            configure_stage(p,'HEAD',offset=28)
            res=run_stage(p,'HEAD')
            self.assertEqual(res['status'],'REVIEW_REQUIRED',res)
            self.assertTrue(res['failures'])
            self.assertEqual(run_stage(p,'TORSO')['status'],'BLOCKED')

    def test_fake_score_or_camera_not_pass(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            conf=configure_stage(p,'HEAD',valid_cam=False)
            res=run_stage(p,'HEAD')
            self.assertEqual(res['status'],'NOT_TESTED')
            cfg=json.loads(conf.read_text())
            cfg['camera_calibration']['verified']=True
            cfg['review']['checks'][0]['rating']=2
            conf.write_text(json.dumps(cfg))
            pin_review_context(conf)
            self.assertEqual(run_stage(p,'HEAD')['status'],'REVIEW_REQUIRED')
            cfg['review']['checks'][0]['rating']=5
            cfg['review']['render_model_sha256']='bad-fingerprint'
            conf.write_text(json.dumps(cfg))
            self.assertEqual(run_stage(p,'HEAD')['status'],'NOT_TESTED')

    def test_missing_mask_and_corrupt_glb_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            configure_stage(p,'HEAD',missing_render=True)
            self.assertEqual(run_stage(p,'HEAD')['status'],'NOT_TESTED')
            configure_stage(p,'HEAD')
            (p/'stages/01_head/model.glb').write_bytes(b'fake glb')
            r=run_stage(p,'HEAD')
            self.assertEqual(r['status'],'BLOCKED')

    def test_new_mesh_hash_invalidates_old_head_approval(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            configure_stage(p,'HEAD')
            self.assertEqual(run_stage(p,'HEAD')['status'],'PASS')
            f=p/'stages/01_head/model.glb'
            f.write_bytes(f.read_bytes()+b'changed')
            self.assertEqual(read_gate(p,'HEAD')['status'],'REVIEW_REQUIRED')
            self.assertEqual(run_stage(p,'TORSO')['status'],'BLOCKED')

    def test_integration_requires_fresh_same_hash_regressions(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p)
            for name,*_ in STAGES:
                configure_stage(p,name)
                result=run_stage(p,name)
                if name=='INTEGRATION':
                    self.assertEqual(result['status'],'REVIEW_REQUIRED',result)
                    self.assertIn('regression_issues',result)
                else:
                    self.assertEqual(result['status'],'PASS',result)
            # Fake a recycled earlier report with a changed hash: should still FAIL.
            integration=_directory(p,'INTEGRATION')
            integrated_sha=hashlib.sha256((integration/'model.glb').read_bytes()).hexdigest()
            for name,*_ in STAGES[:-1]:
                report=dict(read_gate(p,name));report['model_sha256']=integrated_sha
                dest=integration/'regression'/f'{name.lower()}_gate.json'
                dest.write_text(json.dumps(report))
            self.assertEqual(run_stage(p,'INTEGRATION')['status'],'REVIEW_REQUIRED')
            # Produce truly new evidence and scoring assessments in the integration
            # workspace; snapshots must point to assembled model, not old stage GLB.
            from part_fidelity import evaluate as assess
            for name,*_ in STAGES[:-1]:
                srcdir=_directory(p,name)
                src=json.loads((srcdir/'assessment.json').read_text())
                regdir=integration/'regression'
                new=regdir/f'{name.lower()}_assessment.json'
                src['model_asset']='../model.glb'
                for view in src['required_views']:
                    source_view=src['views'][view]
                    # Copy the test image/masks into the integrated workspace.
                    for key in ('reference_image','render_image','reference_mask','render_mask'):
                        old=(srcdir/source_view[key]).resolve()
                        dest=regdir/f'{name.lower()}_{view}_{key}.png'
                        dest.write_bytes(old.read_bytes())
                        source_view[key]=dest.name
                image=regdir/f'{name.lower()}_human_review.png'
                image.write_bytes((srcdir/'review/comparison.png').read_bytes())
                for ck in src['review']['checks']:
                    ck['evidence']=image.name
                new.write_text(json.dumps(src))
                pin_review_context(new)
                generated=assess(new)
                self.assertEqual(generated['status'],'PASS',generated)
                (regdir/f'{name.lower()}_gate.json').write_text(json.dumps(generated))
            self.assertEqual(run_stage(p,'INTEGRATION')['status'],'PASS')
            self.assertEqual(read_gate(p,'INTEGRATION')['status'],'PASS')
            # A valid report for a different part cannot cover the head regression.
            head_assessment=integration/'regression/head_assessment.json'
            original=head_assessment.read_text()
            wrong=json.loads(original);wrong['part']='TORSO'
            head_assessment.write_text(json.dumps(wrong))
            self.assertEqual(read_gate(p,'INTEGRATION')['status'],'REVIEW_REQUIRED')
            head_assessment.write_text(original)
            manifest=integration/'regression_manifest.json'
            original_manifest=manifest.read_text()
            manifest.write_text('{malformed')
            self.assertEqual(run_stage(p,'INTEGRATION')['status'],'REVIEW_REQUIRED')
            manifest.write_text(original_manifest)
            self.assertEqual(run_stage(p,'INTEGRATION')['status'],'PASS')
            # Hash invalidated: previously accepted total no longer accepted.
            file=integration/'model.glb';file.write_bytes(file.read_bytes()+b'changed')
            self.assertEqual(read_gate(p,'INTEGRATION')['status'],'REVIEW_REQUIRED')

    def test_missing_or_weakened_critical_checks_cannot_pass(self):
        for alteration in ('removed','noncritical','empty'):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text())
                if alteration=='removed':conf['review']['checks'].pop()
                elif alteration=='empty':conf['review']['checks']=[]
                else:conf['review']['checks'][0]['critical']=False
                path.write_text(json.dumps(conf))
                self.assertNotEqual(run_stage(p,'HEAD')['status'],'PASS')
                self.assertEqual(run_stage(p,'TORSO')['status'],'BLOCKED')

    def test_strict_boolean_approval_and_calibration(self):
        for group,field in (('review','approved'),('review','independent_from_author'),('camera_calibration','verified')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text());conf[group][field]='false'
                path.write_text(json.dumps(conf))
                self.assertNotEqual(evaluate(path)['status'],'PASS')

    def test_review_weights_and_thresholds_must_be_finite_and_valid(self):
        for field,value in (('weight',0),('weight',-1),('weight',float('nan')),('rating',True),('rating',float('inf')),
                            ('weighted_min',float('nan')),('min_silhouette_iou','0.8'),('min_landmarks_total',0)):
            with self.subTest(field=field,value=value), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text())
                if field in ('weight','rating'):conf['review']['checks'][0][field]=value
                elif field=='weighted_min':conf['review'][field]=value
                else:conf['thresholds'][field]=value
                path.write_text(json.dumps(conf))
                self.assertNotEqual(evaluate(path)['status'],'PASS')

    def test_missing_reviewer_type_or_same_author_cannot_pass(self):
        for alteration in ('missing_type','self_review'):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text())
                if alteration=='missing_type':conf['review'].pop('reviewer_type')
                else:conf['review']['reviewer']=conf['model_author']
                path.write_text(json.dumps(conf))
                self.assertNotEqual(evaluate(path)['status'],'PASS')

    def test_legacy_review_key_is_read_without_inventing_human_approval(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
            conf=json.loads(path.read_text());conf['human_review']=conf.pop('review')
            path.write_text(json.dumps(conf))
            result=evaluate(path)
            self.assertEqual(result['status'],'PASS',result)
            self.assertFalse(result['human_approved'])

    def test_blank_copied_and_degenerate_evidence_is_rejected(self):
        for alteration in ('blank_render','copied_render','same_path','blank_review','all_white_mask','transparent_render'):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD');d=path.parent
                conf=json.loads(path.read_text());v=conf['views']['front']
                if alteration=='blank_render':Image.new('RGB',(140,160),'white').save(d/v['render_image'])
                elif alteration=='copied_render':(d/v['render_image']).write_bytes((d/v['reference_image']).read_bytes())
                elif alteration=='same_path':v['render_image']=v['reference_image']
                elif alteration=='blank_review':Image.new('RGB',(280,160),'white').save(d/'review/comparison.png')
                elif alteration=='all_white_mask':Image.new('L',(140,160),255).save(d/v['render_mask'])
                else:
                    im=Image.new('RGBA',(140,160),(0,0,0,0));ImageDraw.Draw(im).rectangle((30,30,60,60),fill=(255,0,0,0));im.save(d/v['render_image'])
                path.write_text(json.dumps(conf))
                self.assertEqual(evaluate(path)['status'],'BLOCKED')

    def test_duplicate_or_incomplete_landmarks_cannot_supply_evidence_count(self):
        for alteration in ('duplicate','missing_pair','boolean'):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text());landmarks=conf['views']['front']['landmarks']
                if alteration=='duplicate':landmarks['p1']=landmarks['p0']
                elif alteration=='missing_pair':landmarks['p0'].pop('render')
                else:landmarks['p0']['render'][0]=True
                path.write_text(json.dumps(conf))
                self.assertEqual(evaluate(path)['status'],'BLOCKED')

    def test_removed_or_duplicate_views_cannot_pass(self):
        for views in (['front'],['front','front','left','right'],[]):
            with self.subTest(views=views), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                conf=json.loads(path.read_text());conf['required_views']=views
                path.write_text(json.dumps(conf))
                self.assertNotEqual(evaluate(path)['status'],'PASS')

    def test_one_view_cannot_be_relabelled_as_four_views(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
            conf=json.loads(path.read_text());front=conf['views']['front']
            conf['views']={view:front for view in conf['required_views']}
            path.write_text(json.dumps(conf))
            self.assertEqual(evaluate(path)['status'],'BLOCKED')

    def test_glb_payload_and_active_scene_are_verified(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'test.glb'
            for variant in ('valid','truncated','unreachable','degenerate','nonfinite'):
                with self.subTest(variant=variant):
                    vertices=[0,0,0,1,0,0,0,1,0]
                    if variant=='degenerate':vertices=[0]*9
                    if variant=='nonfinite':vertices[0]=float('nan')
                    binary=struct.pack('<9f',*vertices)
                    if variant=='truncated':binary=binary[:4]
                    doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[] if variant=='unreachable' else [0]}],
                         'nodes':[{'mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0}}]}],
                         'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteLength':len(binary)}],
                         'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'}]}
                    blob=json.dumps(doc).encode();blob+=b' '*((-len(blob))%4)
                    raw=struct.pack('<4sII',b'glTF',2,12+8+len(blob)+8+len(binary))
                    raw+=struct.pack('<I4s',len(blob),b'JSON')+blob+struct.pack('<I4s',len(binary),b'BIN\0')+binary
                    path.write_bytes(raw)
                    if variant=='valid':_validate_mesh_snapshot(path)
                    else:
                        with self.assertRaises(ValueError):_validate_mesh_snapshot(path)

    def test_uncertain_camera_is_diagnostic_until_interpretation_is_documented(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
            conf=json.loads(path.read_text());cam=conf['camera_calibration'];cam['diagnostic_only']=True
            path.write_text(json.dumps(conf))
            pin_review_context(path)
            self.assertEqual(evaluate(path)['status'],'REVIEW_REQUIRED')
            cam['diagnostic_only']=False;cam['reference_basis']='APPROVED_DESIGN_INTERPRETATION'
            path.write_text(json.dumps(conf))
            self.assertEqual(evaluate(path)['status'],'NOT_TESTED')
            cam['interpretation_evidence']='interpretation.md';cam['limitations']='Synthetic hidden-side interpretation only'
            (path.parent/'interpretation.md').write_text('SYNTHETIC TEST ONLY: explicit interpretation approval evidence')
            path.write_text(json.dumps(conf));pin_review_context(path);result=evaluate(path)
            self.assertEqual(result['status'],'PASS',result)
            self.assertEqual(result['fidelity_scope'],'APPROVED_DESIGN_INTERPRETATION')

    def test_changed_render_cannot_reuse_old_independent_review(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
            self.assertEqual(run_stage(p,'HEAD')['status'],'PASS')
            conf=json.loads(path.read_text());old_context=conf['review']['context_sha256']
            image=Image.new('RGB',(140,160),'white');ImageDraw.Draw(image).ellipse((40,20,110,130),fill='blue')
            image.save(path.parent/'renders/front.png')
            result=run_stage(p,'HEAD')
            self.assertEqual(result['status'],'NOT_TESTED',result)
            self.assertNotEqual(result['required_review_context_sha256'],old_context)
            self.assertEqual(json.loads(path.read_text())['review']['context_sha256'],old_context)
            self.assertEqual(run_stage(p,'TORSO')['status'],'BLOCKED')

    def test_reviewer_can_pin_inputs_before_setting_decisions(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD');conf=json.loads(path.read_text())
            context=conf['review']['context_sha256'];conf['review']['approved']=False
            for check in conf['review']['checks']:check['rating']=None
            path.write_text(json.dumps(conf));result=evaluate(path)
            self.assertEqual(result['status'],'NOT_TESTED')
            self.assertEqual(result['required_review_context_sha256'],context)

    def test_cli_report_cannot_overwrite_any_input_or_board(self):
        for target in ('assessment.json','model.glb','renders/front.png','review/comparison.png','report_and_board.png'):
            with self.subTest(target=target),tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD');out=path.parent/target
                before=out.read_bytes() if out.exists() else None
                args=[sys.executable,str(SKILL/'scripts/part_fidelity.py'),str(path),'--out',str(out)]
                if target=='report_and_board.png':args.extend(['--board',str(out)])
                process=subprocess.run(args,capture_output=True,text=True)
                self.assertEqual(process.returncode,2,process.stderr)
                self.assertEqual(json.loads(process.stdout)['status'],'BLOCKED')
                self.assertEqual(out.read_bytes() if out.exists() else None,before)

    def test_cli_protects_model_even_when_other_assessment_fields_are_malformed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD');conf=json.loads(path.read_text())
            conf['views']=[];path.write_text(json.dumps(conf));model=path.parent/'model.glb';original=model.read_bytes()
            process=subprocess.run([sys.executable,str(SKILL/'scripts/part_fidelity.py'),str(path),'--out',str(model)],capture_output=True,text=True)
            self.assertEqual(process.returncode,2,process.stderr)
            self.assertEqual(model.read_bytes(),original)

    def test_saved_pass_is_recomputed_not_trusted(self):
        for alteration in ('forged_status','removed_hashes','changed_metrics'):
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as t:
                p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
                if alteration=='forged_status':
                    conf=json.loads(path.read_text());conf['review']['checks'][0]['rating']=1;path.write_text(json.dumps(conf))
                run_stage(p,'HEAD');gate=path.parent/'gate.json';report=json.loads(gate.read_text())
                if alteration=='forged_status':report['status']='PASS'
                elif alteration=='removed_hashes':report['evidence_sha256']={}
                else:report['view_metrics']['front']['silhouette_iou']=.99
                gate.write_text(json.dumps(report))
                self.assertEqual(read_gate(p,'HEAD')['status'],'REVIEW_REQUIRED')
                self.assertEqual(run_stage(p,'TORSO')['status'],'BLOCKED')

    def test_wrong_stage_and_malformed_assessments_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'proj';initialize(p);path=configure_stage(p,'HEAD')
            conf=json.loads(path.read_text());conf['part']='TORSO';path.write_text(json.dumps(conf))
            self.assertEqual(run_stage(p,'HEAD')['status'],'BLOCKED')
            for text in ('{malformed','[]','null'):
                path.write_text(text)
                self.assertEqual(evaluate(path)['status'],'BLOCKED')

    def test_original_reference_hashes_are_honored(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);refs=root/'sources';refs.mkdir()
            for view in ('front','back','left','right'):
                im=Image.new('RGB',(140,160),(230,232,235));ImageDraw.Draw(im).rectangle((40,20,110,130),fill=(190,140,90));im.save(refs/f'{view}.png')
            p=root/'proj';initialize(p,refs);configure_stage(p,'HEAD')
            self.assertEqual(run_stage(p,'HEAD')['status'],'PASS')
            Image.new('RGB',(140,160),'white').save(p/'reference/front.png')
            self.assertEqual(read_gate(p,'HEAD')['status'],'REVIEW_REQUIRED')
            self.assertEqual(run_stage(p,'HEAD')['status'],'BLOCKED')

if __name__=='__main__': unittest.main()
