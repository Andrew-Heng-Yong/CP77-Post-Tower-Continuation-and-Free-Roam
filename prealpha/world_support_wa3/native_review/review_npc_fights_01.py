import json
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2];ns={'__file__':str(W/'prealpha/world_actions_wa2/native_review/census_02.py')};exec((W/'prealpha/world_actions_wa2/native_review/census_02.py').read_text().split('manifest=read(MANIFEST)')[0],ns)
rows=[]
for name in ['mce_wat_nid_phase.questphase','ce_wbr_hill_04.questphase']:
 p=R/'combat_additional_native_01/basegame_4_gamedata.archive'/name;d=ns['read'](Path(str(p)+'.json'));hs=ns['handles'](d);root=d['Data']['RootChunk'];ps=ns['phases']({'$type':'questPhaseNodeDefinition','id':-1,'phaseGraph':root['graph'],'phaseInstancePrefabs':[]},'root',hs)
 rows.append({'resource':name,'binary':str(p),'sha256':ns['sha'](p),'phases':ps})
(R/'npc_fight_families_01.json').write_text(json.dumps(rows,indent=2)+'\n',newline='\n')
for r in rows:
 for p in r['phases']:
  if p['path'] in ['root/13/72','root/25','root/13','root']:
   print(r['resource'],p['path'],'edges',p['edges'])
   for n in (p['payload'].get('phaseGraph') or {}).get('nodes',[]):
    nn={k:v for k,v in n.items() if k!='phaseGraph'};print(json.dumps(nn))
