"""Resolve native phase/scene dependencies of the built bounded EP1 owners."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'prealpha/ncpd_scanner_n1')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import walk,value
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def refs(p):
 d=read(p)
 r=SafeResource(d)
 return {value(x['DepotPath']) for g in flatten(r,r.obj['Data']['RootChunk']) for n in g['nodes'] for x in walk(n) if 'DepotPath' in x and isinstance(value(x['DepotPath']),str) and value(x['DepotPath']).endswith(('.questphase','.scene'))}
build=Path(sys.argv[1]);m=read(build/'component.json');rows=m.get('resource_details',m['resources']);owned={x['depot'] for x in rows}
paths={}
for p in (ROOT/'research').rglob('*.json'):
 s=p.as_posix()
 if '/json/' not in s or not s.endswith(('.questphase.json','.scene.json')):continue
 depot=s.split('/json/',1)[1][:-5].replace('/','\\')
 # Prefer fresh S23 extraction; older raw resources need independent byte comparison.
 if depot not in paths or '/sidejobs_s23/ep1/native_' in s:paths[depot]=p
todo=set().union(*(refs(build/x['readback']) for x in rows))-owned
seen={};missing=[]
while todo:
 dep=todo.pop()
 if dep in seen or dep in owned:continue
 if dep not in paths:missing.append(dep);continue
 p=paths[dep];raw=Path(str(p).replace('\\json\\','\\raw\\').replace('/json/','/raw/')[:-5])
 assert raw.exists(),raw
 seen[dep]={'raw':raw.relative_to(ROOT).as_posix(),'raw_sha256':sha(raw),'json':p.relative_to(ROOT).as_posix(),'json_sha256':sha(p)}
 if dep.endswith('.questphase'):todo|=refs(p)-owned-set(seen)
result={'status':'PASS_DEPENDENCIES_RESOLVED' if not missing else 'MISSING_DEPENDENCIES','component_sha256':sha(build/'component.json'),'auditor_sha256':sha(Path(__file__)),'native_resources':seen,'missing':sorted(set(missing)),'scope':'All directly referenced native phases recursively and their direct scenes; scene external references not transitive. No file writes outside component evidence.'}
dest=build/'dependencies.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'resources':len(seen),'missing':result['missing']}))
