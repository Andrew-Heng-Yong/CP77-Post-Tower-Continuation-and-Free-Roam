"""Read-only structured service quest / scene audit helpers."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value
from inspect_story_services import nodes,reach
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def summary(n):
 return {k:[v[k] for v in walk(n) if k in v] for k in ('factName','realPath','itemId','rewardName','vendorId','sceneFile','reference','phaseResource') if any(k in v for v in walk(n))}
if __name__=='__main__':
 p=Path(sys.argv[1]);r=read(p)['Data']['RootChunk']
 if '.scene.' in p.name:
  ns=nodes(r);ids=set(map(int,sys.argv[2].split(','))) if len(sys.argv)>2 and sys.argv[2][0].isdigit() else set(ns)
  for i,n in ns.items():
   if i not in ids:continue
   if len(sys.argv)>2 and not sys.argv[2][0].isdigit() and sys.argv[2] not in json.dumps(n):continue
   print(i,n['$type'],json.dumps(summary(n)),[(value(o.get('caption')),summary(o)) for o in n.get('options',[])],[[[d['nodeId']['id'],d['isockStamp']['ordinal']]for d in s.get('destinations',[])]for s in n.get('outputSockets',[])])
 else:
  for gp,g in graphs(p).items():
   for n in g['nodes']:
    if len(sys.argv)>2 and sys.argv[2] not in json.dumps(n):continue
    print(gp,n['id'],json.dumps(n))
    print('EDGES',[e for e in g['edges'] if e[0]==n['id'] or e[2]==n['id']])
