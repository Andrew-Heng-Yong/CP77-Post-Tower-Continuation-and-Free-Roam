"""Read-only expanded native node/graph inspection for the Heroes audit."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def graphs(p):
    r=SafeResource(read(p))
    return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}

if __name__=='__main__':
    path=sys.argv[1]
    if len(sys.argv)>2 and sys.argv[2]=='--find':
        for gp,g in graphs(path).items():
            for n in g['nodes']:
                if sys.argv[3] in json.dumps(n):
                    print(gp,n['id'],n['$type'],json.dumps(n,separators=(',',':')))
        raise SystemExit(0)
    gp=sys.argv[2] if len(sys.argv)>2 else 'root'
    ids={int(x) for x in sys.argv[3:]} if len(sys.argv)>3 else None
    g=graphs(path)[gp]
    for n in g['nodes']:
        if ids is None or n['id'] in ids:
            print(json.dumps(n,indent=2))
    print('EDGES',g['edges'])
