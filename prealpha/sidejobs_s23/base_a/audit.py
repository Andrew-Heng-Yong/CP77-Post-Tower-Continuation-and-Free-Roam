"""Read-only compact source/capture inspection for the S23 base_a components."""
import argparse,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
IDS=['mq024_sandra','mq007_smartgun','mq035_ozob','mq012_stud','mq002_veterans','mq021_guide','mq041_corpo','mq044_jakes_vehicle']
CAPTURE=ROOT/'research/sidejobs_s23/live_20261016_01/capture.json'
CAPTURE_SHA='47084A3833CFE507D184A19CDD1276215A15F917F6B97AA4130E6A6E6919748A'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def graphs(p):
    r=SafeResource(load(p));return flatten(r,r.obj['Data']['RootChunk'])
def value(x):return x.get('$value') if isinstance(x,dict) else x
def compact(n):
    d={k:v for k,v in n.items() if k in ['id','$type','socketName','type','condition','phaseResource','sceneFile','phaseInstancePrefabs','debugString']}
    if 'type' in d and isinstance(d['type'],dict):
        d['type']={k:v for k,v in d['type'].items() if k in ['$type','factName','value','setExactValue','path','action','subtype','rewards']}
    if 'phaseGraph' in n:d['inline']=True
    return d
def inspect(p,path,ids,full):
    for g in graphs(p):
        if path and g['path']!=path:continue
        print('GRAPH',g['path'])
        for n in g['nodes']:
            if not ids or n['id'] in ids:print(json.dumps(n if full else compact(n),separators=(',',':')))
        print('EDGES',json.dumps(g['edges'],separators=(',',':')))
def phones():
    for f in ['holocall_initializers','holocall_cleanup']:
        p=ROOT/('research/gig_restoration/gig_phone_u9/sources/json/base/quest/holocalls/'+f+'.questphase.json')
        for g in graphs(p):
            if g['path']!='root':continue
            for n in g['nodes']:
                if any(x in json.dumps(n).lower() for x in ['sandra','ozob','mr_stud','frank','jake']):print(f,n['id'],json.dumps(compact(n),separators=(',',':')))
def capture():
    assert sha(CAPTURE)==CAPTURE_SHA
    c=load(CAPTURE);assert c['first']==c['second'] and c['repeatedReadMatched']
    return {j['id']:j for j in c['first']['jobs'] if j['id'] in IDS}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inspect',type=Path);p.add_argument('--graph');p.add_argument('--ids',type=int,nargs='*');p.add_argument('--full',action='store_true');p.add_argument('--phones',action='store_true');a=p.parse_args()
    if a.phones:phones()
    elif a.inspect:inspect(a.inspect,a.graph,a.ids,a.full)
    else:print(json.dumps(capture(),indent=2))
