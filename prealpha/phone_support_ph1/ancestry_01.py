from model import *
C=Path('prealpha/phone_support_ph1/candidate_03')
for p in C.glob('native_*.json'):
 for gp,g in model(p).items():
  for i,n in g['nodes'].items():
   v={k:v for k,v in n.items() if k!='phaseGraph'}
   if 'holocall_initializers' in str(v):print(p.name,gp,i,v)
def dep(n):return n['phaseResource']['DepotPath']['$value']
base=model(C/'base_quest_cyberpunk2077.questphase.json')
ep=model(C/'ep1_quest_ep1.questphase.json')
a=model(C/'native_base_quest_additional_game_elements.questphase.json')
e=model(C/'native_ep1_quest_ep1_additional_game_elements.questphase.json')
assert dep(base['root/82']['nodes'][3])=='base\\quest\\additional_game_elements.questphase'
assert dep(a['root']['nodes'][34])=='base\\quest\\holocalls\\holocall_initializers.questphase'
assert dep(ep['root/10']['nodes'][4])=='ep1\\quest\\ep1_additional_game_elements.questphase'
assert dep(e['root']['nodes'][3])=='ep1\\quest\\holocalls\\holocall_initializers_ep1.questphase'
out={'status':'PASS_NATIVE_INITIALIZER_RETIREMENT_ANCESTRY','base':'root/82/3 -> additional/34 -> base initializer; root106 ->109 -> terminating107','ep1':'root/10/4 -> additional/3 -> EP1 initializer; root/10/8 ->cut9 cuts4 BEFORE killed10','alternate':'q307 root/6 contains BOTH initializers; journalSucceeded16 ->18 ->cut17 cuts6','sources':read(C/'ancestry_sources_01.json'),'limitation':'Source proof of native ownership and retirement, not a public runtime liveness query.'}
(C/'ancestry_proof_01.json').write_text(json.dumps(out,indent=2)+'\n')
