import json,sys,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[3]; O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
sources=[
 ('research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json',['root','root/82']),
 ('research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json',['root']),
 ('research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json',['root']),
 ('research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/mq040/mq040_biosculpt.questphase.json',None),
]
out=[]
for path,wanted in sources:
 raw=(W/path).read_bytes();r=SafeResource(json.loads(raw)); graphs=flatten(r,r.obj['Data']['RootChunk'])
 selected=[g for g in graphs if wanted is None or g['path'] in wanted]
 row={'path':path,'sha256':hashlib.sha256(raw).hexdigest().upper(),'graphs':selected}
 out.append(row)
 print(path)
 for g in selected:
  print('GRAPH',g['path'],'nodes',len(g['nodes']),'edges',len(g['edges']))
  for n in g['nodes']:
   if path.endswith('minorquests.questphase.json') and n['id'] not in [49,120,121]:continue
   if path.endswith('cyberpunk2077.questphase.json') and g['path']=='root' and n['id'] not in [1,2,82,106,107,109]:continue
   if path.endswith('mq040_biosculpt.questphase.json') and g['path'] not in ['root','root/3','root/12']:continue
   print('NODE',json.dumps(n))
  if len(g['edges'])<80:print('EDGES',g['edges'])
(O/'native_owner_trace_02.json').write_text(json.dumps(out,indent=2)+'\n')
