import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2]
ns={'__file__':str(W/'prealpha/world_actions_wa2/native_review/census_02.py')};exec((W/'prealpha/world_actions_wa2/native_review/census_02.py').read_text().split('manifest=read(MANIFEST)')[0],ns)
read=ns['read'];sha=ns['sha'];handles=ns['handles'];phases=ns['phases']
for folder,out in [('outside_families_native_02','outside_family_inventory_02.json'),('ep1_roots_native_02','ep1_family_inventory_01.json')]:
 rp=R/folder/'report_01.json'
 if not rp.exists():continue
 report=read(rp);rows=[]
 for h in report['hits']:
  p=Path(h['copy']);assert sha(p)==h['sha256'],p
  d=read(Path(str(p)+'.json'));hs=handles(d);root=d['Data']['RootChunk'];fake={'$type':'questPhaseNodeDefinition','id':-1,'phaseGraph':root['graph'],'phaseInstancePrefabs':[]};ps=phases(fake,'root',hs)
  rows.append({'source':str(p)+'.json','resource':h['depot'],'binary_sha256':h['sha256'],'json_sha256':sha(Path(str(p)+'.json')),'phases':ps,'external':sorted({v['value'] for q in ps for v in q['references'] if v['type']=='ResourcePath' and v['value'].endswith('.questphase')})})
 (R/out).write_text(json.dumps(rows,indent=2)+'\n',newline='\n');print(out,len(rows),'prefabs',sum(len(p['prefabs']) for row in rows for p in row['phases']))
