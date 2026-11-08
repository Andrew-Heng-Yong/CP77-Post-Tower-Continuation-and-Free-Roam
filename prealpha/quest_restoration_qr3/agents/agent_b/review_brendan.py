"""Independent raw-handle/socket review of Agent C's preclaim quarantine."""
from pathlib import Path
import json,copy,sys,re,collections
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent/'reviews'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,sha,write,walk,value
idx=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
P=r'towercontinued\sidejobs_s23\base_b\mq037.questphase';N=r'base\quest\minor_quests\mq037\mq037_brendan.questphase'
inputs=[];checks=[]
def check(name,ok,e):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':e});assert ok,name
def rawgraphs(d):
 r=idx[d];j=Path(r['json']);b=(W/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))) if d.startswith('towercontinued') else j.with_suffix('')
 assert sha(b)==r['sha256'];obj=read(j);inputs.append({'depot':d,'binary':str(b),'sha256':sha(b),'source_json':str(j),'json_sha256':sha(j)})
 hs={str(x['HandleId']):x['Data'] for x in walk(obj) if 'HandleId' in x and 'Data' in x}
 def deref(x):return x['Data'] if isinstance(x,dict) and 'HandleId' in x and 'Data' in x else hs.get(str(x['HandleRefId'])) if isinstance(x,dict) and 'HandleRefId' in x else x
 def hid(x):return str(x.get('HandleId',x.get('HandleRefId')))
 def clean(x,seen=()):
  if isinstance(x,dict):
   if 'HandleId'in x or 'HandleRefId'in x:
    h=hid(x)
    if h in seen:return {'cycle':h}
    return clean(deref(x),seen+(h,))
   return {k:clean(v,seen) for k,v in x.items() if k not in ['sockets','connections','phaseGraph']}
  if isinstance(x,list):return [clean(v,seen) for v in x]
  return x
 graphs={}
 def parse(h,gp):
  g=deref(h);ns={str(deref(n)['id']):deref(n) for n in g['nodes']};sock={};edges=[];done=set()
  for i,n in ns.items():
   for sh in n.get('sockets',[]):sock[hid(sh)]=(i,str(value(deref(sh)['name'])))
  for i,n in ns.items():
   for sh in n.get('sockets',[]):
    for ch in deref(sh).get('connections',[]):
     k=hid(ch)
     if k in done:continue
     co=deref(ch);a=sock.get(hid(co['source']));b=sock.get(hid(co['destination']));assert a and b;edges.append([*a,*b]);done.add(k)
  graphs[gp]={'nodes':{i:clean(n) for i,n in ns.items()},'edges':sorted(edges)}
  for i,n in ns.items():
   ph=deref(n.get('phaseGraph'))
   if isinstance(ph,dict) and 'nodes'in ph:parse(n['phaseGraph'],gp+'/'+i)
 parse(obj['Data']['RootChunk']['graph'],'root');return graphs
p=rawgraphs(P);n=rawgraphs(N)
g=p['root'];gn=n['root']
def reach(gr,start):
 seen={str(start)};todo=list(seen)
 while todo:
  a=todo.pop()
  for x,s,y,t in gr['edges']:
   if x==a and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);todo.append(y)
 return seen
def route(gr,a,b):
 q=collections.deque([(str(a),[])]);seen=set()
 while q:
  x,path=q.popleft()
  if x==str(b):return path
  if x in seen:continue
  seen.add(x)
  q.extend((y,path+[[x,s,y,t]]) for x0,s,y,t in gr['edges'] if x0==x and s!='CutSource' and t!='CutDestination')
 return None
for e in [['1004','True','1005','In'],['1005','Out','1006','In'],['1006','Out','34','In1']]:check('raw current preclaim route '+str(e),e in g['edges'],e)
check('current body node invokes native full In1',g['nodes']['34']['phaseResource']['DepotPath']['$value']==N and route(g,1000,34) is not None,route(g,1000,34))
dump='quests/minor_quest/mq037_brendan_dumpster'
for i in ['1002','1004']:
 js=[x for x in walk(g['nodes'][i]) if x.get('$type')=='questJournalEntryState_ConditionType']
 check('current guard '+i+' requires Dumpster Inactive',any(x['path']['realPath']==dump and x['state']=='Inactive' and not x['inverted'] for x in js),js)
 check('current guard '+i+' lacks earned Dumpster success',not any(x['path']['realPath']==dump and x['state']=='Succeeded' for x in js),{'node':i})
check('native full entry sequencing reaches dumpster phase',all(e in gn['edges'] for e in [['0','Out','34','In1'],['34','Out1','10','In1'],['10','Out1','19','In1']]),{'native':'root0->34->10->19'})
check('native excluded root activation is connected',route(n['root/19'],0,16) is not None and ['22','Out','16','Active'] in n['root/19']['edges'] and n['root/19']['nodes']['16']['type']['path']['realPath']==dump,{'native_graph':'root/19','route':route(n['root/19'],0,16)})
check('physical dumpster completion downstream, not preactivation', ['16','Out','12','Active'] in n['root/19']['edges'] and ['12','Out','7','In'] in n['root/19']['edges'] and n['root/19']['nodes']['7']['condition']['type']['deviceConditionFunction']['$value']=='DemolitionPerformed',{'native_graph':'root/19','nodes':[16,12,7]})
pol=W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json';policy=read(pol);entries=[x for x in walk(policy) if x.get('id') in ['mq037_brendan_dumpster','mq037_brendan','mq037_brendan_hooligan001'] and 'decision'in x]
check('actual current policy excludes fresh Dumpster',any(x['id']=='mq037_brendan_dumpster' and x['decision']=='EXCLUDE' for x in entries),entries)
check('selected sequels require earned predecessor',all(any(x['id']==id and x['decision']=='INCLUDE' and 'genuine' in x.get('requirements','').lower() for x in entries) for id in ['mq037_brendan','mq037_brendan_hooligan001']),entries)
S=W/'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds';H=S.with_name('PTFR_HistorySnapshotHS1.reds');s=S.read_text(encoding='utf-8-sig');h=H.read_text(encoding='utf-8-sig')
check('real S23 producer row13 targets selected family', 'if i == 13 { return "mq037_brendan"; }' in s and 'Paths13()' in s and dump in s and 'this.Permit(i, this.Same(this.previous[i], current) && this.Ready(i));' in s,{'script':str(S),'sha256':sha(S)})
check('real S23 fresh18-state bounds allow Inactive',all(re.search(r'func States'+a+r'13\(\).*?return \[1(?:, 1){17}\]',s) for a in ['A','B']),{'scope':'StatesA13 and B13 all18Inactive'})
check('HS1 accepted inactive snapshot not earned-predecessor proof','return this.rows[i].states[0]==1 || this.rows[i].states[0]==2;' in h and 's.Allows(id)' in h,{'script':str(H),'sha256':sha(H),'scope':'HS1.Admis->Allows; present stable Inactive root can pass without completed Dumpster'})
check('existing quarantine target only owned Refused fact',g['nodes']['1008']['type']=={'$type':'questSetVar_NodeType','factName':'PTFRS23_MQ037_Refused','setExactValue':1,'value':1},g['nodes']['1008'])
check('Refused target is currently unused/no outgoing',not any(e[0]=='1008' or e[2]=='1008' for e in g['edges']),{'node':1008})
after=copy.deepcopy(g);after['edges'].remove(['1004','True','1005','In']);after['edges'].append(['1004','True','1008','In'])
check('proposed one edge denies new owner but keeps reachable refusal','34' not in reach(after,1000) and '1005' not in reach(after,1000) and '1008' in reach(after,1000),{'before_reachable':sorted(reach(g,1000)),'after_reachable':sorted(reach(after,1000))})
check('proposed patch retains every saved node payload',after['nodes']==g['nodes'],{'node_count':len(g['nodes'])})
check('already queued Issued/Entered/native descendants stay connected',route(after,1005,34)==route(g,1005,34) and route(after,1006,34)==route(g,1006,34),{'1005_to_body':route(after,1005,34),'scope':'Preserves authored descendants; actual serialized pending-event behavior is live-only'})
check('no native journal/fact/reward reset introduced',after['nodes']['1008']['type']['factName'].startswith('PTFRS23_') and after['nodes']==g['nodes'],{'writes_added':[],'new_identifiers':[]})
check('mutation removal of quarantine admits body again','34' in reach(g,1000) and '34' not in reach(after,1000),{'oracle':'Independent raw graph reachability, with unchanged serialized guard predicates'})
O.mkdir(parents=True,exist_ok=True)
out=O/'brendan_quarantine.json';assert not out.exists()
write(out,{'status':'APPROVE_MINIMAL_PRECLAIM_QUARANTINE_WITH_CONTINUATION_BLOCKER','reviewer':'agent_b independent raw socket parser; AgentC verifier not imported/executed','defect_id':'QR3-MQ037-EXCLUDED-PREREQUISITE','checks':checks,'inputs':inputs+[{'path':str(pol),'sha256':sha(pol)},{'path':str(S),'sha256':sha(S)},{'path':str(H),'sha256':sha(H)}],'approved_change':{'resource':P,'remove':['1004','True','1005','In'],'add':['1004','True','1008','In'],'node_changes':[]},'runtime_changes_performed':[],'limitations':['No gameplay observation or save-runtime transition assertion. Source proves excluded fresh route remains admissible; native world/dialogue predicates were traced as authored potential route, not measured play.','This is a conservative quarantine, not restoration of the selected sequels. Earned-history stage/owner adapter remains explicitly blocked.','Already executing descendants are not cancelled. Previously queued input dispatch and save/restore edge resolution remain engine-dependent.']})
print(json.dumps({'status':'APPROVE_MINIMAL_PRECLAIM_QUARANTINE_WITH_CONTINUATION_BLOCKER','checks':len(checks)}))
