"""Report capabilities; the declared runtime location is not independently attested."""
import argparse, importlib.util, json, os, platform, shutil, sys, tempfile
from pathlib import Path

def report(runtime, model):
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'probe'; p.write_text('ok'); writable=p.read_text()=='ok'
    return {'runtime_assertion':runtime,'runtime_attested':False,'model_assertion':model,
            'model_verified':False,'python':platform.python_version(),'os':platform.system(),
            'cpu_count_visible':os.cpu_count(),'workspace_writable':writable and os.access('.',os.W_OK),
            'native_compiler':sys.version_info >= (3,10),
            'optional_executables':{x:bool(shutil.which(x)) for x in ('blender','gltf-validator','node','chromium','nvidia-smi')},
            'optional_modules':{x:importlib.util.find_spec(x) is not None for x in ('numpy','PIL','trimesh')},
            'strict_policy':'no external 3D SaaS, no local generation, no downloaded learned weights',
            'independent_review':'UNVERIFIED','gpu':'UNVERIFIED','renderer':'UNVERIFIED','engine':'UNVERIFIED'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--runtime',choices=['PLATFORM_CLOUD','LOCAL','UNVERIFIED'],required=True);p.add_argument('--model',required=True)
    a=p.parse_args();r=report(a.runtime,a.model); print(json.dumps(r,indent=2));sys.exit(0 if a.runtime=='PLATFORM_CLOUD' and r['native_compiler'] and r['workspace_writable'] else 2)
