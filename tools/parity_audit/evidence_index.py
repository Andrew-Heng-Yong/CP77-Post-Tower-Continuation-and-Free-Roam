"""Attach physical source/hash/model evidence to every quest/stage result."""
from common import *
import sys
o=Path(sys.argv[1]);fallback=Path(sys.argv[2]) if len(sys.argv)>2 else o;idx=read(o/'resource_inventory.json');models={};rows=[]
for d,r in idx.items():
 if not r.get('graphs'):continue
 p=o/'models'/(fnv(d)+'.json.gz')
 if not p.exists():p=fallback/'models'/p.name
 assert p.is_file(),f'Model missing: {d}'
 models[d]={'source_json':r['json'],'resource_sha256':r['sha256'],'normalized_model':str(p.resolve()),'normalized_sha256':sha(p),'graphs':r['graphs']}
write(o/'model_inventory.json',models)
for stage in read(o/'stage_results.json'):
 for role,key in [('restored','private_roots'),('vanilla','native_roots')]:
  for d in stage[key]:
   r=idx[d];rows.append({'quest_id':stage['quest_id'],'stage':stage['stage'],'status':stage['status'],'role':role,'resource':d,'source_json':r.get('json'),'sha256':r.get('sha256'),'provider_archive':r.get('archive'),'normalized_model':models.get(d,{}).get('normalized_model'),'graphs':r.get('graphs',[]),'scope':'Candidate root evidence; shared stages/handlers need explicit lifecycle mapping'})
write(o/'stage_evidence.json',rows);csvwrite(o/'stage_evidence.csv',rows)
print(json.dumps({'model_resources':len(models),'quest_stage_source_rows':len(rows)}))
