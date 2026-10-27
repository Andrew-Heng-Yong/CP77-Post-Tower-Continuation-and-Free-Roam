import json,sys,hashlib
from pathlib import Path
W=Path(__file__).resolve().parents[3];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten
paths=[
 'research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json',
 'research/q307_extracted/json/ep1/quest/ep1.questphase.json',
 'research/q307_extracted/json/ep1/quest/main_quests/q307/phases/q307_03_hospital.questphase.json',
 'research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json',
 'research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json',
 'research/coyote_sidejobs_audit/native_01/json/base/quest/minor_quests/mq040/mq040.questphase.json']
out=[]
for p in paths:
 try:
  r=SafeResource(json.loads((W/p).read_text()));root=r.obj['Data']['RootChunk'];graphs=flatten(r,root)
 except Exception as e:
  print('skip',p,str(e));continue
 hits=[]
 for g in graphs:
  for n in g['nodes']:
   txt=json.dumps(n)
   if (any(s in txt for s in ['q307_main_game_killed','q307_ep1_killed','minorquests.questphase','mq040.questphase','mq040_active','elcoyote_barman_default_on','mq040_pepe_intro']) or n.get('$type') in ['questGraphSocketDefinition','questDeletionMarkerNodeDefinition']):
    ids={n['id']}
    ids|={e[0] for e in g['edges'] if e[2]==n['id']};ids|={e[2] for e in g['edges'] if e[0]==n['id']}
    hits.append({'graph':g['path'],'match':n['id'],'nodes':[x for x in g['nodes'] if x['id'] in ids],'edges':[e for e in g['edges'] if e[0] in ids and e[2] in ids]})
 row={'path':p,'sha256':hashlib.sha256((W/p).read_bytes()).hexdigest().upper(),'graph_count':len(graphs),'hits':hits}
 out.append(row)
 print(p)
 for h in hits:
  print(' graph',h['graph'],'match',h['match'])
  for n in h['nodes']:print('  ',n['id'],n['$type'],json.dumps({k:v for k,v in n.items() if k not in ['id','$type','phaseGraph']})[:350])
  print(' ',h['edges'])
(O/'native_owner_trace_01.json').write_text(json.dumps(out,indent=2)+'\n')
