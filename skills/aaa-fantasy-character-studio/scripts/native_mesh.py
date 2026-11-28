"""Compile explicit topology or authored ring lofts into GLB 2.0. No external libraries.
This is an authoring kernel, not a trained 3D generator, sculptor, remesher or baker.
Coordinate system: meters, Y up, +Z forward. Bind transforms: translations only.
"""
import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path

MAX_VERTICES=600_000
MAX_TRIANGLES=300_000
MAX_TEXTURE_BYTES=32*1024*1024

def require(ok, msg):
    if not ok: raise ValueError(msg)

def vec(x,n):
    require(isinstance(x,(list,tuple)) and len(x)==n and all(type(v) in (float,int) and math.isfinite(v) and abs(v)<1e10 for v in x),f'expected finite {n}-vector')
    return tuple(float(v) for v in x)

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a):
    n=norm(a); require(n>1e-12,'zero-length vector'); return tuple(x/n for x in a)

def mesh_part(part):
    """Return positions, faces, UVs, source weights, seam pairs. Explicit quads must be ordered and convex."""
    kind=part.get('kind','mesh')
    if kind=='mesh':
        pos=[vec(x,3) for x in part['positions']]; faces=part['faces']; uv=[vec(x,2) for x in part['uv']]
        weights=part.get('weights'); seams=part.get('smooth_seams',[])
    elif kind=='loft':
        rings=part['rings']; require(len(rings)>=2,'need 2+ rings')
        n=len(rings[0]); require(n>=3 and (n+1)*len(rings)<=MAX_VERTICES,'invalid loft size')
        require(all(len(r)==n for r in rings),'unequal rings')
        pos=[]; uv=[]; faces=[]; seams=[]
        ring_weights=part.get('ring_weights'); weights=[] if ring_weights is not None else None
        if weights is not None: require(len(ring_weights)==len(rings),'ring weight count')
        for j,r in enumerate(rings):
            for i in range(n+1):
                pos.append(vec(r[i%n],3)); uv.append((i/n,j/(len(rings)-1)))
                if weights is not None: weights.append(ring_weights[j])
            seams.append([j*(n+1),j*(n+1)+n])
        for j in range(len(rings)-1):
            for i in range(n):
                a=j*(n+1)+i; b=a+n+1
                faces.append([a,a+1,b+1,b] if not part.get('reverse_winding',False) else [a,b,b+1,a+1])
    else: raise ValueError(f'unsupported part kind {kind}')
    require(0<len(pos)<=MAX_VERTICES and len(uv)==len(pos),'position/UV mismatch or limit')
    require(0<len(faces)<=MAX_TRIANGLES,'face count limit')
    require(all(0<=x<=1 for t in uv for x in t),'UV0 outside [0,1]')
    tris=[]; edges=Counter(); nrm=[(0.,0.,0.) for _ in pos]
    for face in faces:
        require(len(face) in (3,4) and len(set(face))==len(face) and all(type(i) is int and 0<=i<len(pos) for i in face),'invalid face')
        for i,j in zip(face,face[1:]+face[:1]): edges[tuple(sorted((i,j)))]+=1
        t=[face[:3]]+([[face[0],face[2],face[3]]] if len(face)==4 else [])
        normals=[]
        for a,b,c in t:
            cr=cross(sub(pos[b],pos[a]),sub(pos[c],pos[a])); require(norm(cr)>1e-12,'degenerate face')
            normals.append(cr)
            for i in (a,b,c): nrm[i]=add(nrm[i],cr)
            tris.append((a,b,c))
        if len(normals)==2: require(dot(*normals)>0,'folded/concave quad; author triangles explicitly')
    require(len(tris)<=MAX_TRIANGLES,'triangle limit')
    require(max(edges.values())<=2,'nonmanifold indexed edge')
    seen=set()
    for pair in seams:
        require(len(pair)==2 and all(type(i) is int and 0<=i<len(pos) and i not in seen for i in pair) and pair[0]!=pair[1],'invalid or reused seam pair')
        a,b=pair; require(norm(sub(pos[a],pos[b]))<1e-7,'seam positions differ'); seen.update(pair)
        avg=add(nrm[a],nrm[b]); nrm[a]=nrm[b]=avg
    if weights is not None: require(len(weights)==len(pos),'weight count mismatch')
    return {'positions':pos,'normals':[unit(x) for x in nrm],'uv':uv,'triangles':tris,'weights':weights,
            'quads':sum(len(f)==4 for f in faces),'indexed_boundary_edges':sum(v==1 for v in edges.values())}

class GLB:
    def __init__(self):
        self.bin=bytearray(); self.d={'asset':{'version':'2.0','generator':'AAA Fantasy Character Studio native kernel v2.0'},'scene':0,'scenes':[{'nodes':[]}], 'nodes':[], 'meshes':[], 'materials':[], 'accessors':[], 'bufferViews':[]}
    def view(self, raw, target=None):
        self.bin.extend(b'\0'*((-len(self.bin))%4)); v={'buffer':0,'byteOffset':len(self.bin),'byteLength':len(raw)}
        if target: v['target']=target
        self.bin.extend(raw); self.d['bufferViews'].append(v); return len(self.d['bufferViews'])-1
    def accessor(self, data, typ, comp=5126, target=None, bounds=False):
        f={5126:'f',5125:'I',5123:'H'}[comp]; k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[typ]
        require(bool(data),'empty accessor'); flat=[x for row in data for x in row] if k>1 else list(data)
        require(len(flat)==len(data)*k,'accessor shape mismatch'); raw=struct.pack('<'+f*len(flat),*flat)
        a={'bufferView':self.view(raw,target),'componentType':comp,'count':len(data),'type':typ}
        if bounds:
            rows=data if k>1 else [(x,) for x in data]; a['min']=[min(col) for col in zip(*rows)]; a['max']=[max(col) for col in zip(*rows)]
        self.d['accessors'].append(a); return len(self.d['accessors'])-1
    def node(self, node): self.d['nodes'].append(node); return len(self.d['nodes'])-1
    def texture(self, base, rel, cache):
        require(isinstance(rel,str) and not Path(rel).is_absolute(),'texture must be relative')
        p=(base/rel).resolve(); require(p.is_relative_to(base.resolve()) and p.is_file(),'texture missing or escapes source directory')
        if p in cache: return cache[p]
        require(p.stat().st_size<=MAX_TEXTURE_BYTES,'texture too large'); raw=p.read_bytes()
        require(sum(v.get('byteLength',0) for v in self.d['bufferViews'] if 'target' not in v)+len(raw)<=MAX_TEXTURE_BYTES,'texture/data budget exceeded')
        mime='image/png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else 'image/jpeg' if raw.startswith(b'\xff\xd8\xff') else None
        require(mime,'only PNG/JPEG supported')
        images=self.d.setdefault('images',[]); textures=self.d.setdefault('textures',[])
        images.append({'bufferView':self.view(raw),'mimeType':mime,'name':p.name}); textures.append({'source':len(images)-1}); cache[p]=len(textures)-1; return cache[p]
    def bytes(self):
        self.bin.extend(b'\0'*((-len(self.bin))%4)); self.d['buffers']=[{'byteLength':len(self.bin)}]
        j=json.dumps(self.d,separators=(',',':'),allow_nan=False).encode(); j+=b' '*((-len(j))%4)
        return struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(self.bin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(self.bin),b'BIN\0')+self.bin

def compile_ir(ir,base):
    require(ir.get('version')==1 and ir.get('axes')=='Y_UP_Z_FORWARD_METERS','unsupported MeshIR version or axes')
    g=GLB(); cache={}; material_ids={}; report=[]; totalv=totalt=0
    for material in ir['materials']:
        name=material['id']; require(isinstance(name,str) and name and name not in material_ids,'duplicate/bad material ID')
        bc=vec(material.get('base_color',[1,1,1,1]),4); metal,rough=vec([material.get('metallic',0),material.get('roughness',.5)],2)
        require(all(0<=x<=1 for x in (*bc,metal,rough)),'material factor out of range')
        m={'name':name,'pbrMetallicRoughness':{'baseColorFactor':bc,'metallicFactor':metal,'roughnessFactor':rough},'doubleSided':bool(material.get('double_sided',False))}
        tex=material.get('textures',{}); require(set(tex)<= {'base_color','orm','normal','ao','emissive'},'unknown texture slot')
        for slot, prop, target in [('base_color','baseColorTexture',m['pbrMetallicRoughness']),('orm','metallicRoughnessTexture',m['pbrMetallicRoughness']),('normal','normalTexture',m),('ao','occlusionTexture',m),('emissive','emissiveTexture',m)]:
            if slot in tex: target[prop]={'index':g.texture(base,tex[slot],cache)}
        if 'orm' in tex and 'ao' not in tex: m['occlusionTexture']={'index':g.texture(base,tex['orm'],cache)}
        if 'emissive' in tex: m['emissiveFactor']=vec(material.get('emissive_factor',[1,1,1]),3); require(all(0<=x<=1 for x in m['emissiveFactor']),'emissive factor out of range')
        alpha=material.get('alpha_mode','OPAQUE'); require(alpha in ('OPAQUE','MASK','BLEND'),'bad alpha mode'); m['alphaMode']=alpha
        if alpha=='MASK': m['alphaCutoff']=float(material.get('alpha_cutoff',.5)); require(0<=m['alphaCutoff']<=1,'bad alpha cutoff')
        material_ids[name]=len(g.d['materials']); g.d['materials'].append(m)
    bones=ir.get('joints',[]); bone_ids={}; bone_nodes=[]; world=[]; roots=[]
    require(len(bones)<=256,'joint limit')
    for bone in bones:
        name=bone['id']; require(isinstance(name,str) and name and name not in bone_ids,'duplicate/bad bone ID')
        t=vec(bone['translation'],3); parent=bone.get('parent'); require(parent is None or parent in bone_ids,'parent must precede child')
        node=g.node({'name':name,'translation':t}); bone_ids[name]=len(bone_nodes); bone_nodes.append(node)
        if parent is None: roots.append(node); world.append(t)
        else:
            pi=bone_ids[parent]; g.d['nodes'][bone_nodes[pi]].setdefault('children',[]).append(node); world.append(add(world[pi],t))
    if bones:
        require(len(roots)==1,'exactly one skeleton root required'); g.d['scenes'][0]['nodes']+=roots
        inv=[(1,0,0,0,0,1,0,0,0,0,1,0,-x,-y,-z,1) for x,y,z in world]
        g.d['skins']=[{'joints':bone_nodes,'skeleton':roots[0],'inverseBindMatrices':g.accessor(inv,'MAT4')}]
    part_ids=set(); skinned=0
    for part in ir['parts']:
        name=part['id']; require(isinstance(name,str) and name and name not in part_ids,'duplicate/bad part ID'); part_ids.add(name)
        require(part['material'] in material_ids,'unknown material')
        p=mesh_part(part); nv=len(p['positions']); nt=len(p['triangles']); totalv+=nv; totalt+=nt; require(totalv<=MAX_VERTICES and totalt<=MAX_TRIANGLES,'aggregate geometry budget exceeded')
        attr={'POSITION':g.accessor(p['positions'],'VEC3',target=34962,bounds=True),'NORMAL':g.accessor(p['normals'],'VEC3',target=34962),'TEXCOORD_0':g.accessor(p['uv'],'VEC2',target=34962)}
        ws=p['weights']; joint_rows=[]; weight_rows=[]
        if ws is not None:
            require(bool(bones),'weights supplied without skeleton')
            for row in ws:
                require(isinstance(row,dict) and 1<=len(row)<=4 and all(j in bone_ids for j in row),'bad influence map')
                pairs=[(bone_ids[j],vec([v],1)[0]) for j,v in row.items()]; require(all(0<v<=1 for _,v in pairs) and abs(sum(v for _,v in pairs)-1)<1e-5,'weights must sum to one; no automatic correction')
                pairs.sort(); pairs += [(0,0)]*(4-len(pairs)); joint_rows.append(tuple(j for j,v in pairs)); weight_rows.append(tuple(v for j,v in pairs))
            attr['JOINTS_0']=g.accessor(joint_rows,'VEC4',5123,34962); attr['WEIGHTS_0']=g.accessor(weight_rows,'VEC4',target=34962)
        prim={'attributes':attr,'indices':g.accessor([i for tri in p['triangles'] for i in tri],'SCALAR',5125,34963),'material':material_ids[part['material']],'mode':4}
        g.d['meshes'].append({'name':name,'primitives':[prim]}); node={'name':name,'mesh':len(g.d['meshes'])-1}
        if ws is not None: node['skin']=0; skinned+=1
        g.d['scenes'][0]['nodes'].append(g.node(node)); report.append({'id':name,'vertices':nv,'triangles':nt,'source_quads':p['quads'],'indexed_boundary_edges':p['indexed_boundary_edges'],'skinned':ws is not None})
    require(totalt>0,'no geometry'); require(not bones or skinned>0,'skeleton without skinned mesh')
    for clip in ir.get('animations',[]):
        require(bool(bones),'animation without skeleton'); anim={'name':clip['name'],'samplers':[],'channels':[]}; targets=set()
        for track in clip['tracks']:
            bone=track['joint']; path=track['path']; require(bone in bone_ids and path in ('translation','rotation') and (bone,path) not in targets,'bad/duplicate animation target'); targets.add((bone,path))
            times=[vec([t],1)[0] for t in track['times']]; require(bool(times) and times[0]>=0 and all(b>a for a,b in zip(times,times[1:])),'animation times must increase')
            values=[vec(v,4 if path=='rotation' else 3) for v in track['values']]; require(len(values)==len(times),'animation sample count mismatch')
            if path=='rotation': require(all(abs(norm(v)-1)<1e-5 for v in values),'animation quaternions must be normalized')
            sampler={'input':g.accessor(times,'SCALAR',bounds=True),'output':g.accessor(values,'VEC4' if path=='rotation' else 'VEC3'),'interpolation':'LINEAR'}; anim['samplers'].append(sampler); anim['channels'].append({'sampler':len(anim['samplers'])-1,'target':{'node':bone_nodes[bone_ids[bone]],'path':path}})
        require(bool(anim['channels']),'empty clip'); g.d.setdefault('animations',[]).append(anim)
    out=g.bytes(); return out, {'status':'COMPILED_ONLY','triangles':totalt,'vertices':totalv,'parts':report,'joints':len(bones),'skinned_parts':skinned,'clips':[a['name'] for a in g.d.get('animations',[])],'embedded_images':len(g.d.get('images',[])),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest(),'not_verified':['visual fidelity','general UV overlap','geometric self-intersection','normal/AO bake','deformation','full glTF validation','engine performance','independent review']}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('source',type=Path); p.add_argument('output',type=Path); p.add_argument('--report',type=Path); a=p.parse_args()
    try:
        require(a.source.stat().st_size<=100*1024*1024,'source exceeds 100 MiB'); ir=json.loads(a.source.read_text()); raw,report=compile_ir(ir,a.source.parent.resolve()); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(raw)
        if a.report: a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2)); return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,OverflowError,struct.error) as e:
        print(f'BLOCKED: {e}'); return 1
if __name__=='__main__': raise SystemExit(main())
