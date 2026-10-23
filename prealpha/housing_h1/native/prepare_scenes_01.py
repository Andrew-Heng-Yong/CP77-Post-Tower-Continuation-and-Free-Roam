"""Build private, bounded housing scene JSON from current official resources."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import walk,value
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest().upper()
MOD='towercontinued\\housing_h1\\native\\'
def main():
 out=Path(sys.argv[1]).resolve();assert not out.exists();out.mkdir(parents=True)
 catalog=read('research/housing_h1/native/catalog_01.json');inv=read('research/housing_h1/native/official_01/inventory.json');sources={r['depot']:r for r in inv['rows']}
 pins={};inputs=[];purchase=[]
 def pin(p):pins[p]=sha(p)
 for p in ['prealpha/housing_h1/native/prepare_scenes_01.py','research/housing_h1/native/catalog_01.json','research/housing_h1/native/official_01/inventory.json']:pin(p)
 def emit(id,kind,obj,src,changes):
  name=id+'_'+kind+'.scene';p=out/(name+'.json');p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8');inputs.append({'depot':MOD+name,'expected':p.relative_to(ROOT).as_posix(),'source':src,'kind':kind,'id':id,'changes':changes})
 for row in catalog['properties']+[{'id':'kerry','service_scene':r'dlc\dlc6_apart\scenes\dlc6_apart_kerry_villa_interactions.scene'}]:
  id=row['id']
  if id=='h10':continue
  src=sources[row['service_scene']]
  for p in [src['json'],src['raw']]:pin(p)
  original=read(src['json'])
  def context(obj):
   root=obj['Data']['RootChunk'];handles=root['sceneGraph']['Data']['graph'];nodes={h['Data']['nodeId']['id']:h['Data'] for h in handles};return root,handles,nodes
  obj=copy.deepcopy(original);root,handles,ns=context(obj);changes=[]
  def setout(n,ids,ordinal=0):
   template=copy.deepcopy(ns[n]['outputSockets'][0]['destinations'][0]);ds=[]
   for target in ids:
    e=copy.deepcopy(template);e['nodeId']['id']=target;e['isockStamp']['name']=0;e['isockStamp']['ordinal']=ordinal;ds.append(e)
   ns[n]['outputSockets'][0]['destinations']=ds;changes.append({'node':n,'socket':0,'targets':ids,'ordinal':ordinal})
  def replace_edge(n,old,new):
   hits=[d for s in ns[n]['outputSockets'] for d in s['destinations'] if d['nodeId']['id']==old];assert len(hits)==1,(id,n,old)
   hits[0]['nodeId']['id']=new;hits[0]['isockStamp']['ordinal']=0;changes.append({'node':n,'replace':old,'with':new})
  def remove_edge(n,target):
   count=0
   for s in ns[n]['outputSockets']:
    before=len(s['destinations']);s['destinations']=[d for d in s['destinations'] if d['nodeId']['id']!=target];count+=before-len(s['destinations'])
   assert count==1,(id,n,target);changes.append({'node':n,'remove':target})
  # Existing H10 precedent: ordinary action hub plus native outside watcher.
  setout(1,[215,1112]);next(d for d in ns[1]['outputSockets'][0]['destinations'] if d['nodeId']['id']==1112)['isockStamp']['ordinal']=1
  setout(1112,[2]);root['entryPoints']=[e for e in root['entryPoints'] if value(e['name'])=='in']
  # Keep normal water/workspot cleanup, omit old clothing stash path as H10 does.
  remove_edge(47,1163);remove_edge(202,1173)
  if id!='kerry':
   replace_edge(220,982,386);replace_edge(226,1000,397)
   vchoice=ns[1156]['outputSockets'][1]['destinations'];assert len(vchoice)==1
   replace_edge(222,1156,vchoice[0]['nodeId']['id'])
   remove_edge(242,1084);replace_edge(242,509,2)
   # Facial expressions belong to this private V-only mirror, not a global controller fact.
   for option in ns[1125]['options'][:5]:
    assert any(v.get('factName')=='mirror_interactions_facials' for v in walk(option['questCondition']));option['questCondition']=None
   changes.append({'node':1125,'local_facials':5})
  # Keep action flow but suppress excluded dating-controller observation writes.
  for h in handles:
   n=h['Data'];writes=[v for v in walk(n) if v.get('$type')=='questSetVar_NodeType' and v['factName'].startswith('mq055_')]
   if writes:
    assert n['$type']=='scnQuestNode' and len(n['outputSockets'])==1
    new={'$type':'scnHubNode','ffStrategy':n['ffStrategy'],'nodeId':n['nodeId'],'outputSockets':n['outputSockets']};h['Data']=new;ns[n['nodeId']['id']]=new;changes.append({'node':n['nodeId']['id'],'removed_dating_writes':[v['factName'] for v in writes]})
  def reachable(nodes,start):
   seen=set();todo=[start]
   while todo:
    i=todo.pop()
    if i in seen:continue
    assert i in nodes,(id,'dangling',i);seen.add(i)
    todo.extend(d['nodeId']['id'] for s in nodes[i].get('outputSockets',[]) for d in s['destinations'])
   return seen
  reach=reachable(ns,1)
  # Excluded acquisition is removed, and no surviving event/command may reference it.
  excluded={a['actorId']['id'] for a in root['actors'] if value(a['actorName']) in ['johnny_mirror','kerry']}
  refs=[]
  for i in reach:
   for v in walk(ns[i]):
    if v.get('$type')=='scnActorId' and v.get('id') in excluded:refs.append((i,'actor',v['id']))
    if v.get('$type')=='scnPerformerId' and v.get('id') in {x*256+1 for x in excluded}:refs.append((i,'performer',v['id']))
  assert not refs,(id,'excluded actor reachable',refs)
  root['actors']=[a for a in root['actors'] if a['actorId']['id'] not in excluded]
  root['sceneGraph']['Data']['graph']=[h for h in handles if h['Data']['nodeId']['id'] in reach]
  root['exitPoints']=[e for e in root['exitPoints'] if e['nodeId']['id'] in reach]
  changes.append({'reachable_nodes':sorted(reach),'excluded_actor_ids':sorted(excluded)})
  assert not any(v.get('$type')=='questSetVar_NodeType' and ('purchased' in v['factName'] or 'kerry' in v['factName'] or v['factName'].startswith('mq055_')) for h in root['sceneGraph']['Data']['graph'] for v in walk(h))
  emit(id,'services',obj,src,changes)
  if id=='kerry':continue
  obj=copy.deepcopy(original);root,handles,ns=context(obj);changes=[]
  entry=next(e['nodeId']['id'] for e in root['entryPoints'] if value(e['name'])=='in_purchase');targets=ns[entry]['outputSockets'][0]['destinations'];choice=next(d['nodeId']['id'] for d in targets if ns[d['nodeId']['id']]['$type']=='scnChoiceNode');watch=next(d['nodeId']['id'] for d in targets if ns[d['nodeId']['id']]['$type']=='scnQuestNode')
  writers=[n['nodeId']['id'] for n in ns.values() if any(v.get('$type')=='questSetVar_NodeType' and v['factName']==row['native_purchase_fact'] for v in walk(n))];assert len(writers)==1;writer=writers[0]
  n=ns[choice];assert len(n['options'])==1 and n['mode']=='attachToWorld'
  hid=max(int(v['HandleId']) for v in walk(obj) if 'HandleId'in v)+1
  def handle(data):
   nonlocal hid
   h={'HandleId':str(hid),'Data':data};hid+=1;return h
  fact={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRH1_'+id+'_PurchaseReady','value':1}
  n['options'][0]['questCondition']=handle({'$type':'questFactsDBCondition','type':handle(fact)});n['options'][0]['blueline']=0;n['options'][0]['bluelineCondition']=None
  setout(choice,[writer],1)
  for s in n['outputSockets'][1:]:s['destinations']=[]
  setout(writer,[2]);w=next(v for v in walk(ns[writer]) if v.get('$type')=='questSetVar_NodeType');w['factName']='PTFRH1_'+id+'_PurchaseRequest';w['value']=1;w['setExactValue']=1
  w=next(v for v in walk(ns[watch]) if v.get('$type')=='questVarComparison_ConditionType');w.update(factName='PTFRH1_'+id+'_PurchaseReady',comparisonType='Equal',value=0);setout(watch,[2])
  root['entryPoints']=[e for e in root['entryPoints'] if e['nodeId']['id']==entry];root['exitPoints']=[e for e in root['exitPoints'] if e['nodeId']['id']==2]
  reach=reachable(ns,entry);assert reach=={entry,choice,watch,writer,2};root['sceneGraph']['Data']['graph']=[h for h in handles if h['Data']['nodeId']['id'] in reach]
  root['actors']=[];root['props']=[];root['workspots']=[];root['workspotInstances']=[]
  purchase.append({'id':id,'scene':MOD+id+'_purchase.scene','entry':'in_purchase','exit':'out','choice':choice,'local_position':n['atwParams']['entityPosition'],'local_orientation':n['atwParams']['entityOrientation'],'native_scene_marker':'#dlc6_sm_apart_'+row['native_purchase_fact'].removeprefix('dlc6_apart_').removesuffix('_purchased')+'_interactions','request_fact':'PTFRH1_'+id+'_PurchaseRequest','ready_fact':'PTFRH1_'+id+'_PurchaseReady','source':src})
  emit(id,'purchase',obj,src,changes)
 result={'status':'PREPARED_PRIVATE_HOUSING_SCENES','inputs':inputs,'purchase':purchase,'source_pins':pins};(out/'prepared.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'scenes':len(inputs),'purchase':len(purchase)}))
if __name__=='__main__':main()
