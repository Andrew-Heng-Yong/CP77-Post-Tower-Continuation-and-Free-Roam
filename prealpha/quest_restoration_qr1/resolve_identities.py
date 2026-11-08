"""Bind catalogue IDs to hash-matching component contracts and installed bindings."""
import sys,collections,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
b=read(H/'baseline.json');current=b['private_resources'];o=Path(b['audit']);catalogue=read(H/'queue.json');ids={r['id'] for r in catalogue['quests']};matches=collections.defaultdict(list);manifest_by_contract=collections.defaultdict(list)
files=subprocess.run(['rg','--files','--no-ignore','prealpha','research/gig_restoration','archive','-g','component.json','-g','build.json','-g','manifest.json'],cwd=W,capture_output=True,text=True,check=True).stdout.splitlines()
for rel in files:
 if any(x.lower() in ('fixtures','fixture','recovery') for x in Path(rel).parts):continue
 p=W/rel
 if p.stat().st_size>12_000_000:continue
 try:m=read(p)
 except (ValueError,OSError):continue
 if not isinstance(m,dict):continue
 resources=m.get('resources',{});rs=resources if isinstance(resources,dict) else {r.get('depot'):r.get('sha256') for r in resources if isinstance(r,dict)} if isinstance(resources,list) else {}
 for name,h in m.get('source_pins',{}).items():
  if 'contract'in name and name.endswith('.json'):manifest_by_contract[name.replace('\\','/')].append({'manifest':str(p),'resources':rs,'contract_sha256':h})
contracts=set(subprocess.run(['rg','--files','--no-ignore','prealpha','-g','*contract*.json'],cwd=W,capture_output=True,text=True,check=True).stdout.splitlines())
contracts.update(p for p in manifest_by_contract if (W/p).is_file())
for rel in contracts:
 if any(x.lower() in ('fixtures','fixture','recovery') for x in Path(rel).parts):continue
 p=W/rel
 if p.stat().st_size>5_000_000:continue
 try:obj=read(p)
 except (OSError,ValueError):continue
 owners=obj.get('owners',obj.get('jobs',obj.get('rows',[]))) if isinstance(obj,dict) else obj if isinstance(obj,list) else []
 if not isinstance(owners,list):continue
 for row in owners:
  if not isinstance(row,dict):continue
  qids=({row['id']} if row.get('id') else set())|set(row.get('ids',[]));dep=row.get('depot');native=row.get('native_source',row.get('native',row.get('source')))
  if not dep or dep not in current:continue
  proofs=[m for m in manifest_by_contract[rel.replace('\\','/')] if m['contract_sha256']==sha(p) and m['resources'].get(dep)==current[dep]]
  for qid in qids & ids:
   matches[qid].append({'contract':str(p),'contract_sha256':sha(p),'resource':dep,'resource_sha256':current[dep],'native_source':native,'manifest_proofs':[{k:v for k,v in m.items() if k!='resources'} for m in proofs],'status':'HASH_BOUND_DECLARATION' if proofs else 'DECLARATION_UNBOUND','limit':'Identity mapping only; not complete quest validation'})
out={'ids_with_hash_bound_mapping':sorted(q for q,rs in matches.items() if any(r['status']=='HASH_BOUND_DECLARATION' for r in rs)),'ids_with_unbound_declaration':sorted(q for q,rs in matches.items() if not any(r['status']=='HASH_BOUND_DECLARATION' for r in rs)),'ids_without_contract_match':sorted(ids-set(matches)),'mappings':dict(matches)}
write(H/'identity_resolution_01.json',out);print(json.dumps({k:len(v) for k,v in out.items()}))
