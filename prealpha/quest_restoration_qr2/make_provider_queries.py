"""Bounded dependency queries from the three concrete quest investigations."""
from pathlib import Path
import json,gzip,sys
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02'
idx=read(A/'resource_inventory.json');models=read(A/'model_inventory.json')
dep=set(read(O/'quests/mq035_ozob/provider_requests.json'))
dep.update(read(O/'quests/mq038_neweridentity/dependency_depots.json')['depots'])
paid=read(O/'quests/mq045_victor_debt/resources.json')
dep.update(paid)
for d in paid:
 m=read(models[d]['normalized_model']) if not models[d]['normalized_model'].endswith('.gz') else json.loads(gzip.decompress(Path(models[d]['normalized_model']).read_bytes()))
 dep.update(m['refs'])
extra=['base\\quest\\cyberpunk2077.questphase','base\\quest\\bugfixing.questphase','base\\quest\\bugfixing\\quest_bugfixing.questphase','base\\quest\\minor_quests\\minorquests.questphase']
dep.update(extra);rows=[]
for d in sorted(dep):
 expected=[idx[d]['sha256']] if idx.get(d,{}).get('sha256') else []
 if d=='base\\quest\\cyberpunk2077.questphase':expected=[sha(W/'research/q307_extracted/raw/base/quest/cyberpunk2077.questphase')]
 rows.append({'depot':d,'expected_sha256':expected,'hash_payload':d.endswith(('.questphase','.scene','.quest')),'export':d in extra[:2]})
write(O/'provider_queries.json',rows)
print(json.dumps({'queries':len(rows),'hashed_graphs':sum(x['hash_payload'] for x in rows),'fresh_parent_exports':2}))
