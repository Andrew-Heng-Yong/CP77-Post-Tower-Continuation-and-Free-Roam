from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;W=H.parents[4];G=W/'prealpha/quest_restoration_qr5/groups/G17'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read
from model import Resource
P=read(G/'verification_01/source_pins.json');M={p['depot']:Resource(read(p['json'])).normalize()for p in P if p.get('depot')}
for q in ['mq305_combat_zone_report','mq306_dumpster']:
 c=read(G/'quests'/q/'contracts.json')['contracts']
 print(q,json.dumps({k:{'status':v['status'],'proven':v['proven'],'remaining':v['remaining']}for k,v in c.items()}))
print('private resources',json.dumps([d for d in M if d.startswith('towercontinued')]))
for tail,ids in [('ep1_minor_quests.questphase',[6,8,12,14,27]),('mq305_outcome.questphase',[128,134,140,141,142,188]),('mq306.questphase',[3,4,5,7,8,9,10,30,31,32,33,35,39]),('mq306_01_intro.questphase',[2,3,9,50,51]),('mq306_boot.questphase',[1,2,3,4,9,90]),('mq305_fresh_boot.questphase',[1,2,3,4,89,90,91,92,100]),('mq306_fresh_boot.questphase',[1,2,3,4,89,90,91,92,100])]:
 d=next(d for d in M if d.endswith('\\'+tail));m=M[d];g=m['graphs']['root'];print('RESOURCE',d,'PREFABS',m['root_prefabs'])
 for i in ids:
  n=g['nodes'].get(str(i))
  if n:print(i,json.dumps({'type':n['type'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'prefabs':n['prefabs'],'payload':n['payload']if str(i)in['9','14','27']else None,'out':[e for e in g['edges']if e[0]==str(i)]}))
print('OWN',json.dumps([o for o in read(W/'prealpha/sidejobs_s24/ep1/contract02.json')['owners']if o['id']in['mq305_combat_zone_report','mq306_dumpster']]))
print('protocols',json.dumps(read(G/'verification_01/protocols.json')))
