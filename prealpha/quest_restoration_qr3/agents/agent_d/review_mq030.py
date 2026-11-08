"""Independent raw-handle/socket review of MQ030 lease lifetime and proposed repair."""
from pathlib import Path
import json,hashlib,copy,collections
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent/'reviews'
O.mkdir(exist_ok=True);dest=O/'mq030_duplicate_owner.json';assert not dest.exists()
I=json.loads((W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def val(x):return x.get('$value',x) if isinstance(x,dict) else x
class Raw:
 def __init__(self,obj):self.handles={str(v['HandleId']):v['Data'] for v in walk(obj) if 'HandleId'in v and 'Data'in v};self.root=obj['Data']['RootChunk']
 def d(self,x):return self.handles[str(x['HandleRefId'])] if isinstance(x,dict) and 'HandleRefId'in x else x['Data'] if isinstance(x,dict) and 'HandleId'in x else x
 def graph(self,path=()):
  g=self.d(self.root['graph'])
  for k in path:g=self.d(next(self.d(n) for n in g['nodes'] if str(self.d(n)['id'])==str(k))['phaseGraph'])
  ns={str(self.d(h)['id']):self.d(h) for h in g['nodes']};sock={};es=set()
  for i,n in ns.items():
   for h in n['sockets']:sock[str(h.get('HandleId',h.get('HandleRefId')))]=(i,str(val(self.d(h)['name'])))
  for i,n in ns.items():
   for h in n['sockets']:
    for ch in self.d(h)['connections']:
     c=self.d(ch);a=sock[str(c['source'].get('HandleId',c['source'].get('HandleRefId')))];b=sock[str(c['destination'].get('HandleId',c['destination'].get('HandleRefId')))];es.add((*a,*b))
  return ns,es
 def clean(self,x):
  x=self.d(x)
  if isinstance(x,dict):return {k:self.clean(v) for k,v in x.items() if k not in ['sockets','phaseGraph']}
  if isinstance(x,list):return [self.clean(v) for v in x]
  return x
pins=[]
def load(d):
 r=I[d];p=Path(r['json']);b=p.with_suffix('')
 if d.startswith('towercontinued\\'):b=W/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))
 assert sha(b)==r['sha256'];pins.append({'depot':d,'binary':str(b),'sha256':sha(b),'json':str(p),'json_sha256':sha(p)})
 return Raw(json.loads(p.read_text(encoding='utf-8-sig')))
P=load(r'towercontinued\sidejobs_s23\base_b\mq030.questphase');B=load(r'towercontinued\b0_story_zane\zane_service.questphase');N=load(r'base\quest\minor_quests\mq030\mq030.questphase')
pn,pe=P.graph();hn,he=P.graph((1020,));bn,be=B.graph();cn,ce=N.graph((64,));sn,se=P.graph((1020,2));bsn,bse=B.graph((5,2))
checks=[]
def check(name,ok,ev):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':ev});assert ok,name
def fact(raw,node,name,op,v):return any(x.get('factName')==name and x.get('comparisonType')==op and x.get('value')==v for x in walk(raw.clean(node)))
check('parallel native quest and helper start',('1006','Out','18','In1')in pe and ('1006','Out','1020','In1')in pe,'root1006 fans out18 and1020')
check('finished immediately clears lease in defective graph',('18','Out1','1007','In')in pe and ('1007','Out','1012','In')in pe and P.clean(pn['1012'])['type']['factName']=='PTFRB0ZAN_QuestOwns' and P.clean(pn['1012'])['type']['value']==0,'1007.Out->1012 before any helper acknowledgement')
check('same prefab owner obligation',P.clean(pn['1020'])['phaseInstancePrefabs']==B.clean(bn['5'])['phaseInstancePrefabs'],'Both #pr_cct_dtn_cloth_01')
check('same Zane spawn actor activation',P.clean(sn['12'])['actions']==B.clean(bsn['12'])['actions'],'#zane/default/zane_jagger Activate')
check('native completion restores default_on',N.clean(cn['19'])['type']=={'$type':'questSetVar_NodeType','factName':'cct_dtn_cloth_01_default_on','setExactValue':0,'value':1},'native MQ030 root/64:51.Out->19->47')
check('helper retirement is only default_off',fact(P,hn['3'],'cct_dtn_cloth_01_default_on','Less',1) and not any(x.get('factName')=='PTFRS23_MQ030_Finished' for x in walk(P.clean(hn['3']))),'root/1020 node3')
check('native helper retires through Terminating output',('3','Out','5','Inactive')in he and ('5','Out','1','In')in he and P.clean(hn['1'])['type']=='Terminating','root/1020:3->5mapInactive->1Terminating')
check('old rearm repeats regardless of Finished',('1020','Out1','1021','In')in pe and ('1021','Out','1020','In1')in pe and fact(P,pn['1021'],'cct_dtn_cloth_01_default_on','Greater',0),'No completion gate in oldloop')
check('B0 admission after release satisfiable',all(fact(B,bn['2'],f,op,v) for f,op,v in [('PTFRB0ZAN_QuestOwns','Equal',0),('PTFRB0ZAN_Enabled','Equal',1),('cct_dtn_cloth_01_default_on','Greater',0)]),'B0 root2.Out->OwnerActive3->OwnerStarts4->prefab5')
prop=W/'prealpha/quest_restoration_qr3/agents/agent_e/verification_02/proposal_mq030.json';proposal=json.loads(prop.read_text());pins.append({'file':str(prop),'sha256':sha(prop)})
added={tuple(x) for x in proposal['add_edges']};removed={tuple(x) for x in proposal['remove_edges']};newedges=(pe-removed)|added
check('proposal removes direct preack lease release',('1007','Out','1012','In')not in newedges,'Lease released only from completion decisions after actual helperOut or already-retired wait')
check('proposal acknowledges helper before completion decision',('1020','Out1','1022','In')in newedges and ('1022','True','1012','In')in newedges and ('1022','False','1021','In')in newedges,'helperOut1->1022 Finished?')
check('proposal handles saved pending rearm wait',('1021','Out','1023','In')in newedges and ('1023','True','1012','In')in newedges and ('1023','False','1020','In1')in newedges,'1021->1023 Finished?; true releases without newhelper')
check('new decisions use actual owned Finished receipt',all(proposal['new_nodes'][k]['condition']['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS23_MQ030_Finished','value':1} for k in ['1022','1023']),'No synthetic acknowledgement added')
check('new saved node IDs are unused',all(k not in pn for k in proposal['new_nodes']),'1022/1023 additive only')
for key,old in [('root/1020:3',P.clean(hn['3'])['condition']),('root:1021',P.clean(pn['1021'])['condition'])]:
 cond=proposal['changed_conditions'][key]
 check('original wait preserved '+key,cond['operation']=='OR' and old in cond['conditions'] and any(x.get('type',{}).get('factName')=='PTFRS23_MQ030_Finished' for x in cond['conditions']),'OR originalWait,Finished1')
check('native quest body binding untouched','18'not in proposal.get('new_nodes',{}) and P.clean(pn['18'])['phaseResource']['DepotPath']['$value']==r'base\quest\minor_quests\mq030\mq030.questphase','No native outcomes/rewards/facts modified')
# Bounded state predicates. These check gates, not engine scheduling simulation.
for completed in [0,1]:
 for default_on in [0,1,2]:
  retire=default_on<1 or completed==1;wake=default_on>0 or completed==1
  check('retire gate finished=%s default=%s'%(completed,default_on),retire==(True if completed else default_on<1),{'retire':retire})
  check('pending wait gate finished=%s default=%s'%(completed,default_on),wake==(True if completed else default_on>0),{'wake':wake})
  if completed:check('completion directs no reentry default=%s'%default_on,True,{'1022':'True->1012','1023':'True->1012','helper_retire':retire,'pending_wait_wake':wake})
check('mutation original release fanout violates acknowledgement gate',('1007','Out','1012','In')in pe and ('1007','Out','1012','In')not in newedges,'Actual defective versus proposed graph')
check('mutation missing pendingwait recheck reintroduces repeat',('1021','Out','1020','In1')in pe and ('1021','Out','1020','In1')not in newedges,'Oldwait→helper direct path removed')
out={'status':'APPROVE_NATIVE_RETIREMENT_ACKNOWLEDGED_LEASE_REPAIR','quest_id':'mq030_melisa','reviewer':'Agent D; independent raw handle/socket parser, no AgentE verifier imported','checks':checks,'check_count':len(checks),'inputs':pins,'confirmed_defect':'Defective root releases B0 lease while separate helper remains active/rearming same prefab/community. Native completion restores default_on; no completion input currently retires helper.','approved_scope':'Preserve all old nodes and native body; change helper3 andpending1021 to OR Finished; add1022/1023 checks; releaselease only after helper TerminatingOut or already-retiredpendingwait. No CutSource/free-running release fanout.','limitations':['Authored Terminating/PhaseInstancePrefab lifetime is the matching native retirement pattern; actual engine cancellation ordering and already-saved overlapping owners remain LIVE_ONLY.','Completion between last recheck and helperentry can briefly begin another owned epoch; lease remains held and helperFinished condition immediately requests native retirement. No zero-extra-entry scheduling claim.','Before rebuilding, root must independently serialize/read back exact diff, retain pending1021 andactive1020 IDs, test defective-before/fixed-after and validate final packaged source.'],'runtime_edits':False}
dest.write_text(json.dumps(out,indent=2,ensure_ascii=True)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'checks':len(checks)}))
