"""Create an actor-free native dialogue choice bound to the exact H10 door."""
from pathlib import Path
import copy,json,hashlib
H=Path(__file__).resolve().parent;C=H/'candidate_01'
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
p=C/'native_donor/northside_purchase.scene.json'
obj=json.loads(p.read_text(encoding='utf-8-sig'));r=obj['Data']['RootChunk']
assert r['actors']==r['playerActors']==[]
ns={h['Data']['nodeId']['id']:h['Data'] for h in r['sceneGraph']['Data']['graph']}
assert set(ns)=={2,1540,1542,1546,1569}
hid=max(int(v['HandleId']) for v in walk(obj) if 'HandleId' in v)+1
def handle(d):
 global hid
 h={'HandleId':str(hid),'Data':d};hid+=1;return h
def fresh_handles(d):
 d=copy.deepcopy(d);mapping={}
 for v in walk(d):
  if 'HandleId' in v:
   global hid
   old=v['HandleId'];mapping[old]=str(hid);v['HandleId']=str(hid);hid+=1
 for v in walk(d):
  if 'HandleRefId' in v:v['HandleRefId']=mapping[v['HandleRefId']]
 return d
def fact(name,value):return handle({'$type':'questFactsDBCondition','type':handle({'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':name,'value':value})})
def and_facts(*pairs):return handle({'$type':'questLogicalCondition','operation':'AND','conditions':[fact(*p) for p in pairs]})
door='$/03_night_city/c_watson/little_china/loc_megabuilding_a_prefab4KCU2IQ/loc_megabuilding_a_gameplay_prefab2GWVWSA/#loc_megabuilding_a_devices/{q001_door_v_flat}_prefab4EOA7RA/#q001_door_v_flat'
choice=ns[1542];choice['mode']='attachToGameObject'
choice['atgoParams']['nodeRef']={'$type':'NodeRef','$storage':'string','$value':door}
choice['atgoParams']['visualizerStyle']='onScreen'
shape=choice['shapeParams']['Data'];shape.update(customActivationRange=3.5,customIndicationRange=5.0,activationYawLimit=360)
shape['offset']={'$type':'Vector3','X':0,'Y':0,'Z':1.1}
template=copy.deepcopy(choice['options'][0]);choice['options']=[]
option_template=copy.deepcopy(next(o for o in r['screenplayStore']['options'] if o['itemId']['id']==5378))
r['screenplayStore']['lines']=[];r['screenplayStore']['options']=[]
r['locStore']['vdEntries']=[];r['locStore']['vpEntries']=[]
labels=['Purchase apartment — €$25,000','Not enough money — €$25,000 required','Not now']
for i,label in enumerate(labels):
 op=copy.deepcopy(template);op['screenplayOptionId']['id']=2+256*i
 op['caption']['$value']='PTFRH5_'+str(i);op['type']['properties']=[1,4,0][i]
 op['isSingleChoice']=0;op['blueline']=0;op['bluelineCondition']=None
 op['questCondition']=and_facts(('PTFRH5_Ready',1),('PTFRH5_Funds',1 if i==0 else 0)) if i<2 else fact('PTFRH5_Ready',1)
 choice['options'].append(op)
 loc=181025050000000001+i;variant=loc+1000
 sc=copy.deepcopy(option_template);sc['itemId']['id']=op['screenplayOptionId']['id'];sc['locstringId']['ruid']=str(loc);r['screenplayStore']['options'].append(sc)
 r['locStore']['vdEntries'].append({'$type':'scnlocLocStoreEmbeddedVariantDescriptorEntry','localeId':'en_us','locstringId':{'$type':'scnlocLocstringId','ruid':str(loc)},'signature':{'$type':'scnlocSignature','val':'3'},'variantId':{'$type':'scnlocVariantId','ruid':str(variant)},'vpeIndex':i})
 r['locStore']['vpEntries'].append({'$type':'scnlocLocStoreEmbeddedVariantPayloadEntry','content':label,'variantId':{'$type':'scnlocVariantId','ruid':str(variant)}})
# Only the explicitly selected purchase output writes Request. Cancel is a
# separate harmless UI request; the insufficient-funds row is inactive.
first=copy.deepcopy(choice['outputSockets'][0]);reserved=copy.deepcopy(choice['outputSockets'][1:])
choice['outputSockets']=[]
for i,dest in enumerate((1540,None,1570)):
 s=copy.deepcopy(first);s['stamp']['ordinal']=i
 if dest is None:s['destinations']=[]
 else:s['destinations'][0]['nodeId']['id']=dest
 choice['outputSockets'].append(s)
choice['outputSockets']+=reserved
writer=next(v for v in walk(ns[1540]) if v.get('$type')=='questSetVar_NodeType');writer['factName']='PTFRH5_Request'
cancel=fresh_handles(ns[1540]);cancel['nodeId']['id']=1570;cancel['questNode']['Data']['id']=1570
next(v for v in walk(cancel) if v.get('$type')=='questSetVar_NodeType')['factName']='PTFRH5_Cancel'
r['sceneGraph']['Data']['graph'].append(handle(cancel))
next(v for v in walk(ns[1569]) if v.get('$type')=='questVarComparison_ConditionType')['factName']='PTFRH5_Ready'
# Discard inherited screenplay/performer debug labels with no executable use.
r['debugSymbols']['performersDebugSymbols']=[]
for v in walk(r):
 assert not(v.get('$type')=='scnActorId' and v['id']!=4294967295)
 assert not(v.get('$type')=='scnPerformerId' and v['id']&255==1)
out=C/'h10_purchase.scene.json';assert not out.exists();out.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Prepared H10 actor-free dialogue: buy, insufficient funds, not now.')
