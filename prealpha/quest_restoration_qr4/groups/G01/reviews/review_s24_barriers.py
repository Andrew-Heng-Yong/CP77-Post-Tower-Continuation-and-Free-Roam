"""Independent rejection of the proposed S24 fresh ownership race.

Uses fresh QR3 binary exports and a separate raw handle/socket parser. It does
not import the investigator's verifier or modify resources.
"""
from pathlib import Path
import sys,copy,json
W=Path(__file__).resolve().parents[5];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
IDX=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
checks=[];pins=[];proof=[]
def check(name,ok,evidence):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
def parse(obj):
 hs={}
 def walk(x):
  if isinstance(x,dict):
   if 'HandleId'in x and 'Data'in x:hs[str(x['HandleId'])]=x['Data']
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(obj)
 def d(x):return hs[str(x['HandleRefId'])] if isinstance(x,dict) and 'HandleRefId'in x else x.get('Data',x) if isinstance(x,dict) else x
 root=d(obj['Data']['RootChunk']['graph']);nodes={str(d(h)['id']):d(h) for h in root['nodes']};sockets={};edges=set()
 def v(x):return x.get('$value',x) if isinstance(x,dict) else x
 for i,n in nodes.items():
  for h in n['sockets']:
   s=d(h);key=str(h.get('HandleId',h.get('HandleRefId')));sockets[key]=(i,str(v(s['name'])))
 for i,n in nodes.items():
  for h in n['sockets']:
   for c in d(h).get('connections',[]):
    q=d(c);a=q['source'];b=q['destination'];ak=str(a.get('HandleId',a.get('HandleRefId')));bk=str(b.get('HandleId',b.get('HandleRefId')));edges.add((*sockets[ak],*sockets[bk]))
 return nodes,edges,d
def reach(edges,start,blocked=set()):
 seen={start};todo=[start]
 while todo:
  for a,s,b,t in edges:
   if a==todo[-1] and b not in seen and b not in blocked and s!='CutSource' and t!='CutDestination':seen.add(b);todo.insert(0,b)
  todo.pop()
 return seen
for quest,contact,controller in [('mq015','r3no','103'),('mq019','lizzy','66')]:
 fresh=O/'s24_barrier_current'/(quest+'.json');dep='towercontinued\\sidejobs_s24\\base\\'+quest+'.questphase';raw=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'/dep.replace('\\','/')
 check('current staged binary matches source index '+quest,sha(raw)==IDX[dep]['sha256'],str(raw))
 nodes,edges,d=parse(read(fresh));barrier=nodes['1003'];condition=d(barrier['condition']);fact='PTFRS24_PHONE_'+contact.upper()+'_Issued'
 def leaf_conditions(h,resolver=d):
  c=resolver(h)
  if c['$type']=='questLogicalCondition':
   return [z for x in c['conditions'] for z in leaf_conditions(x,resolver)]
  return [resolver(c['type'])] if c['$type']=='questFactsDBCondition' else [c]
 def required_facts(h,resolver=d):
  c=resolver(h)
  if c['$type']=='questLogicalCondition':
   sets=[required_facts(x,resolver) for x in c['conditions']]
   if c['operation']=='AND':return set().union(*sets)
   if c['operation']=='OR':return set.intersection(*sets) if sets else set()
   return set()
  if c['$type']=='questFactsDBCondition':
   v=resolver(c['type']);return {(v['factName'],v['comparisonType'],v['value'])} if v['$type']=='questVarComparison_ConditionType' else set()
  return set()
 cmp=next(x for x in leaf_conditions(condition) if x.get('factName')==fact)
 check('actual intermediate is pause '+quest,barrier['$type']=='questPauseConditionNodeDefinition','1003')
 check('pause requires exact durable phoneIssued1 '+quest,(fact,'Equal',1) in required_facts(condition),cmp)
 check('actual connected fresh path includes wait '+quest,('1002','Out','1003','In') in edges and ('1003','Out','54','In') in edges and ('1004','True','1005','In') in edges,sorted(edges))
 check('phone barrier dominates every fresh quest claim '+quest,'1005' in reach(edges,'1000') and '1005' not in reach(edges,'1000',{'1003'}),'Actual raw root connections; all potential branches included, not just a title/fact scan')
 check('phone0 cannot pass intermediate wait '+quest,not(0==cmp['value']),'Proposed quest-first state is not executable from the actual fresh input')
 check('phone1 can pass intermediate wait '+quest,1==cmp['value'],'No new prerequisite or listener is necessary')
 writer=d(nodes['1005']['type']);check('questIssued written only downstream '+quest,writer['factName']=='PTFRS24_'+quest.upper()+'_Issued' and writer['value']==1,writer)
 pd='towercontinued\\sidejobs_s24\\phone\\'+contact+'.questphase';j=Path(IDX[pd]['json']);pr=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'/pd.replace('\\','/')
 check('phone wrapper pinned '+quest,sha(pr)==IDX[pd]['sha256'],str(pr));pn,pe,pderef=parse(read(j));conds=[]
 for i in ['1002','1003']:
  c=pderef(pn[i]['condition']);facts=leaf_conditions(c,pderef);conds.append(facts)
  check('phone preclaim requires parent notIssued '+quest+' '+i,('PTFRS24_'+quest.upper()+'_Issued','Equal',0) in required_facts(c,pderef),facts)
 check('phone claim enters native controller without parent recheck '+quest,('1003','True','1004','In') in pe and ('1004','Out',controller,'In1') in pe,'Durable phone receipt precedes queued native controller activation')
 mut=set(edges);mut.remove(('1002','Out','1003','In'));mut.add(('1002','Out','54','In'))
 check('missing barrier mutation detected '+quest,'1005' in reach(mut,'1000',{'1003'}),'Original alleged ordering becomes possible only after deliberate removal of the existing pause')
 pins += [{'depot':dep,'binary':str(raw),'sha256':sha(raw),'fresh_export':str(fresh),'json_sha256':sha(fresh)},{'depot':'towercontinued\\sidejobs_s24\\phone\\'+contact+'.questphase','binary':str(pr),'sha256':sha(pr),'source_json':str(j),'json_sha256':sha(j)}]
 proof.append({'quest':quest,'barrier_node':'1003','required_receipt':fact+'==1','claim_node':'1005','conclusion':'Proposed fresh race contradicted by actual connected intermediate pause'})
write(O/'s24_phone_barrier_review.json',{'status':'REJECT_PROPOSED_REPAIR_EXISTING_BARRIER_CONFIRMED','checks':checks,'count':len(checks),'source_pins':pins,'findings':proof,'runtime_defect_confirmed':False,'repair_approved':False,'reason':'Initial investigation inspected quest preclaim1002/1004 but skipped actual pause1003. Appending redundant phone guards is not a source-confirmed fix.','remaining':['Already-issued orphan/adoption state is a separate unsupported save/controller question; no saved execution was inspected.','Native controller scheduling, queued request processing, playback and interruption remain engine boundaries.'],'game_writes':0,'save_writes':0,'runtime_changes':[]})
print({'status':'REJECT_UNJUSTIFIED_REPAIR','checks':len(checks),'actual_current_binary_exports':2,'mutations':2})
