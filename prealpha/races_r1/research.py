"""Read-only native repeatable-race resource closure and graph inspection."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value

def resources():
    return {str(p).split('json\\',1)[-1][:-5].replace('/','\\'):p for p in sorted((ROOT/'research/races_r1').glob('native_*/json/**/*.json'))}

if __name__=='__main__':
    mode=sys.argv[1]; rs=resources()
    if mode=='missing':
        refs={x.get('$value') for p in rs.values() for x in walk(json.loads(p.read_text(encoding='utf-8-sig'))) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x.get('$value','').endswith(('.questphase','.scene'))}
        print(json.dumps(sorted(refs-set(rs))))
    elif mode=='nodes':
        r=SafeResource(json.loads((ROOT/sys.argv[2]).read_text(encoding='utf-8-sig')))
        for g in flatten(r,r.obj['Data']['RootChunk']):
            if g['path']!=sys.argv[3]:continue
            selected=set(map(int,sys.argv[4:]))
            for n in g['nodes']:
                if not selected or n['id'] in selected:print(json.dumps(n))
            print('EDGES',json.dumps(g['edges']))
    elif mode=='facts':
        facts=sorted({value(x[k]) for p in rs.values() for x in walk(json.loads(p.read_text(encoding='utf-8-sig'))) for k in ['factName','factName1','factName2'] if k in x})
        print(json.dumps(facts))
    elif mode=='summary':
        for d,p in rs.items():
            o=json.loads(p.read_text(encoding='utf-8-sig'))
            print(json.dumps({'depot':d,'actors':[a.get('actorName') for a in o['Data']['RootChunk'].get('actors',[])],'facts':sorted({value(x[k]) for x in walk(o) for k in ['factName','factName1','factName2'] if k in x})}))
