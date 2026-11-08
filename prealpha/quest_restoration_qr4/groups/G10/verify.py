"""G10 Dakota gig contracts, using exact native recipe donors and current QR3 bytes.
Run --output NEW_DIRECTORY. All mutations are in-memory raw-resource copies.
"""
from pathlib import Path
import sys,json,gzip,collections,copy,argparse,re
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');WORK=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'
MAN=W/'research/gig_restoration/native_gigs_u9/manifest.json';MF=read(MAN);MANPINS={k.replace('\\','/'):v for k,v in MF['source_pins'].items()};PLANPATH=MAN.parent/'build_plan.json';PLAN=read(PLANPATH)
HC=r'base\quest\holocalls\dakota\dakota_holocall.questphase';HS=HC.replace('.questphase','.scene');CL=HC.replace('_holocall','_cleanup');SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
SPECS={
 'sts_bls_ina_05':dict(title='Goodbye, Night City',parent=5,body=9,poi=46,ow='phases/sts_bls_ina_05_openworld_phase.questphase',gpl='phases/sts_bls_ina_05_gameplay_phase.questphase',finished_graph='root/2',finished_node=294,credit_wait=10,branch='Bruce rescue/leave-alone and optional pacifist outcomes; native root/2 and root/9 debrief routes remain distinct.'),
 'sts_bls_ina_04':dict(title='Radar Love',parent=5,body=8,poi=43,ow='phases/sts_bls_ina_04_openworld.questphase',gpl='phases/sts_bls_ina_04_gameplay.questphase',finished_graph='root/3',finished_node=195,credit_wait=9,branch='Native stolen-van delivery/failure outcomes; credit_alias1 is the deliberate same-job native credit lineage, not a second independent award.'),
 'sts_bls_ina_03':dict(title='Flying Drugs',parent=3,body=7,poi=72,ow='phases/sts_bls_ina_03_ow.questphase',gpl='phases/sts_bls_ina_03_gpl.questphase',finished_graph='root/4',finished_node=12,credit_wait=2,branch='Sabotaged antenna and hacked antenna alternatives preserve native fact spellings, including ina_03_antenna_sbotaged and #ina_03_antenna_hacked; normal/pacifist rewards remain distinct.'),
 'sts_bls_ina_02':dict(title="Big Pete's Got Big Problems",parent=4,body=2,poi=41,ow='phases/sts_bls_ina_02_ow.questphase',gpl='phases/sts_bls_ina_02_gpl.questphase',finished_graph='root/72',finished_node=91,credit_wait=4,branch='Native kill/spare Big Pete outcomes and debrief/SMS alternatives remain; no forced death, synthetic spared receipt or arbitrary AI command.'),
}
def path(g,a,b):
 q=collections.deque([[str(a)]]);s={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,so,y,si in g['edges']:
   if x==p[-1] and so!='CutSource' and si!='CutDestination' and y not in s:s.add(y);q.append(p+[y])
 return None
def ev(x,fs,js):
 t=x['$type']
 if t=='questLogicalCondition':
  a=[ev(y,fs,js) for y in x['conditions']];return all(a) if x['operation']=='AND' else any(a) if x['operation']=='OR' else not any(a) if x['operation']=='NOR' else False
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],fs,js)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in fs:return False
  a=fs[x['factName']];b=x['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return x['path']['realPath'] in js and ((js[x['path']['realPath']]==x['state'])!=bool(x.get('inverted',0)))
 raise ValueError(t)
def fixture(c):
 fs={};js={}
 for x in walk(c):
  if x.get('$type')=='questVarComparison_ConditionType':fs[x['factName']]=x['value']+1 if x['comparisonType']=='Greater' else x['value']-1 if x['comparisonType']=='Less' else x['value']
  if x.get('$type')=='questJournalEntryState_ConditionType':js.setdefault(x['path']['realPath'],x['state'])
 return fs,js
def run(O):
 assert not O.exists(),'Fresh output required';checks=[];pins=[];models={};raws={};evidence={};mutations=[]
 def check(name,ok,evidence,q=None):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',quest_id=q,evidence=evidence));assert ok,name
 queue=read(W/'prealpha/quest_restoration_qr3/queue.json');Q={q['id']:q for q in queue['quests'] if q['id'] in SPECS};check('effective queue four identities',set(Q)==set(SPECS),list(Q))
 check('pinned U9 approved build plan',sha(PLANPATH)==MF['plan_sha256'],str(PLANPATH))
 corepath=H.parent/'G09/shared_core.json';core=read(corepath);check('frozen Dakota shared core',sha(corepath)=='BDD1BB748A68160491FE98715951DAD7C79D8CB8233333255C250D2FF060A857',str(corepath))
 for k in ['tests','source_pins']:check('shared core artifact '+k,sha(core[k])==core[k+'_sha256'],core[k])
 for pin in core['sources']:check('shared core current source '+pin['depot'],sha(pin['binary'])==pin['resource_sha256'] and sha(pin['json'])==pin['json_sha256'],pin['binary'])
 scriptrel='r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds';script=WORK.parent/'package'/scriptrel;epoch=read(H.parents[1]/'source_epoch_00.json');sp=next(x for x in epoch['package_files'] if x['path']==scriptrel);check('effective consolidated producer script epoch pin',sha(script)==sp['sha256'],str(script));code=script.read_text(encoding='utf8');producer=code.split('public class NativeGigsU9 extends ScriptableSystem {',1)[1].split('public class NativeGigsTickU9',1)[0];catalog=code.split('public abstract class NativeGigDataU9 {',1)[1].split('public class NativeGigsU9',1)[0]
 ids=json.loads(re.search(r'func IDs\(\).*?return (\[.*?\]);',catalog).group(1))
 def data(method,index):
  body=re.search(r'func '+method+r'\(i: Int32\).*?(?=public static func|\Z)',catalog,re.S).group(0);m=re.search(r'if i\s*==\s*'+str(index)+r'\s*\{\s*return (\[.*?\]);',body)
  return json.loads(m.group(1)) if m else []
 for needle in ['if this.State(paths[k],classes[k])!=1 { return false; }','if this.Fact(a[k])!=0 { return false; }','if !this.EntrySafe(i)','this.Own(id,"Started")!=0','this.OldUnused(k) && this.EntrySafe(k)','this.Root(k)==1 && !this.Terminal(k)']:
  check('effective producer guard '+needle,needle in producer,dict(script=str(script),source=needle))
 pins.append(dict(depot='CURRENT_CONSOLIDATED_REDSCRIPT',binary=str(script),sha256=sha(script),source_epoch_pin=sp['sha256']))
 recipes=[r for r in MF['recipes'] if r.get('id') in SPECS];deps={HC,HS,CL,SH}
 for q,x in Q.items():deps.update(x['restored_candidates']);deps.update(d for d in x['vanilla_candidates'] if '\\'+q+'\\' in d)
 for d in sorted(deps):
  r=IDX[d];j=Path(r['json']);raw=WORK/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
  if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
  check('current source '+d,raw.is_file() and sha(raw)==r['sha256'],str(raw));raws[d]=read(j);m=Resource(raws[d]).normalize();check('decoded graph '+d,not m['errors'],m['errors']);models[d]=m
  pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),source_json=str(j),json_sha256=sha(j),provider=r['archive']))
 donors={}
 for rr in recipes:
  p=rr['raw']
  if p in donors:continue
  j=p.replace('/raw/','/json/')+'.json';expected=MANPINS.get(p)
  check('vanilla donor binary recorded '+p,(sha(W/p)==expected) if expected else (W/p).is_file(),dict(path=p,historical_raw_hash=expected,limit=None if expected else 'Manifest pins JSON only; raw hash measured now, no historical raw-pin assertion'))
  check('manifest exact vanilla donor JSON '+j,sha(W/j)==MANPINS[j],j)
  donors[p]=Resource(read(W/j)).normalize();check('native donor parses '+p,not donors[p]['errors'],donors[p]['errors']);pins.append(dict(depot='NATIVE_RECIPE_DONOR',binary=str(W/p),sha256=sha(W/p),source_json=str(W/j),json_sha256=sha(W/j),historical_raw_hash=expected,limit=None if expected else 'Historical manifest raw hash absent; source comparison is pinned native JSON evidence'))
 def g(d,gp='root'):return models[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
 def writes(node,f,v):return any(x.get('factName')==f and x.get('value')==v for x in node['writes'])
 for q,s in SPECS.items():
  er=next(r for r in recipes if r['id']==q and r['kind']=='entry');entry=er['depot'];main=er['native'];s.update(entry=entry,native=main);base='base\\open_world\\street_stories\\badlands\\inland_avenue\\'+q+'\\';ow=base+s['ow'].replace('/','\\');s['openworld']=ow;s['gameplay']=base+s['gpl'].replace('/','\\');pfx='PTFRU9_'+q
  rr=[r for r in recipes if r['id']==q];copied=[]
  for r in rr:
   d=r['depot'];dg=donors[r['raw']]['graphs'][r['graph']]
   for i in r['ids']:
    if i==0:continue
    expected=copy.deepcopy(dg['nodes'][str(i)]['payload']);adaptation=None
    if d==entry and i==s['body'] and expected.get('phaseResource',{}).get('Flags')=='Embedded':
     expected['phaseResource']['Flags']='Soft';adaptation='Existing Embedded→Soft external reference to same exact native body depot'
    check('native recipe payload '+q+d+str(i),n(d,i)['payload']==expected,dict(depot=d,node=i,native_binary=r['raw'],native_graph=r['graph'],approved_reference_adaptation=adaptation),q)
   # All copied inline graphs retain exact native nodes/sockets/connections.
   for gp,gr in models[d]['graphs'].items():
    if gp=='root':continue
    sourcegp=r['graph']+gp[len('root'):];expected_graph=copy.deepcopy(donors[r['raw']]['graphs'][sourcegp]);approved_edits=[]
    if r['kind']=='entry':
     for edit in next(j for j in PLAN['jobs'] if j['id']==q)['parent'].get('edits',[]):
      if edit['graph']!=sourcegp:continue
      old=list(map(str,edit['remove']));new=list(map(str,edit['add'])) if edit.get('add') else None;expected_graph['edges'].remove(old)
      if new:expected_graph['edges'].append(new)
      approved_edits.append(edit)
     expected_graph['edges'].sort();seen=reachable(expected_graph['nodes'],expected_graph['edges'],expected_graph['entries'].values());expected_graph['reachable']=sorted(seen);expected_graph['unreachable']=sorted(set(expected_graph['nodes'])-seen)
    check('native nested graph plus pinned foreign-POI contraction '+q+d+gp,gr==expected_graph,dict(private_graph=gp,native_graph=sourcegp,approved_edits=approved_edits),q)
   copied.append(dict(kind=r['kind'],resource=d,native_binary=r['raw'],native_graph=r['graph'],nodes=r['ids']))
  check('native full body exact reference and actual input '+q,n(entry,s['body'])['refs']==[main] and edge(entry,[65004,'Out',s['body'],er['main_input']]) and er['main_input'] in g(main)['entries'],dict(body=s['body'],input=er['main_input'],native=main),q)
  check('actual POI then Started then body '+q,edge(entry,[s['poi'],'Out',65004,'In']) and writes(n(entry,65004),pfx+'_Started',1),dict(poi=s['poi'],receipt=65004),q)
  guard=n(entry,65002)['payload']['condition'];fs,js=fixture(guard);check('actual entry guard positive '+q,ev(guard,fs,js),dict(facts=len(fs),journals=len(js)),q)
  for f in [pfx+'_ParentEntered',pfx+'_Fault','PTFRU9_Support_Fault']:
   check('reject used/fault entry '+q+f,not ev(guard,fs|{f:1},js),f,q)
  for jp in js:
   if jp.startswith('quests/'):
    check('protect completed/failed history '+q+jp,all(not ev(guard,fs,js|{jp:z}) for z in ['Active','Succeeded','Failed']),jp,q)
  check('native finished writer '+q,writes(n(ow,s['finished_node'],s['finished_graph']),'ina_'+q[-2:]+'_finished',1),dict(resource=ow,graph=s['finished_graph'],node=s['finished_node']),q)
  cr=next(r for r in rr if r['kind']=='credit');credit=cr['depot'];cond=n(credit,65000)['payload']['condition'];cf,cj=fixture(cond)
  check('credit claim gates actual receipts '+q,ev(cond,cf,cj) and all(not ev(cond,cf|{f:1},cj) for f in [pfx+'_CreditEntered',pfx+'_CreditDone']) and not ev(cond,cf|{pfx+'_Started':0},cj),dict(depot=credit,guard=65000),q)
  check('native finish wait before exact additive district credit '+q,n(credit,s['credit_wait'])['reads'][0]['factName']=='ina_'+q[-2:]+'_finished' and n(credit,11)['writes']==[{'$type':'questSetVar_NodeType','factName':'bls_sts_counter','setExactValue':0,'value':1}] and all(edge(credit,e) for e in [(65000,'Out',65001,'In'),(65001,'Out',s['credit_wait'],'In'),(s['credit_wait'],'Out',11,'In'),(11,'Out',65002,'In')]),dict(wait=s['credit_wait'],increment=11,receipt=65002,alias=credit),q)
  maps=[]
  for r in rr:
   if r['kind']!='map':continue
   d=r['depot'];mn=[(i,nn) for i,nn in g(d)['nodes'].items() if nn['journal_paths']];check('native Dakota map visit and POI '+q+d,n(d,2)['reads'][0]['factName']=='dakota_visited' and any('points_of_interest/street_stories/'+q in nn['journal_paths'] for i,nn in mn),dict(resource=d,native_graph=r['graph']),q)
   maps.append(dict(resource=d,native_graph=r['graph'],guard=n(d,65000)['payload']['condition'],journal_nodes=[i for i,nn in mn]))
  calls=[];facts=[];journals=[];rewards=[];assets=[];phone=[]
  native_ds=[d for d in deps if '\\'+q+'\\' in d and d.startswith('base\\')]
  for d in native_ds:
   for gp,gr in models[d]['graphs'].items():
    for i,nn in gr['nodes'].items():
     pin=dict(resource=d,graph=gp,node=i,incoming=[e for e in gr['edges'] if e[2]==i],outgoing=[e for e in gr['edges'] if e[0]==i])
     if nn['reads'] or nn['writes']:facts.append(pin|dict(reads=nn['reads'],writes=nn['writes']))
     if nn['journal_paths']:journals.append(pin|dict(paths=nn['journal_paths']))
     if nn['reward']:rewards.append(pin|dict(payload=nn['payload']))
     if nn['node_refs'] or nn['prefabs']:assets.append(pin|dict(node_refs=nn['node_refs'],prefabs=nn['prefabs']))
     for target in nn['refs']:
      if '_holocall_' in target and target.endswith('.scene'):
       for e in pin['incoming']:
        if target in models and e[3] in g(target,'scene')['entries']:calls.append(pin|dict(scene=target,input=e[3],entry_node=g(target,'scene')['entries'][e[3]]))
  check('actual prebrief/debrief caller scene entries '+q,any('_prebrief.scene' in x['scene'] for x in calls) and any('_debriefs.scene' in x['scene'] for x in calls),calls,q)
  for call in calls:
   d=call['scene'];sg=g(d,'scene');seen=reachable(sg['nodes'],sg['edges'],[call['entry_node']])
   for i,nn in sg['nodes'].items():
    for w in nn['writes']:
     req=w.get('factName','')
     if w.get('value')!=1 or not req.startswith('holo_dakota_') or not req.endswith('_activate') or i not in seen:continue
     base_req=req.removesuffix('_activate');ack=base_req+'_done';waits=[j for j,node in sg['nodes'].items() if any(r.get('factName')==ack and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in node['reads']) and path(sg,i,j)];clears=[j for j,node in sg['nodes'].items() if writes(node,ack,0) and any(path(sg,k,j) for k in waits)]
     readers=[j for j,node in g(HC)['nodes'].items() if any(r.get('factName')==req for r in node['reads'])];acks=[j for j,node in g(HS,'scene')['nodes'].items() if writes(node,ack,1) and base_req in g(HS,'scene')['entries'] and path(g(HS,'scene'),g(HS,'scene')['entries'][base_req],j)]
     scene_waits=[j for j,node in sg['nodes'].items() if any(r.get('factName')==ack and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in node['reads'])]
     retry=not waits and req.endswith('_start_activate') and bool(scene_waits) and any(e[0]==i and sg['nodes'][e[2]]['type']=='scnHubNode' for e in sg['edges'])
     check('native call request controller ack and explicit wait context '+q+d+i,bool(readers and acks) and (bool(waits and clears) or retry),dict(caller=call,producer=i,request=req,waits=waits,clears=clears,readers=readers,ack_writers=acks,native_retry=retry,scene_waits=scene_waits,limit='Native retry rejoins scene hub without a new local done wait; shared waiting/scene scheduling is not simulated' if retry else None),q)
     phone.append(dict(scene=d,input=call['input'],producer=i,request=req,waits=waits,clears=clears,readers=readers,ack_writers=acks,entry_to_request=path(sg,call['entry_node'],i),native_retry=retry,scene_waits=scene_waits,status='CONDITIONAL_NATIVE_SHARED_WAIT_CONTEXT' if retry else 'PASS_STRUCTURAL_REQUEST_ACK_PATH'))
  ci=ids.index(q);cat={method:data(method,ci) for method in ['Paths','Facts','TerminalFacts','LegacyTags','LegacyOwnerFacts']};check('effective catalogue native root and terminal fact '+q,any(q in x for x in cat['Paths']) and 'ina_'+q[-2:]+'_finished' in cat['TerminalFacts'],dict(index=ci,catalogue=cat),q)
  nativej={p for row in journals for p in row['paths'] if p.startswith('quests/') and q in p};nativef={x.get('factName') for row in facts for x in row['reads']+row['writes'] if x.get('factName','').startswith(('ina_'+q[-2:]+'_','#ina_'+q[-2:]+'_',q+'_'))};coverage=dict(native_journal_refs_not_catalogued=sorted(nativej-set(cat['Paths'])),native_fact_refs_not_catalogued=sorted(nativef-set(cat['Facts'])),limit='Reference absence from EntrySafe catalogue is a coverage discrepancy, not a confirmed valid save state or a repair justification; journal definitions/reachability/history implications need target evidence.')
  evidence[q]=dict(spec=s,recipes=copied,entry_guard=guard,guard_facts=fs,journal_fixture=js,effective_producer=dict(script=str(script),sha256=sha(script),class_name='NativeGigsU9',line_start=1520,catalogue_index=ci,catalogue=cat,reference_coverage=coverage,limit='Resource65002 has no journal predicates. Current EntrySafe/Request/Poll enforce catalogue journal/fact/legacy preconditions before issuing Permit; execution/races remain LIVE_ONLY.'),maps=maps,credit=dict(depot=credit,guard=cond,native_recipe=cr),calls=calls,phone_protocols=phone,fact_paths=facts,journal_paths=journals,rewards=rewards,asset_bindings=assets,native_root=g(main),root_prefabs={d:models[d]['root_prefabs'] for d in native_ds})
  # Real serialized credit source mutation; compare to independent native donor payload.
  bad=copy.deepcopy(raws[credit]);target=next(x for x in walk(bad) if x.get('$type')=='questFactsDBManagerNodeDefinition' and x.get('id')==11);next(x for x in walk(target) if x.get('$type')=='questSetVar_NodeType')['value']=2;bm=Resource(bad).normalize();det=bm['graphs']['root']['nodes']['11']['payload']!=donors[cr['raw']]['graphs'][cr['graph']]['nodes']['11']['payload'];mutations.append(dict(quest_id=q,fault='actual serialized district credit1to2',detected=det));check('raw district mutation '+q,det,mutations[-1],q)
 # Assertions on case-specific original branch semantics, beyond generic extraction.
 def hasread(d,gp,i,f,v):return any(r.get('factName')==f and r.get('value')==v for r in n(d,i,gp)['reads'])
 s=SPECS['sts_bls_ina_03'];check('Flying Drugs sabotage and hacking native alternatives',hasread(s['gameplay'],'root/11/42',111,'ina_03_antenna_sbotaged',1) and hasread(s['gameplay'],'root/11/42',112,'#ina_03_antenna_hacked',1),dict(graph='root/11/42',nodes=[111,112]),'sts_bls_ina_03')
 s=SPECS['sts_bls_ina_02'];check('Big Pete actual kill spare debrief alternatives',hasread(s['openworld'],'root/73',109,'ina_02_big_pete_dead',0) and edge(s['openworld'],[109,'True',110,'Active'],'root/73') and edge(s['openworld'],[109,'False',111,'Active'],'root/73'),dict(graph='root/73',nodes=[109,110,111]),'sts_bls_ina_02')
 s=SPECS['sts_bls_ina_05'];check('Goodbye Bruce left-alone branch remains',hasread(s['openworld'],'root/2',376,'ina_05_bruce_left_alone',0) and edge(s['openworld'],[376,'True',377,'In'],'root/2') and edge(s['openworld'],[376,'False',378,'In'],'root/2'),dict(graph='root/2',nodes=[376,377,378]),'sts_bls_ina_05')
 # Mutate a genuine original main-body dependency and require binding check to fail.
 d=SPECS['sts_bls_ina_04']['entry'];bad=copy.deepcopy(raws[d]);node=next(x for x in walk(bad) if x.get('$type')=='questPhaseNodeDefinition' and x.get('id')==8);res=Resource(bad);target=res.d(node['phaseResource']) if False else node['phaseResource'];target['DepotPath']['$value']='towercontinued\\missing_radar.questphase';bm=Resource(bad).normalize();det=bm['graphs']['root']['nodes']['8']['refs']!=[SPECS['sts_bls_ina_04']['native']];mutations.append(dict(fault='Radar main body resource missing',detected=det));check('raw missing dependency mutation',det,mutations[-1])
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',dict(quests=evidence,manifest=str(MAN),manifest_sha256=sha(MAN),queue=str(W/'prealpha/quest_restoration_qr3/queue.json'),queue_sha256=sha(W/'prealpha/quest_restoration_qr3/queue.json'),shared_core=str(corepath),shared_core_sha256=sha(corepath),shared_limits=core['limits']));write(O/'tests.json',dict(status='PASS_SCOPED_STATIC_CHECKS',count=len(checks),checks=checks,mutations=mutations,runtime_changes=[],limits='Structural MAY paths do not establish engine call delivery, owner retirement, world placement, current TweakDB values or save/reward transition safety.'))
 return dict(checks=len(checks),sources=len(pins),mutations=len(mutations))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
