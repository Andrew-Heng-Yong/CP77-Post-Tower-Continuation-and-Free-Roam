"""Compact read-only stock graph inspection."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
doc=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
r=SafeResource(doc)
def values(x,key):
 if isinstance(x,dict):
  for k,v in x.items():
   if k==key:yield v
   yield from values(v,key)
 elif isinstance(x,list):
  for v in x:yield from values(v,key)
for g in flatten(r,r.obj['Data']['RootChunk']):
 if len(sys.argv)>2 and g['path']!=sys.argv[2]:continue
 print('GRAPH',g['path'])
 for n in g['nodes']:
  if len(sys.argv)>3:
   if int(sys.argv[3])==n['id']:print(json.dumps(n,indent=2))
   continue
  p={k:v for k,v in n.items() if k not in ('phaseGraph','id','$type')}
  keys=('factName','realPath','DepotPath','prefabNodeRef','triggerAreaRef','socketName','rewards','action','entryName','phaseName','spawnerReference','communityEntryName','communityEntryPhaseName')
  detail={k:list(values(p,k)) for k in keys if list(values(p,k))}
  edges=[e[1:] for e in g['edges'] if e[0]==n['id']]
  print(n['id'],n['$type'].replace('quest',''),json.dumps(edges),json.dumps(detail))
