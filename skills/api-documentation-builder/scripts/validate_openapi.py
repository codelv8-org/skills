#!/usr/bin/env python3
"""Offline checks on a generated sanitized OpenAPI document; never resolves URLs."""
import json, re, sys
from pathlib import Path

METHODS={'get','put','post','delete','options','head','patch','trace'}

def check(d):
    errors=[]
    def req(ok, code):
        if not ok: errors.append(code)
    def local_ref(ref):
        if not isinstance(ref,str) or not ref.startswith('#/'): return None
        node=d
        try:
            for seg in ref[2:].split('/'):
                key=seg.replace('~1','/').replace('~0','~'); node=node[int(key)] if isinstance(node,list) else node[key]
            return node
        except (KeyError, TypeError, IndexError, ValueError): return None
    def walk(x,seen):
        if isinstance(x,(dict,list)):
            if id(x) in seen: return
            seen.add(id(x))
        if isinstance(x,dict):
            for k,v in x.items():
                if k=='$ref': req(local_ref(v) is not None,'external-or-unresolved-reference')
                if k in ('$dynamicRef','$recursiveRef','$id'): req(False,'unsupported-reference-or-schema-id')
                if k=='servers':
                    req(isinstance(v,list) and all(isinstance(server,dict) and server.get('url')=='https://api.example.invalid' and not server.get('variables') for server in v),'non-placeholder-server')
                walk(v,seen)
        elif isinstance(x,list):
            for v in x: walk(v,seen)
    req(isinstance(d.get('openapi'),str) and bool(re.fullmatch(r'3\.[01]\.\d+',d['openapi'])),'openapi-version')
    info=d.get('info',{}); req(bool(info.get('title')) and bool(info.get('version')),'info-title-or-version')
    walk(d,set())
    schemes=d.get('components',{}).get('securitySchemes',{})
    def sec(x):
        if x is None: return
        req(isinstance(x,list),'security-list')
        for entry in x:
            req(isinstance(entry,dict) and all(k in schemes and isinstance(v,list) for k,v in entry.items()),'security-scheme-reference')
    sec(d.get('security'))
    def params(items):
        out={}
        for p in items:
            if '$ref' in p: p=local_ref(p['$ref'])
            if not isinstance(p,dict): req(False,'parameter-reference'); continue
            key=(p.get('name'),p.get('in')); req(key not in out and bool(key[0]) and key[1] in {'path','query','header','cookie'},'parameter-identity')
            out[key]=p
        return out
    ids=set(); paths=d.get('paths')
    req(isinstance(paths,dict),'paths-object')
    for path,item in paths.items():
        req(isinstance(path,str) and path.startswith('/') and '?' not in path and '://' not in path,'path-template')
        if '$ref' in item: req(False,'path-item-reference-needs-inline-review'); continue
        names=set(re.findall(r'\{([^{}]+)\}',path)); base=params(item.get('parameters',[]))
        for method,op in item.items():
            if method not in METHODS: continue
            oid=op.get('operationId'); req(isinstance(oid,str) and bool(oid) and oid not in ids,'operation-id'); ids.add(oid)
            merged={**base,**params(op.get('parameters',[]))}
            req({n for n,loc in merged if loc=='path'}==names and all(p.get('required') is True for (n,loc),p in merged.items() if loc=='path'),'path-parameter-mismatch')
            responses=op.get('responses',{}); req(isinstance(responses,dict) and bool(responses),'responses-missing')
            for code,r in responses.items():
                req(isinstance(code,str) and bool(re.fullmatch(r'(?:[1-5][0-9]{2}|[1-5]XX|default)',code)),'response-status')
                req(isinstance(r,dict) and ('$ref' in r or bool(r.get('description'))),'response-description')
            sec(op.get('security'))
    return errors

def main():
    if len(sys.argv)!=2: print('Usage: validate_openapi.py GENERATED_OPENAPI.yaml'); return 1
    try:
        p=Path(sys.argv[1]); raw=p.read_text(encoding='utf-8')
        if p.suffix.lower()=='.json': d=json.loads(raw)
        else:
            try: import yaml
            except ImportError: print('FAIL: PyYAML unavailable; use JSON or an approved offline validator'); return 1
            d=yaml.safe_load(raw)
        errors=check(d)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError): print('FAIL: invalid contract structure'); return 1
    except Exception: print('FAIL: contract parsing or validation error'); return 1
    for e in sorted(set(errors)): print('BLOCK:',e)
    print('FAIL' if errors else 'PASS: limited offline structural checks; full standards validation, examples, scopes and privacy review still required')
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main())
