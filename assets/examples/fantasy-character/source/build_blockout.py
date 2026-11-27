#!/usr/bin/env python3
"""Reference-traced visual hull and diagnostic skin, NOT an anatomical sculpt or game asset.
Dependencies: numpy scipy scikit-image Pillow trimesh. Coordinates are manual observations
from the synthetic concept, not measured human anatomy or calibrated camera views.
"""
import json, struct, hashlib, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
import trimesh
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parents[1]
# Traces use 1204 x 1280 review coordinates; the full source is resized exactly.
# The front silhouette includes the outer robe, hair, ornaments, and boots.
FRONT=[(309,3),(318,21),(326,29),(338,47),(351,68),(357,91),(349,119),(350,145),(363,179),(391,186),(417,194),(448,193),(440,213),(432,232),(446,264),(464,294),(473,318),(486,338),(504,356),(522,379),(542,409),(556,437),(571,457),(582,479),(587,500),(597,520),(600,545),(596,555),(590,549),(582,531),(573,510),(562,503),(558,514),(552,508),(552,490),(543,474),(543,465),(522,450),(503,430),(479,416),(473,396),(454,379),(429,349),(409,312),(388,292),(386,337),(374,366),(378,404),(393,448),(410,502),(430,570),(451,631),(474,701),(493,763),(507,818),(509,881),(502,930),(512,961),(505,986),(480,1005),(445,1024),(449,1056),(436,1076),(407,1090),(405,1145),(415,1175),(433,1195),(437,1218),(426,1225),(376,1224),(354,1213),(353,1179),(352,1110),(352,1084),(326,1091),(302,1096),(273,1092),(252,1082),(258,1116),(252,1158),(250,1195),(249,1217),(232,1225),(192,1223),(188,1214),(192,1198),(207,1178),(214,1146),(208,1092),(179,1080),(150,1084),(145,1070),(151,1035),(111,1016),(91,1000),(93,985),(101,963),(75,951),(55,934),(54,919),(64,892),(82,851),(105,807),(126,766),(139,720),(151,682),(178,620),(201,552),(216,491),(214,480),(235,417),(243,399),(240,371),(245,343),(236,292),(222,264),(206,296),(186,330),(163,360),(139,382),(132,403),(115,423),(88,448),(77,463),(75,480),(67,508),(61,514),(56,509),(58,494),(48,503),(37,525),(30,544),(26,554),(19,553),(20,543),(17,545),(21,522),(32,499),(38,478),(50,459),(63,439),(85,413),(99,387),(110,346),(113,363),(134,331),(149,298),(167,270),(181,245),(178,225),(167,194),(190,201),(213,189),(237,180),(258,178),(270,145),(272,123),(264,108),(261,92),(268,71),(279,53),(290,40),(288,23),(300,21)]
SIDE=[(879,28),(887,31),(897,46),(901,65),(906,91),(908,125),(910,168),(904,201),(892,211),(890,228),(889,257),(900,288),(911,321),(922,351),(931,376),(940,396),(929,402),(918,411),(913,399),(904,407),(882,390),(882,417),(878,432),(867,438),(830,438),(827,434),(830,425),(843,420),(854,405),(857,392),(853,357),(850,337),(840,356),(827,390),(824,373),(829,324),(823,285),(824,251),(822,225),(828,199),(829,178),(826,155),(829,136),(837,118),(844,103),(848,96),(842,86),(834,79),(840,71),(837,57),(846,48),(859,45),(869,36)]
# Deliberate assumptions: no independent left profile; back not used for depth.
# Full silhouette is not topology of separate cloth, face or fingers.
LANDMARKS={'crown_tip':[309,3],'head_top':[310,44],'chin':[310,163],'neck':[310,188],'waist':[310,389],'shoulder_left':[408,228],'elbow_left':[483,373],'wrist_left':[556,468],'fingertip_left':[596,550],'shoulder_right':[211,228],'elbow_right':[135,373],'wrist_right':[65,468],'fingertip_right':[21,550],'left_ankle':[379,1159],'right_ankle':[228,1159],'floor':[310,1225]}
S=1.85/(1225-44)

def mask(poly,size=(1204,1280)):
    im=Image.new('L',size);ImageDraw.Draw(im).polygon(poly,fill=255);return np.asarray(im)>0

def hull():
    mf=mask(FRONT);ms=mask(SIDE)
    # Sampling in meters, GLTF Y-up and +Z front; 11.5mm grid.
    dx=.0115
    xx=np.arange(-.51,.511,dx); yy=np.arange(-.025,1.97,dx); zz=np.arange(-.40,.27,dx)
    vol=np.zeros((len(xx),len(yy),len(zz)),np.float32)
    # side profile shoulder/hip alignment: floor -> floor, top hair -> head top.
    for j,y in enumerate(yy):
        fy=int(round(1225-y/S));sy=int(round(438-y*(438-44)/1.85))
        if not 0<=fy<mf.shape[0] or not 0<=sy<ms.shape[0]: continue
        xs=np.where(mf[fy])[0]; ss=np.where(ms[sy])[0]
        # crown top is inferred in profile; keep small thickness rather than delete.
        if not len(xs):continue
        if not len(ss):
            if y>1.85: ss=np.array([870,885])
            else:continue
        z0=(861-ss[-1])*1.85/(438-44);z1=(861-ss[0])*1.85/(438-44)
        if z1-z0<.025: z0-=.008;z1+=.008
        split=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
        for run in split:
            lo=(run[0]-310)*S;hi=(run[-1]-310)*S
            if hi-lo<.006:lo-=.004;hi+=.004
            mid=(lo+hi)/2;w=(hi-lo)/2
            # Independent arm intervals: arm-depth is inferred, not the cape depth.
            a,b=z0,z1
            if abs(mid)>.18 and 1.02<y<1.62:
                width=min(.16,max(.05,(hi-lo)*1.05));a,b=-width/2+.01,width/2+.01
            # A rounded intersection of the front and side envelope; not a true scan.
            # Mildly flattened cross-section, rather than rectangular extrusion.
            v=((xx-mid)/max(w,.003))[:,None]
            u=((zz-(a+b)/2)/max((b-a)/2,.003))[None,:]
            field=1-(abs(v)**3+abs(u)**2)
            vol[:,j,:]=np.maximum(vol[:,j,:],np.clip(field,0,1))
    vol=gaussian_filter(vol,(.85,1.45,.85))
    verts,faces,_,_=marching_cubes(vol,level=.17,spacing=(dx,dx,dx),allow_degenerate=False)
    verts+=np.array([xx[0],yy[0],zz[0]])
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=True);mesh.fix_normals()
    # Keep physically present isolated crown/arm fragments if substantive.
    mesh=trimesh.util.concatenate([p for p in mesh.split(only_watertight=False) if len(p.faces)>150]);mesh.fix_normals()
    trimesh.smoothing.filter_taubin(mesh,lamb=.45,nu=.48,iterations=12); mesh.vertices[:,1]-=mesh.bounds[0,1]
    return mesh

# Bind-pose joint scaffold. World positions are inferred, never anatomical acceptance.
BONES=[('root',None,(0,0,0)),('pelvis','root',(0,.98,0)),('spine','pelvis',(0,1.22,0)),('chest','spine',(0,1.47,0)),('neck','chest',(0,1.64,0)),('head','neck',(0,1.73,0))]
for side,sgn in [('L',1),('R',-1)]:
    BONES.extend([(f'clavicle_{side}','chest',(sgn*.09,1.57,0)),(f'upper_arm_{side}',f'clavicle_{side}',(sgn*.15,1.56,.005)),(f'forearm_{side}',f'upper_arm_{side}',(sgn*.275,1.335,.015)),(f'hand_{side}',f'forearm_{side}',(sgn*.386,1.18,.02)),(f'thigh_{side}','pelvis',(sgn*.095,.98,0)),(f'shin_{side}',f'thigh_{side}',(sgn*.105,.48,.005)),(f'foot_{side}',f'shin_{side}',(sgn*.124,.11,.04)),(f'robe_{side}','pelvis',(sgn*.13,1.16,-.02)),(f'robe_tip_{side}',f'robe_{side}',(sgn*.22,.54,-.04))])
BONES.extend([('hair_01','head',(0,1.77,-.09)),('hair_02','hair_01',(0,1.48,-.16)),('hair_03','hair_02',(0,1.28,-.19)),('robe_back','pelvis',(0,1.18,-.14)),('robe_back_tip','robe_back',(0,.50,-.19))])

def skin(mesh):
    v=np.asarray(mesh.vertices);names=[b[0] for b in BONES];world=np.array([b[2] for b in BONES]);J=np.zeros((len(v),4),np.uint16);W=np.zeros((len(v),4),np.float32)
    for i,(x,y,z) in enumerate(v):
        side='L' if x>=0 else 'R'; ax=abs(x)
        if y>1.70: group=['head','neck','hair_01'] if z<-.06 else ['head','neck']
        elif y>1.24 and z<-.095 and ax<.17: group=['head','neck','hair_01','hair_02','hair_03','chest']
        elif y>1.01 and ax>np.interp(y,[1.01,1.30,1.55,1.68],[.27,.20,.12,.15]):group=[f'clavicle_{side}',f'upper_arm_{side}',f'forearm_{side}',f'hand_{side}','chest']
        elif y<.22: group=[f'foot_{side}',f'shin_{side}']
        elif y<1.20: group=['pelvis',f'thigh_{side}',f'shin_{side}',f'foot_{side}',f'robe_{side}',f'robe_tip_{side}','robe_back','robe_back_tip']
        else:group=['pelvis','spine','chest','neck','head',f'clavicle_{side}']
        ids=np.array([names.index(n) for n in group]);d=np.linalg.norm(world[ids]-v[i],axis=1);order=np.argsort(d)[:4];ids=ids[order];d=d[order];w=1/(d+.035)**4;w/=w.sum();J[i,:len(ids)]=ids;W[i,:len(ids)]=w
    return names,world,J,W

class GLB:
    def __init__(self): self.raw=bytearray();self.doc={'asset':{'version':'2.0','generator':'Sword Immortal visual hull diagnostic'},'bufferViews':[],'accessors':[],'buffers':[{}]}
    def arr(self,a,kind,component,target=None,bounds=False):
        a=np.ascontiguousarray(a);pad=(-len(self.raw))%4;self.raw.extend(b'\0'*pad);off=len(self.raw);b=a.tobytes();self.raw.extend(b);view={'buffer':0,'byteOffset':off,'byteLength':len(b)}
        if target:view['target']=target
        vi=len(self.doc['bufferViews']);self.doc['bufferViews'].append(view);d={'bufferView':vi,'componentType':component,'count':len(a),'type':kind}
        if bounds:d.update(min=a.min(axis=0).reshape(-1).tolist(),max=a.max(axis=0).reshape(-1).tolist())
        idx=len(self.doc['accessors']);self.doc['accessors'].append(d);return idx
    def save(self,path):
        self.raw.extend(b'\0'*((-len(self.raw))%4));self.doc['buffers'][0]['byteLength']=len(self.raw);j=json.dumps(self.doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4);out=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(self.raw))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(self.raw),0x004e4942)+self.raw;path.write_bytes(out)

def export(mesh):
    names,world,J,W=skin(mesh);g=GLB();v=np.asarray(mesh.vertices,dtype='<f4');n=np.asarray(mesh.vertex_normals,dtype='<f4');f=np.asarray(mesh.faces,dtype='<u2').reshape(-1)
    # UV0 intentionally omitted: proxy has no surface unwrap. Do not fake production UVs.
    attr={'POSITION':g.arr(v,'VEC3',5126,34962,True),'NORMAL':g.arr(n,'VEC3',5126,34962),'JOINTS_0':g.arr(J.astype('<u2'),'VEC4',5123,34962),'WEIGHTS_0':g.arr(W.astype('<f4'),'VEC4',5126,34962)}
    ia=g.arr(f,'SCALAR',5123,34963);nodes=[];matrices=[]
    for name,parent,pos in BONES:
        parentpos=world[names.index(parent)] if parent else np.zeros(3);nodes.append({'name':name,'translation':(np.array(pos)-parentpos).tolist()});m=np.eye(4,dtype=np.float32);m[:3,3]=-np.array(pos);matrices.append(m.T.reshape(-1))
    for k,(_,parent,_) in enumerate(BONES):
        if parent:nodes[names.index(parent)].setdefault('children',[]).append(k)
    ib=g.arr(np.array(matrices,dtype='<f4'),'MAT4',5126)
    nodes.append({'name':'Reference visual hull - diagnostic skin','mesh':0,'skin':0,'extras':{'status':'PROTOTYPE','not_anatomical':True}})
    t=g.arr(np.array([0,1,2],dtype='<f4'),'SCALAR',5126,bounds=True);samplers=[];channels=[];angles={'upper_arm_L':7,'upper_arm_R':-7,'forearm_L':-8,'forearm_R':8,'head':3}
    for name,angle in angles.items():
        axis='y' if name=='head' else 'z'; q=Rotation.from_euler(axis,np.array([[0],[angle],[0]]),degrees=True).as_quat().astype('<f4'); ai=g.arr(q,'VEC4',5126);samplers.append({'input':t,'output':ai,'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':names.index(name),'path':'rotation'}})
    g.doc.update(scene=0,scenes=[{'nodes':[0,len(names)]}],nodes=nodes,meshes=[{'name':'Fused concept silhouette','primitives':[{'attributes':attr,'indices':ia,'material':0}]}],materials=[{'name':'Neutral review clay','pbrMetallicRoughness':{'baseColorFactor':[.44,.48,.53,1],'metallicFactor':0,'roughnessFactor':.87}}],skins=[{'name':'Diagnostic inferred joints','joints':list(range(len(names))),'skeleton':0,'inverseBindMatrices':ib}],animations=[{'name':'Diagnostic bend - NOT production motion','samplers':samplers,'channels':channels}],extras={'status':'PROTOTYPE','profile':'WEB_HERO target','gate':'G1 blocked','notes':'Fused silhouette hull, no anatomy, UV, textures, production rig or engine release.'})
    g.save(ROOT/'export'/'sword-immortal-blockout.glb')
    # Verify CPU rest pose and diagnostic pose using exact arrays used for export.
    assert np.isfinite(v).all() and np.isfinite(W).all() and np.max(np.abs(W.sum(axis=1)-1))<1e-6 and J.max()<len(names)
    def deform(pose):
        globals=[]
        for name,parent,pos in BONES:
            parentpos=world[names.index(parent)] if parent else np.zeros(3);m=np.eye(4);m[:3,3]=np.array(pos)-parentpos
            if name in pose:m[:3,:3]=Rotation.from_euler('y' if name=='head' else 'z',pose[name],degrees=True).as_matrix()
            globals.append(globals[names.index(parent)]@m if parent else m)
        mats=np.array(globals)@np.array(matrices).reshape(-1,4,4).transpose(0,2,1)
        homo=np.c_[v,np.ones(len(v))];vv=np.einsum('nkjl,nl->nkj',mats[J],homo);return (vv[:,:,:3]*W[:,:,None]).sum(axis=1)
    rest=deform({});bent=deform(angles);assert np.isfinite(bent).all();resterr=np.max(np.linalg.norm(rest-v,axis=1));delta=np.linalg.norm(bent-v,axis=1);assert resterr<1e-6 and delta.max()>.005
    report={'status':'PROTOTYPE_NOT_AAA','vertices':len(v),'triangles':len(mesh.faces),'joint_count':len(names),'animation_clips':['Diagnostic bend - NOT production motion'],'height_m':float(mesh.extents[1]),'bounds_m':mesh.bounds.tolist(),'weight_sum_max_error':float(np.max(np.abs(W.sum(axis=1)-1))),'rest_pose_max_error_m':float(resterr),'diagnostic_max_displacement_m':float(delta.max()),'degenerate_faces':int(np.sum(mesh.area_faces<1e-12)),'connected_components':len(mesh.split(only_watertight=False)),'watertight':bool(mesh.is_watertight),'material_count':1,'uv0':False,'textures':0,'game_engine_test':'NOT RUN','independent_visual_review':'NOT RUN','limitations':['fused hull of garment and body','inferred depth and joints','no anatomical topology or real costume layers','no UV or texture bake','no production rigging or animation','no Three.js device runtime test']}
    (ROOT/'evidence'/'mesh-metrics.json').write_text(json.dumps(report,indent=2)+'\n');(ROOT/'source'/'rig-scaffold.json').write_text(json.dumps({'status':'inferred diagnostic scaffold','joints':[{'name':a,'parent':b,'position_m':c} for a,b,c in BONES]},indent=2)+'\n');np.savez_compressed(ROOT/'source'/'mesh-arrays.npz',vertices=v,faces=np.asarray(mesh.faces),normals=n,joints=J,weights=W);mesh.export(ROOT/'source'/'visual-hull.obj')
    return report,bent

def evidence(mesh,bent):
    import cv2
    im=Image.open(ROOT/'refs'/'concept.png').convert('RGB').resize((1204,1280));im.thumbnail((1204,1280));d=ImageDraw.Draw(im,'RGBA');d.line(FRONT+[FRONT[0]],fill=(87,219,240,255),width=3);d.line(SIDE+[SIDE[0]],fill=(87,219,240,255),width=2)
    for key,p in LANDMARKS.items():d.ellipse((p[0]-4,p[1]-4,p[0]+4,p[1]+4),fill=(247,186,91,255))
    im.save(ROOT/'renders'/'reference-trace.webp',quality=85)
    (ROOT/'evidence'/'reference-trace.json').write_text(json.dumps({'coordinate_space':[1204,1280],'front_polygon':FRONT,'side_polygon':SIDE,'landmarks':LANDMARKS,'source_sha256':hashlib.sha256((ROOT/'refs'/'concept.png').read_bytes()).hexdigest(),'scale_assumption':'1.85 m from head top to floor; crown not included','view_limit':'single small side facing left; no opposing side; noncalibrated concept'},indent=2)+'\n')
    # Actual orthographic CPU render, painter's algorithm with triangle depth sorting.
    v=np.asarray(mesh.vertices);f=np.asarray(mesh.faces);height=720;width=400;scale=height*.83/mesh.extents[1];center_y=mesh.bounds[:,1].mean()
    def render(verts,angle,title,wire=False):
        a=np.deg2rad(angle);right=np.array([np.cos(a),0,-np.sin(a)]);toward=np.array([np.sin(a),0,np.cos(a)]);q=np.c_[width/2+(verts@right)*scale,height/2-(verts[:,1]-center_y)*scale];depth=verts@toward;tris=verts[f];norm=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]);norm/=np.maximum(1e-10,np.linalg.norm(norm,axis=1))[:,None];light=(toward*.7+right*(-.4)+np.array([0,.6,0]));light/=np.linalg.norm(light);intensity=.33+.58*np.clip(norm@light,0,1)+.10*np.clip(norm@toward,0,1);canvas=np.full((height,width,3),[26,32,45],np.uint8);pts=np.round(q[f]).astype(np.int32)
        for idx in np.argsort(depth[f].mean(axis=1)):
            if norm[idx]@toward<0:continue
            color=tuple(np.clip(np.array([179,190,207])*intensity[idx],0,255).astype(int).tolist());cv2.fillConvexPoly(canvas,pts[idx],color,lineType=cv2.LINE_AA)
            if wire:cv2.polylines(canvas,[pts[idx]],True,(78,89,112),1,cv2.LINE_AA)
        out=Image.fromarray(canvas);draw=ImageDraw.Draw(out);draw.text((16,15),title,fill=(232,237,245));draw.text((16,height-23),'G1 PROXY - NOT AAA',fill=(238,191,114));return out
    angles=[(0,'FRONT'),(-90,'PROFILE'),(180,'BACK'),(35,'THREE QUARTER')];sheet=Image.new('RGB',(width*4,height),(26,32,45))
    for i,(a,title) in enumerate(angles):sheet.paste(render(v,a,title),(width*i,0))
    sheet.save(ROOT/'renders'/'clay-views.webp',quality=88);pair=Image.new('RGB',(width*2,height));pair.paste(render(v,0,'REST / WIREFRAME',True),(0,0));pair.paste(render(bent,0,'DIAGNOSTIC BEND'),(width,0));pair.save(ROOT/'renders'/'diagnostic-bend.webp',quality=88)

if __name__=='__main__':
    for p in ['source','evidence','export','renders']: (ROOT/p).mkdir(exist_ok=True)
    mesh=hull();report,bent=export(mesh);evidence(mesh,bent);print(json.dumps(report,indent=2))
