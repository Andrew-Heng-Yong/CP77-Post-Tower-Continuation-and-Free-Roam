from model import *
W=Path.cwd()
for p in ['research/q307_extracted/json/ep1/quest/ep1.quest.json','research/q307_extracted/json/ep1/quest/main_quests/q307/q307.quest.json','research/q307_extracted/json/base/quest/cyberpunk2077.questphase.json']:
 print(p)
 for gp,g in model(p).items():
  for i,n in g['nodes'].items():
   if any('holocall_initializers' in str(x) or 'q307_ep1_killed' in str(x) or 'q307_main_game_killed' in str(x) for x in [n]) or (gp=='root' and n['$type'] in ['questCutControlNodeDefinition','questOutputNodeDefinition']):
    print(gp,i,str(n)[:650]);print([e for e in g['edges'] if e[0]==i or e[2]==i])
