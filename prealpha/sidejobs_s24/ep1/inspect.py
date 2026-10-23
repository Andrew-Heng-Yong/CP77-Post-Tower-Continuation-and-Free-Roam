"""Read-only compact normalized native node queries for S24."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import value,walk
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
if __name__=='__main__':
 path,pattern=sys.argv[1:3]
 for p in ([Path(path)] if Path(path).is_file() else Path(path).rglob('*.questphase.json')):
  for gp,g in graphs(p).items():
   for n in g['nodes']:
    if pattern in json.dumps({k:v for k,v in n.items() if k!='phaseGraph'}):
     print(p.relative_to(ROOT) if p.is_absolute() else p,gp,n['id'],json.dumps({k:v for k,v in n.items() if k!='phaseGraph'}))
