"""S25 native service slices, legacy scene equivalence and admission safeguards."""
import copy,importlib.util,json,sys
from pathlib import Path
from inspect import SafeResource,nodes as scene_nodes,reach,read,walk,value,graphs
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('s22_tests',ROOT/'prealpha/sidejobs_s22/delamain_v2/test.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
sha=m.sha
def evaluate(c,f,j):
 if c.get('$type')=='questLogicalCondition':
  vals=[evaluate(x,f,j) for x in c['conditions']]
  return {'AND':all(vals),'OR':any(vals),'NOR':not any(vals)}[c['operation']]
 if c.get('$type')=='questObjectCondition' and c['type'].get('$type')=='questInventory_ConditionType':
  assert c['type']['comparisonType']=='Less' and c['type']['quantity']==1 and c['type']['isPlayer']==1
  return f.get('_dying_night_quantity',None) is not None and f['_dying_night_quantity']<1
 return m.evaluate(c,f,j)
def nmap(g):return {n['id']:n for n in g['nodes']}
def es(g):return {tuple(e) for e in g['edges']}
def jsonof(raw):return ROOT/(raw.replace('/raw/','/json/')+'.json')
def scene(p):
 r=SafeResource(read(p));return r.payload(r.obj['Data']['RootChunk'])
def sn(r):return {n['nodeId']['id']:n for n in r['sceneGraph']['graph']}
def sedges(n):return [[[d['nodeId']['id'],d['isockStamp']['ordinal']] for d in s['destinations']] for s in n['outputSockets']]
def verify(build):
 manifest=read(build/'build.json');contract=read(ROOT/manifest['contract']);checks=cases=0
 def source(raw):return build/manifest['native_readbacks'][raw]
 for p,h in manifest['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in manifest['resources'].items():assert sha(build/'source'/p)==h,p
 for s in contract['owners']:
  native=nmap(graphs(source(s['native_source']))[s['source_graph']]);g=graphs(build/'readback'/(s['key'].lower()+'.json'))['root'];actual=nmap(g)
  for i in s['native_ids']:assert actual[i]==native[i],(s['key'],i);checks+=1
  expected={tuple(e) for e in s['native_edges']}|{(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'False',1002,'In'),(1003,'True',1004,'In')}
  if s['key']=='GUN':expected|={(1004,'Out',1006,'In'),(1006,'Out',1005,'In'),(1005,'Out',51,'Active'),(1005,'Out',52,'In'),(1005,'Out',1008,'In'),(1008,'Out',1007,'In')}
  else:expected|={(1004,'Out',1005,'In'),(1005,'Out',s['native_start'],s['native_start_socket']),(s['native_finish'],'Out',1007,'In')}
  assert es(g)==expected;checks+=1
  assert actual[1002]['condition']==actual[1003]['condition'];checks+=1
  good=manifest['common_equal']|s['facts_equal']|{k:v['min'] for k,v in s['fact_ranges'].items()}|{s['tag']+'_Permit':1,s['tag']+'_Issued':0,s['tag']+'_Finished':0,s['tag']+'_Fault':0}
  if s['key']=='GUN':good['_dying_night_quantity']=0
  js={j['path']:'Inactive' for j in s['journals']};cond=actual[1002]['condition']
  assert evaluate(cond,good,js);cases+=1
  for k,v in good.items():
   if k=='_dying_night_quantity':continue
   bounds=s['fact_ranges'].get(k,{'min':v,'max':v})
   for alt in {-1,0,1,2,3,99,2147483647,bounds['min']-1,bounds['max']+1}:
    assert evaluate(cond,good|{k:alt},js)==(bounds['min']<=alt<=bounds['max']),(s['key'],k,alt);cases+=1
  for path in js:
   for state in (None,'Active','Succeeded','Failed'):
    assert not evaluate(cond,good,js|{path:state}),(s['key'],path,state);cases+=1
  cur=next(j for j in read(ROOT/contract['capture'])['second']['jobs'] if j['id']==s['id'])
  assert cur['rootState']=='Succeeded'
  assert not evaluate(cond,good,js|{j['path']:j['state'] for j in cur['journals']});cases+=1
  for n in actual.values():
   if n['id'] in s['native_ids']:continue
   if s['key']=='GUN' and n['id']==1006:continue
   if n['$type']=='questFactsDBManagerNodeDefinition':assert n['type']['factName'].startswith(s['tag']+'_')
   else:assert n['$type'] in ('questInputNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition')
  if s['key']=='PAID':
   old=SafeResource(read(source(s['scene_current'])));new=SafeResource(read(build/'readback/viktor_scene.json'));donor=SafeResource(read(source(s['scene_native'])))
   before=old.payload(old.obj['Data']['RootChunk']);after=new.payload(new.obj['Data']['RootChunk']);stock=donor.payload(donor.obj['Data']['RootChunk'])
   bn=sn(before);an=sn(after);dn=sn(stock)
   assert set(bn)==set(an)==set(dn)
   for i,n in an.items():
    if i not in (351,840):assert n==bn[i],('unrelated Viktor node changed',i);checks+=1;continue
    expectednode=copy.deepcopy(bn[i]);expectednode['options'][1]=copy.deepcopy(dn[i]['options'][1]);expectednode['outputSockets'][1]=copy.deepcopy(dn[i]['outputSockets'][1])
    condition=n['options'][1]['questCondition'];children=condition['conditions']
    assert condition['operation']=='AND' and len(children)==5
    assert children[3]==dn[i]['options'][1]['questCondition']
    guard=copy.deepcopy(condition);guard['conditions'].pop(3)
    root=s['journals'][0]['path']
    assert evaluate(guard,{s['tag']+'_Issued':1,s['tag']+'_Finished':0,s['tag']+'_Fault':0},{root:'Active'});cases+=1
    for state in (None,'Inactive','Succeeded','Failed'):
     assert not evaluate(guard,{s['tag']+'_Issued':1,s['tag']+'_Finished':0,s['tag']+'_Fault':0},{root:state});cases+=1
    for f in ('Issued','Finished','Fault'):
     fs={s['tag']+'_Issued':1,s['tag']+'_Finished':0,s['tag']+'_Fault':0};fs[s['tag']+'_'+f]=0 if f=='Issued' else 1
     assert not evaluate(guard,fs,{root:'Active'});cases+=1
    expectednode['options'][1]['questCondition']=copy.deepcopy(condition)
    assert n==expectednode;checks+=1
    # Balanced native payment metadata unchanged: exact debit logic, not a
    # replacement SetFact or synthetic subtraction added by this component.
    assert n['options'][1]['bluelineCondition']==dn[i]['options'][1]['bluelineCondition'];checks+=1
   before['sceneGraph']=after['sceneGraph']
   assert before==after,'Non-graph Viktor header/actor/props changed';checks+=1
   added=reach(an,[1,640])-reach(bn,[1,640])
   assert added=={50,156,324,454,1129,1132,1136,1141,1144},added;checks+=1
   for i in added:assert an[i]==dn[i],('New debt reachable payload differs from stock',i);checks+=1
   assert an[454]['questNode']['type']=={'$type':'questSetVar_NodeType','factName':'victor_debt_paid_full','setExactValue':0,'value':1}
   assert actual[12]['condition']['type']['factName']=='victor_debt_paid_full'
   assert actual[11]['type']['path']['realPath']==root
   assert not any(n.get('type',{}).get('factName')=='CYB-571237' for n in actual.values());checks+=4
  if s['key']=='GUN':
   for qty in (None,1,2,99):assert not evaluate(cond,good|{'_dying_night_quantity':qty},js);cases+=1
   dn=sn(scene(source(s['scene_native'])));sh=sn(scene(source(s['shop_current'])))
   inv=copy.deepcopy(dn[281]['questNode']['condition']);inv['type']['comparisonType']='Less'
   assert cond['conditions'][-1]==inv;checks+=1
   ct=nmap(graphs(source(s['contact_source']))['root'])[168];ct=copy.deepcopy(ct);ct['id']=1006;ct['type']['params'][0]['contact']['realPath']='contacts/wilson'
   assert actual[1006]==ct;checks+=1
   for state in ('Inactive','Active','Failed',None,'Succeeded'):
    assert evaluate(actual[1008]['condition'],{}, {s['journals'][0]['path']:state})==(state=='Succeeded');cases+=1
   after=scene(build/'readback/gun_scene.json');an=sn(after)
   assert set(an)==set(s['scene_ids'])==reach(an,[0]);checks+=1
   for i,n in an.items():
    expectednode=copy.deepcopy(sh[i] if i in (0,224,678) else dn[i])
    assert sedges(n)==s['scene_edges'][str(i)],i
    # Destination stamps are valid native ordinals; only declared routes differ.
    for o in n['outputSockets']:
     for d in o['destinations']:assert d['isockStamp']['name']==0 and d['nodeId']['id'] in an;checks+=1
    expectednode['outputSockets']=copy.deepcopy(n['outputSockets'])
    if i==177:expectednode['options'].pop(1)
    if i==512:expectednode['questNode']['condition']['type']['sceneFile']['DepotPath']['$value']=s['scene_depot']
    assert n==expectednode,('gun payload',i);checks+=1
   assert after['props']==[] and len(after['entryPoints'])==1 and after['entryPoints'][0]['nodeId']['id']==0;checks+=1
   before=scene(source(s['scene_native']))
   for key in before:
    if key not in ('sceneGraph','props','entryPoints'):assert before[key]==after[key],('scene header',key);checks+=1
   for n in an.values():
    assert not any(x.get('$type')=='scnPropId' and x.get('id')!=4294967295 for x in walk(n)),n['nodeId']
    assert not any(x.get('factName') in ('q001_spawn_wilson_attention','q101_spawn_wilson_attention') for x in walk(n));checks+=2
   assert an[212]==dn[212] and an[281]==dn[281] and an[430]==dn[430] and an[209]==dn[209] and an[369]==dn[369];checks+=5
   oldg=graphs(source(s['body_current']))['root'];newg=graphs(build/'readback/wilson_body.json')['root'];bn=nmap(oldg);nn=nmap(newg)
   for i,n in bn.items():assert nn[i]==n,('old body payload',i);checks+=1
   request=copy.deepcopy(bn[5]);request['id']=101;request['sceneFile']['DepotPath']['$value']=s['scene_depot'];assert nn[101]==request;checks+=1
   changed={(4,'Out',100,'In'),(100,'False',5,'wilson_default_in'),(100,'True',101,'wilson_default_in'),(12,'CutSource',101,'CutDestination')}
   assert es(newg)==(es(oldg)-{(4,'Out',5,'wilson_default_in')})|changed;checks+=1
   # Non-S25 selector collapses exactly to the installed graph: original actors,
   # spawn actions, wanted interruption and normal shop path remain authoritative.
   assert (es(newg)-changed)|{(4,'Out',5,'wilson_default_in')}==es(oldg);checks+=1
   selector=nn[100]['condition'];root=s['journals'][0]['path']
   for issued in (0,1):
    for finished in (0,1):
     for fault in (0,1):
      for state in (None,'Inactive','Active','Succeeded','Failed'):
       fs={s['tag']+'_Issued':issued,s['tag']+'_Finished':finished,s['tag']+'_Fault':fault}
       assert evaluate(selector,fs,{root:state})==(issued==1 and finished==0 and fault==0 and state in ('Inactive','Active'));cases+=1
   assert s['body_depot'] in manifest['mod_overrides'] and not any(p.endswith('owner.questphase') for p in manifest['resources']);checks+=1
   assert not any(x.get('$type')=='questSpawnManagerNodeDefinition' for x in actual.values());checks+=1
   # No new Near writer and no attention writers: original B0 controller remains
   # sole proximity owner and S23 MQ011 lease file is only pinned, not shipped.
   assert not any(x.get('factName') in ('PTFRB0WV_Near','q001_spawn_wilson_attention') and x.get('$type')=='questSetVar_NodeType' for n in actual.values() for x in walk(n));checks+=1
 return {'status':'PASS_STATIC_NOT_LIVE','native_payload_checks':checks,'policy_cases':cases,'component_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'owners':len(contract['owners']),'existing_completed_roots_protected':True,'native_progress_resets':False,'game_writes':False}
if __name__=='__main__':
 build=HERE/'build'/sys.argv[1];out=build/'tests.json';assert not out.exists(),out
 result=verify(build);out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
