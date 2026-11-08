from model import *
C=Path('prealpha/phone_support_ph1/candidate_03');b=model(C/'base_quest_cyberpunk2077.questphase.json')
for gp,g in b.items():
 for i,n in g['nodes'].items():
  v={k:v for k,v in n.items() if k!='phaseGraph'}
  if 'additional_game_elements' in str(v):print(gp,i,v)
