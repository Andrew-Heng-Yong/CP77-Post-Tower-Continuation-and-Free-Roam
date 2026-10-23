"""Independent source/packed-readback review of H1 scene scope; no engine execution."""
import argparse, copy, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
def resolve(obj):
 handles={x['HandleId']:x['Data'] for x in walk(obj) if 'HandleId' in x}
 def rec(x,active=frozenset()):
  if isinstance(x,list):return [rec(v,active) for v in x]
  if not isinstance(x,dict):return x
  if 'HandleRefId' in x:
   key=x['HandleRefId']
   if key=='-1':return None
   assert key in handles and key not in active
   return rec(handles[key],active|{key})
  if 'HandleId' in x:return rec(x['Data'],active|{x['HandleId']})
  return {k:rec(v,active) for k,v in x.items()}
 return rec(obj)
def nodes(root):return {n['nodeId']['id']:n for n in root['sceneGraph']['graph']}
def successors(n):return [d['nodeId']['id'] for s in n.get('outputSockets',[]) for d in s['destinations']]
def reach(ns,start):
 todo=[start];seen=set()
 while todo:
  i=todo.pop()
  if i in seen:continue
  assert i in ns,('dangling scene edge',i)
  seen.add(i);todo.extend(successors(ns[i]))
 return seen

def service_policy(root,original):
 ns=nodes(root);src=nodes(original)
 assert [val(e['name']) for e in root['entryPoints']]==['in']
 assert reach(ns,root['entryPoints'][0]['nodeId']['id'])==set(ns)
 # Selected acquisition data, not incidental resource/path names, identifies cast.
 assert {a['actorName'] for a in root['actors']}=={'v_male_tpp','v_female_tpp'}
 for a in root['actors']:
  assert a in original['actors'] and a['acquisitionPlan']=='spawnDespawn'
  assert val(a['spawnDespawnParams']['specRecordId']) in {'Character.q110_tpp_male_v','Character.q110_tpp_female_v'}
  assert a['spawnDespawnParams']['spawnOnStart']==0 and a['spawnDespawnParams']['keepAlive']==0
 assert len(root['playerActors'])==1
 player=root['playerActors'][0]
 assert player['acquisitionPlan']=='findInContext'
 assert player['findActorInContextParams']['contextualName']=='Player'
 assert val(player['findActorInContextParams']['specRecordId'])=='Character.Player_Puppet_Base'
 actor_ids={a['actorId']['id'] for a in root['actors']+root['playerActors']}
 prop_ids={p['propId']['id'] for p in root['props']}
 actor_performers={i*256+1 for i in actor_ids}
 player_performer=player['actorId']['id']*256+1
 valid_performers=actor_performers|{i*256+2 for i in prop_ids}|{4294967040}
 for x in walk(root['sceneGraph']):
  if x.get('$type')=='scnActorId':assert x['id'] in actor_ids|{4294967295}
  if x.get('$type')=='scnPerformerId':assert x['id'] in valid_performers
  if x.get('$type')=='scneventsAttachPropToPerformer':
   assert x['performerId']['id']==player_performer and x['propId']['id'] in prop_ids
  if x.get('$type')=='questSetVar_NodeType':
   assert 'purchased' not in x['factName'] and 'kerry' not in x['factName'] and not x['factName'].startswith('mq055_')
 for p in root['props']:
  assert p in original['props']
  assert p['entityAcquisitionPlan'] in {'findInNode','spawnDespawn'}
  if p['entityAcquisitionPlan']=='spawnDespawn':
   assert p['spawnDespawnParams']['itemOwnerId']['id'] in {4294967040,player_performer}
 # Context metadata and authored V/prop workspots remain byte-equivalent logically.
 for k in set(original)-{'actors','sceneGraph','entryPoints','exitPoints'}:
  assert root[k]==original[k],('unexpected root metadata drift',k)
 # Changes to reachable native nodes are bounded to explicit routing/guard changes.
 expected=copy.deepcopy(src)
 def redirect(n,old,new):
  targets=[d for s in expected[n]['outputSockets'] for d in s['destinations'] if d['nodeId']['id']==old]
  assert len(targets)==1
  targets[0]['nodeId']['id']=new;targets[0]['isockStamp']['ordinal']=0
 def remove(n,target):
  before=successors(expected[n])
  assert before.count(target)==1
  for s in expected[n]['outputSockets']:s['destinations']=[d for d in s['destinations'] if d['nodeId']['id']!=target]
 def output(n,targets):
  template=copy.deepcopy(expected[n]['outputSockets'][0]['destinations'][0])
  ds=[]
  for ident,ordinal in targets:
   d=copy.deepcopy(template);d['nodeId']['id']=ident;d['isockStamp']['name']=0;d['isockStamp']['ordinal']=ordinal;ds.append(d)
  expected[n]['outputSockets'][0]['destinations']=ds
 output(1,[(215,0),(1112,1)]);output(1112,[(2,0)])
 remove(47,1163);remove(202,1173)
 if player['actorId']['id']!=4: # Kerry native scene has player ID4; all four ordinary scenes ID3.
  redirect(220,982,386);redirect(226,1000,397)
  v_branch=src[1156]['outputSockets'][1]['destinations'];assert len(v_branch)==1
  redirect(222,1156,v_branch[0]['nodeId']['id']);remove(242,1084);redirect(242,509,2)
  for option in expected[1125]['options'][:5]:
   assert any(v.get('factName')=='mirror_interactions_facials' for v in walk(option['questCondition']))
   option['questCondition']=None
 removed_actors={a['actorId']['id'] for a in original['actors'] if a['actorName'] in {'johnny_mirror','kerry'}}
 for i,n in expected.items():
  writes=[v for v in walk(n) if v.get('$type')=='questSetVar_NodeType' and v['factName'].startswith('mq055_')]
  if writes:expected[i]={k:n[k] for k in ['ffStrategy','nodeId','outputSockets']}|{'$type':'scnHubNode'}
  elif 'actorBehaviors' in n:
   removed=[a for a in n['actorBehaviors'] if a['actorId']['id'] in removed_actors]
   assert all(a['behaviorMode']=='OnlyIfAlive' for a in removed)
   n['actorBehaviors']=[a for a in n['actorBehaviors'] if a['actorId']['id'] not in removed_actors]
 expected_reach=reach(expected,1)
 assert set(ns)==expected_reach
 for i,n in ns.items():assert n==expected[i],('unexpected native node drift',i)
 assert root['exitPoints']==[e for e in original['exitPoints'] if e['nodeId']['id'] in expected_reach]
 return {'actors':[a['actorName'] for a in root['actors']],'player_actor_id':player['actorId']['id'],'nodes':len(ns),'props':len(prop_ids),'prop_item_owners':[{'name':p['propName'],'owner':p['spawnDespawnParams']['itemOwnerId']['id']} for p in root['props'] if p['entityAcquisitionPlan']=='spawnDespawn'],'native_node_checks':len(ns)}

def purchase_policy(root,original,identity):
 ns=nodes(root);src=nodes(original)
 assert [val(e['name']) for e in root['entryPoints']]==['in_purchase']
 start=root['entryPoints'][0]['nodeId']['id']
 assert len(ns)==5 and reach(ns,start)==set(ns)
 assert root['actors']==[] and root['props']==[] and root['workspots']==[] and root['workspotInstances']==[]
 choices=[n for n in ns.values() if n['$type']=='scnChoiceNode'];assert len(choices)==1
 choice=choices[0];assert len(choice['options'])==1 and choice['mode']=='attachToWorld'
 assert choice['atwParams']==src[choice['nodeId']['id']]['atwParams']
 opt=choice['options'][0]
 assert opt['blueline']==0 and opt['bluelineCondition'] is None and val(opt['gameplayAction'])=='0'
 expected_ready={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRH1_'+identity+'_PurchaseReady','value':1}}
 assert opt['questCondition']==expected_ready
 writes=[v for v in walk(root['sceneGraph']) if v.get('$type')=='questSetVar_NodeType']
 assert [(v['factName'],v['setExactValue'],v['value']) for v in writes]==[('PTFRH1_'+identity+'_PurchaseRequest',1,1)]
 assert not any(('Payment' in v.get('$type','')) or v.get('$type') in {'questAddRemoveItem_NodeType','questRewardManagerNodeDefinition'} for v in walk(root['sceneGraph']))
 ready_conditions=[v for v in walk(root['sceneGraph']) if v.get('$type')=='questVarComparison_ConditionType']
 assert {(v['factName'],v['comparisonType'],v['value']) for v in ready_conditions}=={('PTFRH1_'+identity+'_PurchaseReady','Equal',0),('PTFRH1_'+identity+'_PurchaseReady','Equal',1)}
 writer=next(n for n in ns.values() if any(v.get('$type')=='questSetVar_NodeType' for v in walk(n)))
 assert successors(choice)==[writer['nodeId']['id']] and successors(writer)==[2] and ns[2]['$type']=='scnEndNode'
 return {'nodes':5,'selection_writes':[v['factName'] for v in writes],'payment_nodes':0,'native_owned_writes':0,'actor_acquisitions':0}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('component');ap.add_argument('--out',required=True);args=ap.parse_args()
 component_path=ROOT/args.component;out=ROOT/args.out;assert not out.exists()
 c=read(component_path);folder=component_path.parent;pins={};checks=0;results=[];cases=[]
 def pin(p):pins[Path(p).relative_to(ROOT).as_posix()]=sha(p)
 pin(component_path);pin(Path(__file__))
 for p,h in c['source_pins'].items():assert sha(ROOT/p)==h,p;checks+=1
 for inp in c['presentation']['inputs']:
  rb=folder/'readback'/(inp['depot'].rsplit('\\',1)[-1]+'.json')
  source=ROOT/inp['source']['json'];actual=resolve(read(rb)['Data']['RootChunk']);original=resolve(read(source)['Data']['RootChunk'])
  for p in [rb,source,ROOT/inp['source']['raw'],ROOT/inp['expected']]:pin(p)
  assert actual==resolve(read(ROOT/inp['expected'])['Data']['RootChunk']);checks+=1
  if inp['kind']=='services':
   result=service_policy(actual,original);checks+=result['native_node_checks']+len(actual['props'])+12
   bad=copy.deepcopy(actual);bad['actors'][0]['spawnDespawnParams']['specRecordId']['$value']='Character.Silverhand'
   try:service_policy(bad,original)
   except AssertionError:cases.append(inp['id']+'_excluded_actor')
   else:raise AssertionError('excluded actor mutation escaped')
  else:
   result=purchase_policy(actual,original,inp['id']);checks+=16
   bad=copy.deepcopy(actual);choice=next(n for n in nodes(bad).values() if n['$type']=='scnChoiceNode');choice['options'][0]['blueline']=1
   try:purchase_policy(bad,original,inp['id'])
   except AssertionError:cases.append(inp['id']+'_native_payment')
   else:raise AssertionError('native payment mutation escaped')
  results.append({'id':inp['id'],'kind':inp['kind'],'readback':rb.relative_to(ROOT).as_posix(),**result})
 proof={'status':'PASS_INDEPENDENT_NATIVE_SCENE_SCOPE_NOT_LIVE','component_sha256':sha(component_path),'reviewer_sha256':sha(__file__),'checks':checks,'policy_cases':len(cases),'negative_cases':cases,'source_pins':pins,'scenes':results,'scope':['Nine final native scene readbacks; actual selected V actor acquisition and all reachable performer references; explicit native graph delta comparison.','Four original purchase anchors retain only request selection, with no native payment/item/reward or owned-fact writers.','Five service scenes retain original V props/workspots; removed Johnny/Kerry acquisition is absent and no reachable event references those performers.'],'limits':['This is source and packed-readback proof, not live scene playback or device lifecycle proof.','Quest owner/payment-ledger protocols are reviewed by their separate component tests and aggregate review.'],'game_writes':0}
 out.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in proof.items() if k not in ['source_pins','scenes']}))
if __name__=='__main__':main()
