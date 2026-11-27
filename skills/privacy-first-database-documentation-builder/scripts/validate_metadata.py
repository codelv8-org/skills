#!/usr/bin/env python3
"""Strict offline validation of ALREADY independently approved schema metadata."""
import json
import re
import sys
from pathlib import Path
from release_check import scan

LEVEL = {'Public': 0, 'Internal': 1, 'Confidential': 2, 'Restricted': 3, 'Unknown': 3, None: 3}
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,127}\Z')
PHRASES = {'double precision', 'character varying', 'national character varying', 'national character', 'timestamp with time zone', 'timestamp without time zone', 'time with time zone', 'time without time zone', 'bit varying', 'long varchar', 'long varbinary', 'unsigned big int', 'varying character', 'native character'}
RISK = re.compile(r'(^|_)(hn|an|cid|patient|person|national_id|citizen_id|birth|dob|diagnosis|icd|clinical|medical|password|passwd|secret|token|credential|email|phone|address|first_name|last_name|fullname|full_name|ssn|biometric)(_|$)', re.I)

class Block(ValueError): pass

def require(test, code):
    if not test: raise Block(code)

def pairs(items):
    out = {}
    for k, v in items:
        require(k not in out, 'duplicate-json-key')
        out[k] = v
    return out

def exact(x, required, optional=()):
    require(isinstance(x, dict) and set(required) <= set(x) <= set(required) | set(optional), 'allowlist-or-missing-field')

def seq(x):
    require(isinstance(x,list), 'expected-array'); return x

def ident(x):
    require(isinstance(x,str) and IDENT.fullmatch(x) is not None and not any(scan(x)), 'unsafe-or-unsupported-identifier'); return x

def choose(x, allowed):
    require(x in allowed, 'invalid-enum'); return x

def source(x, sources):
    require(ident(x) in sources, 'unknown-source')

def classification(x):
    choose(x, LEVEL)

def safe_text(x):
    if x is None: return
    require(isinstance(x,str) and 0 < len(x.strip()) <= 300 and len(x)<=300, 'definition-length-or-type')
    require(not any(ord(c)<32 or ord(c)==127 for c in x) and not re.search(r'[<>`]|https?://|\b(?:SELECT|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM)\b',x,re.I) and not any(scan(x)), 'unsafe-definition-pattern')

def effective_field(c, o=None):
    label=c.get('classification')
    risk=bool(RISK.search(c['name']) or (o and RISK.search(o['name'])))
    return 'Restricted' if LEVEL[label]==3 or risk else label

def effective_object(o):
    floor=max([LEVEL[o.get('classification')]]+[LEVEL[effective_field(c,o)] for c in o['columns']])
    return ['Public','Internal','Confidential','Restricted'][floor]

def ordered_names(x, names):
    v=seq(x)
    require(bool(v) and all(ident(n) in names for n in v) and len(v)==len(set(v)), 'key-columns'); return v

def oid(o): return o['schema'], o['name']

def validate(d):
    exact(d,('contract_version','system_label','engine','schema_revision','scope_id','status','approval','sources','objects'),('definitions','lineage'))
    require(d['contract_version']=='2.0','contract-version')
    for k in ('system_label','schema_revision','scope_id'): ident(d[k])
    choose(d['engine'],('mysql','mariadb','postgresql','sqlserver','sqlite','other'))
    choose(d['status'],('verified','partial','template'))
    a=d['approval']; exact(a,('role','reviewed','metadata_only','audience'))
    choose(a['role'],('DBA','DataOwner','Synthetic')); choose(a['audience'],('internal','restricted','public'))
    require(a['reviewed'] is True and a['metadata_only'] is True,'approval-required')
    require((a['role']=='Synthetic')==(d['status']=='template'),'synthetic-status')
    sl=seq(d['sources']); sources=set(ident(s) for s in sl)
    require(bool(sources) and len(sources)==len(sl),'duplicate-or-empty-source')
    obj={}; all_keys={}; all_cols={}
    objects=seq(d['objects']); require(bool(objects) or d['status']!='verified','empty-verified-scope')
    for o in objects:
        exact(o,('schema','name','kind','source_id','columns','keys','foreign_keys'),('classification',))
        identity=(ident(o['schema']),ident(o['name']))
        require(identity not in obj,'duplicate-object'); obj[identity]=o
        choose(o['kind'],('table','view','materialized_view','other')); classification(o.get('classification')); source(o['source_id'],sources)
        cols={}; ords=set(); keys=set(); pk=0; key_sets=[]
        require(bool(seq(o['columns'])),'empty-columns')
        for c in o['columns']:
            exact(c,('name','ordinal','type','length','precision','scale','nullable','source_id'),('classification',))
            n=ident(c['name']); z=c['ordinal']; require(n not in cols and type(z) is int and z>0 and z not in ords,'duplicate-column-or-ordinal')
            t=c['type']; require(isinstance(t,str) and (t.lower() in PHRASES or IDENT.fullmatch(t) is not None) and not any(scan(t)),'unsafe-type')
            for f in ('length','precision','scale'):
                v=c[f]; require(v is None or (type(v) is int and -1000000000<=v<=1000000000 and (f=='scale' or v>=0)),'invalid-dimension')
            require(c['nullable'] is None or type(c['nullable']) is bool,'invalid-nullability')
            classification(c.get('classification')); source(c['source_id'],sources)
            cols[n]=c; ords.add(z)
        for k in seq(o['keys']):
            exact(k,('name','kind','columns','source_id')); n=ident(k['name']); require(n not in keys,'duplicate-key'); keys.add(n)
            choose(k['kind'],('primary','unique')); source(k['source_id'],sources); kn=ordered_names(k['columns'],cols); key_sets.append(set(kn))
            if k['kind']=='primary':
                pk+=1; require(all(cols[x]['nullable'] is not True for x in kn),'nullable-primary-key')
        require(pk<=1,'multiple-primary-keys'); all_keys[identity]=key_sets; all_cols[identity]=cols
        for fk in seq(o['foreign_keys']):
            exact(fk,('name','columns','target_schema','target_name','target_columns','source_id'))
            n=ident(fk['name']); require(n not in keys,'duplicate-key'); keys.add(n); source(fk['source_id'],sources)
            ordered_names(fk['columns'],cols); ident(fk['target_schema']); ident(fk['target_name'])
            seq(fk['target_columns']); [ident(x) for x in fk['target_columns']]
    for o in objects:
        for fk in o['foreign_keys']:
            target=(fk['target_schema'],fk['target_name']); require(target in obj,'foreign-key-outside-scope')
            dst=ordered_names(fk['target_columns'],all_cols[target]); require(len(fk['columns'])==len(dst),'foreign-key-arity')
            require(set(dst) in all_keys[target],'foreign-key-target-key-unverified')
    seen=set()
    for v in seq(d.get('definitions',[])):
        exact(v,('schema','object','column','definition','grain','format','unit','owner_role','source_id','status'))
        k=(ident(v['schema']),ident(v['object'])); require(k in obj,'definition-outside-scope')
        c=v['column']; require(c is None or ident(c) in all_cols[k],'definition-column-outside-scope')
        require((*k,c) not in seen,'duplicate-definition'); seen.add((*k,c)); source(v['source_id'],sources); choose(v['status'],('verified','proposed'))
        for f in ('definition','grain','format','unit','owner_role'): safe_text(v[f])
        require((v['format'] is None and v['unit'] is None) if c is None else (v['grain'] is None and v['owner_role'] is None),'definition-level')
    seen=set()
    for e in seq(d.get('lineage',[])):
        exact(e,('from_schema','from_object','to_schema','to_object','kind','source_id'))
        f=(ident(e['from_schema']),ident(e['from_object'])); t=(ident(e['to_schema']),ident(e['to_object']))
        require(f in obj and t in obj and f!=t,'lineage-outside-scope-or-self'); choose(e['kind'],('derived_from','replicates','transforms')); source(e['source_id'],sources)
        k=(f,t,e['kind']); require(k not in seen,'duplicate-lineage'); seen.add(k)
    return d

def load(path):
    p=Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size<=20*1024*1024,'invalid-input-file')
    return validate(json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=pairs,parse_constant=lambda _: (_ for _ in ()).throw(Block('invalid-json-number'))))

def main():
    if len(sys.argv)!=2: print('Usage: validate_metadata.py APPROVED.json'); return 1
    try: load(sys.argv[1])
    except Block as e: print('BLOCK:',e); return 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError): print('BLOCK: invalid input structure'); return 1
    print('PASS: structural checks only; independent source and disclosure review still required'); return 0
if __name__=='__main__': raise SystemExit(main())
