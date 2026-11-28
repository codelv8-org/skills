"""Bounded software clay renderer for exact native GLB bind geometry. No external deps.
Not a PBR renderer, deformation test, or arbitrary glTF importer.
"""
import argparse, json, math, struct, zlib
from pathlib import Path
from native_mesh import cross, dot, norm, sub, unit, require


def read_native(path):
    require(path.stat().st_size<=128*1024*1024,'GLB exceeds renderer byte limit'); raw=path.read_bytes()
    magic,version,size=struct.unpack_from('<4sII',raw); require(magic==b'glTF' and version==2 and size==len(raw),'bad GLB')
    n,typ=struct.unpack_from('<I4s',raw,12); require(typ==b'JSON','missing JSON')
    d=json.loads(raw[20:20+n]); bsize,btype=struct.unpack_from('<I4s',raw,20+n); require(btype==b'BIN\0' and 28+n+bsize==len(raw),'bad BIN'); data=raw[28+n:]
    require(d.get('asset',{}).get('generator','').startswith('AAA Fantasy Character Studio native kernel'),'native compiler GLB only')
    def accessor(i,kind,comp,k):
        a=d['accessors'][i]; v=d['bufferViews'][a['bufferView']]; require(a['type']==kind and a['componentType']==comp and 'sparse' not in a and 'byteStride' not in v and v['buffer']==0,'unsupported accessor')
        offset=v.get('byteOffset',0)+a.get('byteOffset',0); count=a['count']; fmt={5126:'f',5125:'I'}[comp]; length=count*k*4
        require(0<count<=900_000 and 0<=offset<=len(data)-length and offset+length<=v.get('byteOffset',0)+v['byteLength'],'accessor outside buffer')
        return list(struct.iter_unpack('<'+fmt*k,data[offset:offset+length]))
    parts=[]
    for node in d['nodes']:
        if 'mesh' not in node: continue
        require(not ({'matrix','rotation','scale','translation'} & set(node)),'mesh node transform unsupported')
        for prim in d['meshes'][node['mesh']]['primitives']:
            require(prim.get('mode',4)==4,'triangles required'); pos=accessor(prim['attributes']['POSITION'],'VEC3',5126,3); idx=[x[0] for x in accessor(prim['indices'],'SCALAR',5125,1)]
            require(len(idx)%3==0 and all(i<len(pos) for i in idx),'bad triangles'); tris=list(zip(idx[::3],idx[1::3],idx[2::3]));parts.append((pos,tris))
    require(parts and sum(len(t) for _,t in parts)<=300_000,'empty or too complex'); return parts


def png(path,w,h,rgb):
    def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    payload=b''.join(b'\0'+rgb[y*w*3:(y+1)*w*3] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(payload,6))+chunk(b'IEND',b''))


def render(parts,view,center,scale,size=384):
    cam=unit(view); right=unit(cross((0,1,0),cam)); up=cross(cam,right); light=unit((.3,.55,1)); img=bytearray([238,240,242]*(size*size)); depth=[-math.inf]*(size*size); budget=35_000_000; covered=0
    for pos,tris in parts:
        pts=[]
        for p in pos:
            q=sub(p,center);pts.append((size/2+dot(q,right)*scale,size/2-dot(q,up)*scale,dot(q,cam)))
        for ia,ib,ic in tris:
            a,b,c=pts[ia],pts[ib],pts[ic]; dx1=b[0]-a[0];dy1=b[1]-a[1];dx2=c[0]-a[0];dy2=c[1]-a[1];det=dx1*dy2-dy1*dx2
            if abs(det)<1e-10:continue
            xmin=max(0,math.floor(min(a[0],b[0],c[0])));xmax=min(size-1,math.ceil(max(a[0],b[0],c[0])));ymin=max(0,math.floor(min(a[1],b[1],c[1])));ymax=min(size-1,math.ceil(max(a[1],b[1],c[1])))
            budget-=max(0,xmax-xmin+1)*max(0,ymax-ymin+1); require(budget>=0,'raster budget exceeded; reduce resolution or use cloud renderer')
            n=unit(cross(sub(pos[ib],pos[ia]),sub(pos[ic],pos[ia]))); nl=(dot(n,right),dot(n,up),dot(n,cam)); shade=int(80+135*max(0,dot(nl,light)))
            if nl[2]<0: shade=max(38,shade//2)  # dark back faces expose winding defects; no culling
            pixel=bytes((shade,shade,shade))
            for y in range(ymin,ymax+1):
                py=y+.5-a[1]
                for x in range(xmin,xmax+1):
                    px=x+.5-a[0];u=(px*dy2-py*dx2)/det;v=(dx1*py-dy1*px)/det
                    if u<0 or v<0 or u+v>1:continue
                    z=a[2]+u*(b[2]-a[2])+v*(c[2]-a[2]); i=y*size+x
                    if z>depth[i]:
                        if depth[i]==-math.inf: covered+=1
                        depth[i]=z;img[3*i:3*i+3]=pixel
    return img,covered


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('glb',type=Path);p.add_argument('outdir',type=Path);p.add_argument('--size',type=int,default=384);p.add_argument('--camera-from',type=Path,help='reuse center and pixel scale from accepted views.json');a=p.parse_args()
    try:
        require(128<=a.size<=512,'size must be 128..512'); parts=read_native(a.glb);mins=[min(p[i] for pos,_ in parts for p in pos) for i in range(3)]; maxs=[max(p[i] for pos,_ in parts for p in pos) for i in range(3)];center=tuple((x+y)/2 for x,y in zip(mins,maxs)); span=norm(sub(maxs,mins));require(span>0,'zero extent');scale=a.size*.87/span
        if a.camera_from:
            locked=json.loads(a.camera_from.read_text()); require(locked['resolution']==a.size,'camera resolution differs'); center=tuple(locked['center_m']);scale=float(locked['pixels_per_meter']); require(len(center)==3 and all(math.isfinite(v) for v in center) and math.isfinite(scale) and scale>0,'bad locked camera')
        views={'front':(0,0,1),'back':(0,0,-1),'right':(1,0,0),'left':(-1,0,0),'three_quarter':(1,.25,1)}; a.outdir.mkdir(parents=True,exist_ok=True);result={}
        for name,view in views.items():
            img,n=render(parts,view,center,scale,a.size); png(a.outdir/(name+'.png'),a.size,a.size,img);result[name]={'covered_pixels':n,'camera_direction':view}
        report={'status':'CLAY_BIND_ONLY','source':str(a.glb),'center_m':center,'pixels_per_meter':scale,'resolution':a.size,'camera_lock_source':str(a.camera_from) if a.camera_from else None,'views':result,'limitations':'Flat software shading from native GLB triangles; no texture, PBR, animation, smooth normal, ray bake or independent review.'};(a.outdir/'views.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,struct.error) as e:print(f'BLOCKED: {e}');return 1
if __name__=='__main__':raise SystemExit(main())
