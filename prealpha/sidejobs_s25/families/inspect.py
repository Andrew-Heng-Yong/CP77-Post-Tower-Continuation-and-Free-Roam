"""Read-only, compact, normalized original graph inspection for S25 families."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import value,walk
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
if __name__=='__main__':
 path=sys.argv[1];gpath=sys.argv[2] if len(sys.argv)>2 else 'root'
 for gp,g in graphs(path).items():
  if gp!=gpath:continue
  for n in g['nodes']:
   print(n['id'],n['$type'],json.dumps({k:v for k,v in n.items() if k in ('condition','socketName','phaseResource','type')},separators=(',',':')))
  print('EDGES',g['edges'])
