import json
from pathlib import Path
R=Path('prealpha/world_support_wa3/native_review');a=json.load(open(R/'npc_fight_families_01.json'))
def compact(x):
 if isinstance(x,dict):
  if '$value' in x:return x['$value']
  return {k:compact(v) for k,v in x.items() if k not in ['phaseGraph','dynamicEntityUniqueName','sceneActorContextName','slotName','phaseResource','unfreezingTriggerNodeRef','saveLock']}
 if isinstance(x,list):return [compact(v) for v in x]
 return x
out=[]
for r in a:
 for p in r['phases']:
  if (r['resource'].startswith('mce') and p['path'] in ['root/13','root/13/72']) or (not r['resource'].startswith('mce') and p['path'] in ['root','root/25']):
   q={'source':r['resource'],'path':p['path'],'edges':p['edges'],'nodes':[compact(n) for n in (p['payload'].get('phaseGraph') or {}).get('nodes',[])]};out.append(q)
(R/'npc_fight_compact_01.json').write_text(json.dumps(out,indent=2))
for q in out:
 if q['source'].startswith('mce'):
  print(q['path'], 'edges',q['edges'])
  for n in q['nodes']:print(json.dumps(n))
