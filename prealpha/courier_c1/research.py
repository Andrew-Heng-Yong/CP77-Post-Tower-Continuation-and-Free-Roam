"""Read-only analysis of extracted official courier graphs; writes only new evidence."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'prealpha/ncpd_scanner_n1'), str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk, value

def resources():
    found = {}
    for p in sorted((ROOT/'research/courier_c1').glob('*/json/**/*.json')):
        depot = str(p).split('json\\',1)[-1][:-5].replace('/', '\\')
        found[depot] = p
    return found

if __name__ == '__main__':
    rs=resources()
    if sys.argv[1] == 'missing':
        refs=set()
        # Only actual references from courier graphs, not unrelated upper-root branches.
        for depot,p in rs.items():
            if 'courier' not in depot: continue
            for x in walk(json.loads(p.read_text(encoding='utf-8-sig'))):
                if x.get('$type')=='ResourcePath' and x.get('$storage')=='string':
                    s=x.get('$value','')
                    if s.endswith(('.questphase','.scene')): refs.add(s)
        print(json.dumps(sorted(refs-set(rs))))
    elif sys.argv[1] == 'nodes':
        p=ROOT/sys.argv[2]; r=SafeResource(json.loads(p.read_text(encoding='utf-8-sig')))
        selected=set(map(int,sys.argv[3:]))
        g=flatten(r,r.obj['Data']['RootChunk'])[0]
        for n in g['nodes']:
            if n['id'] in selected: print(json.dumps(n))
    elif sys.argv[1] == 'facts':
        facts=set()
        for depot,p in rs.items():
            if 'courier' not in depot: continue
            for x in walk(json.loads(p.read_text(encoding='utf-8-sig'))):
                if 'factName' in x: facts.add(value(x['factName']))
        print(json.dumps(sorted(facts)))
