"""Read-only Dogtown checkpoint graph inspection; output lives in this component."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def graphs(p):
 r=SafeResource(read(p)); return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def resources():
 return {str(p).split('json\\',1)[-1][:-5].replace('/','\\'):p for p in sorted((ROOT/'research/dogtown_dt1/gate').glob('native_*/json/**/*.json'))}
def compact(n):
 return {'id':n['id'],'type':n['$type'],'facts':[{'name':value(x[k]),'comparison':x.get('comparisonType'),'value':x.get('value')} for x in walk(n) for k in ['factName','factName1','factName2'] if k in x], 'refs':sorted({x['$value'] for x in walk(n) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string'}),'actions':sorted({str(value(x[k])) for x in walk(n) for k in ['deviceAction','action','socketName'] if k in x})}
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='missing':
  rs=resources(); refs={x['$value'] for p in rs.values() for x in walk(read(p)) if x.get('$type')=='ResourcePath' and x.get('$storage')=='string' and x['$value'].endswith(('.questphase','.scene'))};print(json.dumps(sorted(refs-set(rs))))
 elif mode=='graphs':
  for p,g in graphs(ROOT/sys.argv[2]).items(): print(p, len(g['nodes']),len(g['edges']))
 elif mode in ['nodes','compact']:
  g=graphs(ROOT/sys.argv[2])[sys.argv[3]]; selected=set(map(int,sys.argv[4:]));
  for n in g['nodes']:
   if not selected or n['id'] in selected:print(json.dumps(compact(n) if mode=='compact' else n))
  print('EDGES',json.dumps([e for e in g['edges'] if not selected or e[0] in selected or e[2] in selected]))
