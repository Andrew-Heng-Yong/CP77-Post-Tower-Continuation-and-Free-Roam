"""S22 bounded Delamain exported-resource checks; not runtime proof."""
import json,sys,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read,sha,walk,value

def graphs(p):
 r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return {tuple(e) for e in g['edges']}
def evaluate(c,f,j):
 if c['$type']=='questLogicalCondition':
  vs=[evaluate(x,f,j) for x in c['conditions']];return all(vs) if c['operation']=='AND' else any(vs)
 t=c['type']
 if c['$type']=='questJournalCondition':return j.get(t['path']['realPath'])==t['state']
 assert c['$type']=='questFactsDBCondition'
 if t['$type']=='questVarVsVarComparison_ConditionType':return f.get(t['factName1'],0)==f.get(t['factName2'],0)
 a=f.get(t['factName'],0);b=t['value'];return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[t['comparisonType']]

def verify(build):
 m=read(build/'build.json');a=read(HERE/'admission.json');assert m['admission']==a
 assert len(m['resources'])==4 and len(m['boots'])==2
 for p,h in m['source_pins'].items():assert sha(ROOT/p)==h,p
 for p,h in m['resources'].items():assert sha(build/'source'/p)==h,p
 out={name:graphs(build/'readback'/f'{name}.json') for name in ('scan','owner','support','fixer_cleanup')}
 scan=graphs(ROOT/(m['scan_source'].replace('/raw/','/json/')+'.json'))
 parent=graphs(ROOT/(m['parent_source'].replace('/raw/','/json/')+'.json'))
 copied=0
 # Every stock scan node payload is unchanged, including nested rewards,
 # community/scene ownership, retry/marker graphs and cleanup.
 assert set(scan)==set(out['scan'])
 for path,g in scan.items():
  actual=out['scan'][path];on=nodes(g);an=nodes(actual)
  assert all(an[i]==n for i,n in on.items()),('scan payload',path)
  copied+=len(on)
  if path not in ('root','root/267'):assert actual==g,('nested graph',path)
 sn=nodes(out['scan']['root']);se=edges(out['scan']['root']);expected=edges(scan['root'])
 for leg in m['legs']:
  i=1000+leg['slot'];d=leg['delay'];slot=leg['slot']
  expected.remove((195,'Out'+str(slot),d,'In'))
  expected|={(195,'Out'+str(slot),i,'In'),(i,'True',198,'In'+str(slot)),(i,'False',d,'In')}
  c=sn[i]['condition'];p='quests/side_quest/'+leg['root'];f='sq025_'+leg['name']+'_done'
  for done,state in itertools.product((0,1,2),('Inactive','Active','Succeeded','Failed',None)):
   assert evaluate(c,{f:done},{p:state})==(done==1 and state=='Succeeded')
 assert se==expected
 # Follow completed cleanup input through guards and prove no Succeeded write.
 hg=out['scan']['root/267'];hn=nodes(hg);he=edges(hg)
 for jid in range(2,9):
  assert hn[jid]==nodes(scan['root/267'])[jid]
  assert (100+jid,'False',jid,'Inactive') in he
  assert not any(e[2]==jid and e[0] != 100+jid for e in he)
 current=10;seen=set();success={nodes(scan['root/267'])[i]['type']['path']['realPath']:'Succeeded' for i in range(2,9)}
 while current!=1:
  assert current not in seen;seen.add(current);n=hn[current]
  assert n['$type']!='questJournalNodeDefinition'
  port='True' if n['$type']=='questConditionNodeDefinition' and evaluate(n['condition'],{},success) else 'Out'
  es=[e for e in he if e[0]==current and e[1]==port];assert len(es)==1,(current,es);current=es[0][2]
 # Parent gameplay/final return and failure payloads stay stock. No excluded
 # sequel resource, hook/reception/briefing scene, or global SQ025 done write.
 pn=nodes(out['owner']['root']);native=nodes(parent['root'])
 for i in m['parent_selected']:
  if i==79:
   n=dict(pn[i]);n['phaseResource']=native[i]['phaseResource'];assert n==native[i]
  else:assert pn[i]==native[i],('parent node',i)
  copied+=1
 for path,g in parent.items():
  if path=='root' or int(path.split('/')[1]) not in m['parent_selected']:continue
  if path=='root/147':continue
  assert out['owner'][path]==g,('native owner',path);copied+=len(g['nodes'])
 traffic=out['owner']['root/147'];orig=parent['root/147'];tids={0,1,3,4,10,11,12,14,15,16,17,18,19,65}
 assert nodes(traffic)=={i:n for i,n in nodes(orig).items() if i in tids}
 assert edges(traffic)=={e for e in edges(orig) if e[0] in tids and e[2] in tids}|{(0,'Out',65,'In')}
 assert not any('resurgence.questphase' in json.dumps(n) or 'sq025_05a_messages' in json.dumps(n) for n in pn.values())
 assert all(x.get('factName') not in ('sq025_scans_done','sq025_done') for n in pn.values() for x in walk(n) if x.get('$type')=='questSetVar_NodeType')
 pe=edges(out['owner']['root'])
 assert {(1003,'True',1004,'In'),(1004,'Out',1005,'Active'),(1005,'Out',1013,'Active'),(1013,'Out',1014,'Active'),(1014,'Out',1006,'In'),(1006,'Out',1007,'In')} <= pe
 assert (124,'Out1',1008,'In') in pe and not any(e[2]==134 for e in pe)
 # Admission independently proves the exact supported progress; current user
 # Inactive OR Failed policy does not bypass preserved completed siblings.
 names={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
 good=m['common_equal']|a['facts_equal']|m['phone_idle_equal']|{'PTFRS22_SQ025_Permit':1,'PTFRS22_SQ025_Issued':0,'PTFRS22_SQ025_Fault':0,'PTFRS22_SQ025_SupportIssued':1}
 for pair in m['phone_balances']:
  for k in pair:good[k]=0
 j={v['path']:names[v['states'][0]] for v in a['journals']}
 condition=pn[1002]['condition'];assert condition==pn[1003]['condition'];assert evaluate(condition,good,j)
 negatives=0;positive=1
 for k,v in good.items():
  for wrong in (-1,0,1,2,7):
   if wrong==v:continue
   assert not evaluate(condition,good|{k:wrong},j),(k,wrong);negatives+=1
 for spec in a['journals']:
  for state in (None,'Inactive','Active','Succeeded','Failed','Unknown'):
   accepted=state in [names[v] for v in spec['states']]
   assert evaluate(condition,good,j|{spec['path']:state})==accepted,(spec['path'],state)
   if accepted:positive+=1
   else:negatives+=1
 # All128 completion masks seed only selected AND inputs, never spawn their
 # completed owners; exact live mask has3seeds+4remaining native routes.
 for mask in range(128):
  seeds=[];pending=[]
  for leg in m['legs']:
   done=(mask>>(leg['slot']-1))&1;p='quests/side_quest/'+leg['root'];f='sq025_'+leg['name']+'_done'
   (seeds if evaluate(sn[1000+leg['slot']]['condition'],{f:done},{p:'Succeeded' if done else 'Inactive'}) else pending).append(leg['slot'])
  assert len(seeds)+len(pending)==7 and not(set(seeds)&set(pending))
 init=graphs(ROOT/(m['phone_init_source'].replace('/raw/','/json/')+'.json'))
 assert nodes(out['support']['root'])[51]==nodes(init['root'])[51];copied+=1
 support=nodes(out['support']['root']);sc=support[1002]['condition']
 assert sc==support[1003]['condition']
 assert not evaluate(sc,good,j)
 assert evaluate(sc,good|{'PTFRS22_SQ025_SupportIssued':0},j)
 assert not evaluate(sc,good|{'PTFRS22_SQ025_SupportIssued':0,'PTFRS22_SQ025_Issued':1},j)
 # Save during root preparation cannot take the admission path again, and
 # the persisted graph does not proceed until all protected states survive.
 assert not evaluate(condition,good|{'PTFRS22_SQ025_Issued':1},j)
 post=pn[1006]['condition'];postj=j|{a['root']:'Active',a['root']+'/03_scan':'Active',a['root']+'/03_scan/03_02_scan_delamains':'Active'}
 assert evaluate(post,good|{'PTFRS22_SQ025_Issued':1},postj)
 protected=[s for s in a['journals'] if s['states']==[3]]
 for spec in protected:
  for state in ('Inactive','Active','Failed',None):
   assert not evaluate(post,good|{'PTFRS22_SQ025_Issued':1},postj|{spec['path']:state})
 assert len(m['phone_balances'])==16 and len(m['phone_idle_equal'])==57
 cg=out['fixer_cleanup']['root'];old=graphs(ROOT/'prealpha/courier_c1/build/c1_02/readback/fixer_cleanup.json')['root']
 assert all(nodes(cg)[i]==n for i,n in nodes(old).items());copied+=len(nodes(old))
 for path,g in graphs(ROOT/'prealpha/courier_c1/build/c1_02/readback/fixer_cleanup.json').items():
  if path!='root':assert out['fixer_cleanup'][path]==g;copied+=len(g['nodes'])
 expected={((e[0],e[1],700,'In') if e[0] in (600,601) and e[2]==6 else e) for e in edges(old)}|{(700,'True',701,'In12'),(700,'False',6,'In2'),(701,'Out12',6,'In2')}
 assert edges(cg)==expected
 csource=graphs(ROOT/(m['cleanup_source'].replace('/raw/','/json/')+'.json'))['root']
 for src,dst in ((438,700),(302,701)):
  n=dict(nodes(cg)[dst]);n['id']=src;assert n==nodes(csource)[src];copied+=1
 refs=sorted({str(value(x['DepotPath'])) for obj in out.values() for g in obj.values() for n in g['nodes'] for x in walk(n) if 'DepotPath' in x and str(value(x['DepotPath'])).endswith(('.scene','.questphase'))})
 return {'status':'PASS_EXPORTED_NOT_LIVE','build_sha256':sha(build/'build.json'),'tester_sha256':sha(Path(__file__)),'copied_native_nodes':copied,'negative_admissions':negatives,'positive_admissions':positive,'completion_masks':128,'protected_succeeded_states':len(protected),'native_fact_admission_count':len(a['facts_equal']),'resources':4,'boot_resources':2,'native_dependencies':refs,'not_proven':['Runtime journal root activation preserves Succeeded children','Native counters/journal numeric 3 of 7 and completed legs','Remaining four gameplay/calls/markers/final scanner reward','Save/reload during owned preparation','Official source comparison, mod collision and packed integration handled by parent']}

if __name__=='__main__':
 b=Path(sys.argv[1]);dest=b/'tests.json';assert not dest.exists();r=verify(b);dest.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
