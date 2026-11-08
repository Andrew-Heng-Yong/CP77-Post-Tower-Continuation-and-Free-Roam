"""Independent raw-graph review of Agent E. Never executes Agent E verifiers."""
from pathlib import Path
import json,copy,sys,collections,re
W=Path(__file__).resolve().parents[4];O=Path(__file__).resolve().parent/'reviews'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value,depots
I=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json')
C=W/'prealpha/quest_restoration_qr3/candidate_01';PH3=W/'prealpha/phone_studios_ph3/candidate_01';checks=[];inputs=[];models={};objects={}
def check(name,ok,e):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':e});assert ok,name
def parse(obj):
 hs={str(x['HandleId']):x['Data'] for x in walk(obj) if 'HandleId'in x and 'Data'in x}
 def dh(x):return x['Data'] if isinstance(x,dict) and 'HandleId'in x and 'Data'in x else hs.get(str(x['HandleRefId'])) if isinstance(x,dict) and 'HandleRefId'in x else x
 def hk(x):return str(x.get('HandleId',x.get('HandleRefId')))
 def clean(x,seen=()):
  if isinstance(x,dict):
   if 'HandleId'in x or 'HandleRefId'in x:
    h=hk(x)
    if h in seen:return {'cycle':h}
    return clean(dh(x),seen+(h,))
   return {k:clean(v,seen) for k,v in x.items() if k not in ['sockets','connections','phaseGraph']}
  if isinstance(x,list):return [clean(v,seen) for v in x]
  return x
 out={}
 def gr(h,gp):
  g=dh(h);ns={str(dh(n)['id']):dh(n) for n in g['nodes']};socks={};edges=[];done=set()
  for i,n in ns.items():
   for sh in n.get('sockets',[]):socks[hk(sh)]=(i,str(value(dh(sh)['name'])))
  for i,n in ns.items():
   for sh in n.get('sockets',[]):
    for ch in dh(sh).get('connections',[]):
     h=hk(ch)
     if h in done:continue
     con=dh(ch);a=socks.get(hk(con['source']));b=socks.get(hk(con['destination']));assert a and b;edges.append([*a,*b]);done.add(h)
  out[gp]={'nodes':{i:clean(n) for i,n in ns.items()},'edges':sorted(edges)}
  for i,n in ns.items():
   if isinstance(dh(n.get('phaseGraph')),dict) and 'nodes'in dh(n['phaseGraph']):gr(n['phaseGraph'],gp+'/'+i)
 if 'graph'in obj['Data']['RootChunk']:gr(obj['Data']['RootChunk']['graph'],'root')
 return out
def load(d):
 if d in models:return models[d]
 r=I[d];j=Path(r['json']);b=PH3/'archive_source'/Path(d.replace('\\','/')) if d.startswith('towercontinued') else j.with_suffix('')
 check('binary source pin '+d,b.is_file() and sha(b)==r['sha256'],{'binary':str(b),'sha256':r['sha256']})
 inputs.append({'depot':d,'binary':str(b),'sha256':sha(b),'json':str(j),'json_sha256':sha(j)})
 objects[d]=read(j);models[d]=parse(objects[d]);return models[d]
def edge(m,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in m[gp]['edges']
def nd(m,i,gp='root'):return m[gp]['nodes'][str(i)]
def leaves(x,t):return [z for z in walk(x) if z.get('$type')==t]
def ev(x,fs,js):
 t=x.get('$type')
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],fs,js)
 if t=='questLogicalCondition':
  vs=[ev(v,fs,js) for v in x['conditions']]
  if x['operation']=='AND':return False if False in vs else None if None in vs else True
  r=True if True in vs else None if None in vs else False
  return (None if r is None else not r) if x['operation']=='NOR' else r
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in fs:return None
  a,b=fs[x['factName']],x['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return None if x['path']['realPath'] not in js else (js[x['path']['realPath']]==x['state'])!=bool(x.get('inverted',0))
 return None
def state(cond):
 fs={}
 for z in leaves(cond,'questVarComparison_ConditionType'):
  k,v,c=z['factName'],z['value'],z['comparisonType']
  if c=='Equal':fs[k]=v
  elif c in ['Greater','GreaterOrEqual']:fs[k]=max(fs.get(k,-2147483648),v+(c=='Greater'))
  elif c in ['Less','LessOrEqual']:fs[k]=min(fs.get(k,2147483647),v-(c=='Less'))
 js={x['path']['realPath']:x['state'] for x in leaves(cond,'questJournalEntryState_ConditionType')}
 return fs,js
parent=load(r'base\quest\minor_quests\minorquests.questphase')
for p,node_id,n in [(r'towercontinued\sidejobs_s23\base_b\mq030.questphase',18,r'base\quest\minor_quests\mq030\mq030.questphase'),(r'towercontinued\sidejobs_s2\mq032_sacrum.questphase',4,r'base\quest\minor_quests\mq032\mq032_sacrum.questphase'),(r'towercontinued\sidejobs_s23\base_b\mq026.questphase',39,r'base\quest\minor_quests\mq026\mq026.questphase'),(r'towercontinued\sidejobs_s25\prophet\mq026_fresh.questphase',39,r'base\quest\minor_quests\mq026\mq026.questphase')]:
 m=load(p);load(n)
 check('native body node payload exact '+p,nd(m,node_id)==nd(parent,node_id),{'node':node_id,'original_parent':'minorquests'})
 check('native body reference exact '+p,value(nd(m,node_id)['phaseResource']['DepotPath'])==n,{'resource':n})
MQ030=r'towercontinued\sidejobs_s23\base_b\mq030.questphase';M=load(MQ030);B=load(r'towercontinued\b0_story_zane\zane_service.questphase');native30=load(r'base\quest\minor_quests\mq030\mq030.questphase')
check('MQ030 initial lease handoff precedes native owner',all(edge(M,*e) for e in [(1003,'Out',1010,'In'),(1010,'Out',1011,'In'),(1011,'Out',54,'In'),(54,'Out',80,'In'),(80,'Out',55,'In'),(55,'Out',1004,'In'),(1004,'True',1005,'In'),(1005,'Out',1006,'In'),(1006,'Out',18,'In1'),(1006,'Out',1020,'In1')]),{'source':'actual private root'})
for i in [54,80,55]:check('MQ030 exact native prerequisite '+str(i),nd(M,i)==nd(parent,i),nd(M,i))
check('MQ030 natural quest progression preserved',all(edge(native30,*e) for e in [(43,'Out1',63,'In1'),(63,'Out1',64,'In1'),(64,'Out1',83,'In1'),(83,'Out1',1,'In')]),{'route':'43 ->63 ->64 ->83 ->1'})
check('MQ030 actual current early release reproduced',edge(M,18,'Out1',1007,'In') and edge(M,1007,'Out',1012,'In') and nd(M,1012)['type']['factName']=='PTFRB0ZAN_QuestOwns' and nd(M,1012)['type']['value']==0,{'release_route':[18,1007,1012]})
check('MQ030 current helper can remain/rearm',edge(M,1020,'Out1',1021,'In') and edge(M,1021,'Out',1020,'In1') and nd(M,3,'root/1020')['condition']['type']['comparisonType']=='Less' and nd(M,1021)['condition']['type']['comparisonType']=='Greater',{'helper':'default_on<1 termination, default_on>0 rearm; neither checks Finished'})
check('MQ030 two actual phase owners share prefab',nd(M,1020)['phaseInstancePrefabs']==nd(B,5)['phaseInstancePrefabs'] and value(nd(M,1020)['phaseInstancePrefabs'][0]['prefabNodeRef'])=='#pr_cct_dtn_cloth_01',{'helper':1020,'B0owner':5})
bc=nd(B,2)['condition'];fs,js=state(bc);fs.update({'PTFRB0ZAN_QuestOwns':0,'cct_dtn_cloth_01_default_on':1,'mq030_done':1,'mq030_active':0})
check('MQ030 B0 can admit completed case after premature release',ev(bc,fs,js) is True,{'facts':fs,'scope':'Actual predicate; not measured actor duplication'})
repair=C/'repair_mq030';patch=read(repair/'patch.json');after_raw=C/'archive_source'/Path(MQ030.replace('\\','/'))
check('MQ030 candidate raw after hash pins serialized resource',sha(after_raw)==patch['after'],{'path':str(after_raw),'sha256':patch['after']})
A=parse(read(repair/'after.json'));AG=A['root'];MG=M['root']
inc={tuple(e) for e in AG['edges'] if e[2]=='1012'}
safe=lambda g:{tuple(e) for e in g['edges'] if e[2]=='1012'}=={('1022','True','1012','In'),('1023','True','1012','In')}
check('MQ030 final release only after helper ack or retired pending state',safe(AG) and not safe(MG),{'candidate_incoming_release':sorted(inc),'failing_before_passing_after':True})
for e in [(1020,'Out1',1022,'In'),(1022,'False',1021,'In'),(1021,'Out',1023,'In'),(1023,'False',1020,'In1')]:check('MQ030 candidate transition connected '+str(e),edge(A,*e),e)
check('MQ030 helper Terminating ack unchanged',nd(A,1,'root/1020')['type']=='Terminating' and edge(A,3,'Out',5,'Inactive','root/1020') and edge(A,5,'Out',1,'In','root/1020') and A['root/1020']['edges']==M['root/1020']['edges'],{'actual helper natural completion':'3 ->5 ->1 Terminating'})
F='PTFRS23_MQ030_Finished';D='cct_dtn_cloth_01_default_on'
for helper in [True,False]:
 for finished in [0,1]:
  for default in [0,1]:
   cond=nd(A,3,'root/1020')['condition'] if helper else nd(A,1021)['condition'];old=nd(M,3,'root/1020')['condition'] if helper else nd(M,1021)['condition'];f={F:finished,D:default};v=ev(cond,f,{})
   check('MQ030 after gate helper'+str(helper)+' finished'+str(finished)+' default'+str(default),v is True if finished else v==ev(old,f,{}),{'old':ev(old,f,{}),'new':v})
check('MQ030 retained saved IDs/payloads except allowed conditions',set(MG['nodes'])<=set(AG['nodes']) and set(AG['nodes'])-set(MG['nodes'])=={'1022','1023'} and all(nd(M,i)==nd(A,i) for i in MG['nodes'] if i!='1021'),{'original_nodes':len(MG['nodes']),'new_local_nodes':[1022,1023]})
bad=copy.deepcopy(AG);bad['edges'].append(['1007','Out','1012','In']);check('MQ030 real candidate mutation restoring early release fails',not safe(bad),{'oracle':'Shared prefab retirement must dominate lease release'})
SAC=load(r'base\quest\minor_quests\mq032\mq032_sacrum.questphase');PS=load(r'towercontinued\sidejobs_s2\mq032_sacrum.questphase')
check('MQ032 true entry reaches native In1',all(edge(PS,*e) for e in [(0,'Out',1000,'In'),(1000,'Out',1001,'In'),(1002,'True',1003,'In'),(1003,'Out',4,'In1'),(4,'Out1',1004,'In')]),{'entry_node':4,'full_native_body':True})
for e in [(31,'Out',40,'In'),(40,'Out',32,'In1'),(40,'Out',33,'In1'),(32,'Out1',33,'hook_done'),(33,'Success',34,'Success'),(33,'Fail',34,'Fail'),(34,'Out1',1,'In')]:check('MQ032 native progression edge '+str(e),edge(SAC,*e),e)
bad=copy.deepcopy(SAC['root']);bad['edges'].remove(['32','Out1','33','hook_done']);check('MQ032 actual graph mutation missing hook branch detected',['32','Out1','33','hook_done'] not in bad['edges'],{'native expectation':'hook_done connection'})
X=load(r'towercontinued\sidejobs_s23\base_b\mq026.questphase');Y=load(r'towercontinued\sidejobs_s25\prophet\mq026_fresh.questphase');NC=load(r'base\quest\minor_quests\mq026\mq026.questphase')
for label,m in [('S23',X),('S25',Y)]:
 for i in [1002,1004]:
  co=nd(m,i)['condition'];f,j=state(co)
  check('MQ026 '+label+' actual seam positive '+str(i),ev(co,f,j) is True,{'guard':i,'facts':f})
  own='PTFRS23_MQ026_Issued' if label=='S23' else 'PTFRS25_MQ026_FRESH_Issued';other='PTFRS25_MQ026_FRESH_Issued' if label=='S23' else 'PTFRS23_MQ026_Issued'
  check('MQ026 '+label+' excludes other receipt '+str(i),ev(co,f|{other:1},j) is False,other)
  check('MQ026 '+label+' excludes own receipt '+str(i),ev(co,f|{own:1},j) is False,own)
  check('MQ026 '+label+' native cross-prefix history guarded '+str(i),ev(co,f|{'mq027_50_prophet':1},j) is False,{'native initialization':'mq027_50_prophet=0 requires already0'})
f1,j1=state(nd(X,1002)['condition']);f2,j2=state(nd(Y,1002)['condition'])
check('MQ026 genuine serialized seam exclusion both ways',ev(nd(X,1002)['condition'],f2,j2) is False and ev(nd(Y,1002)['condition'],f1,j1) is False,{'S23_first_conspiracy_done':f1['mq026_first_conspiracy_done'],'S25_first_conspiracy_done':f2['mq026_first_conspiracy_done']})
for e in [(0,'Out',3,'In'),(3,'Out',103,'In'),(103,'Out',4,'In'),(33,'combat_out',36,'In1'),(33,'killed_out',106,'In4'),(5,'Out',6,'In')]:check('MQ026 native progression edge '+str(e),edge(NC,*e),e)
# Independently inspect every discovered native quest-scoped source in the closed
# input families; Agent E's list is discovery only, all hashes are recomputed.
qscope={q:[] for q in ['mq030','mq032','mq026']};outside={q:[] for q in qscope}
for d,r in I.items():
 for q in qscope:
  if d.startswith('base\\quest\\minor_quests\\'+q+'\\') and r.get('json'):
   load(d);obj=objects[d];qscope[q].append(d)
   writes=[x for x in walk(obj) if x.get('$type')=='questSetVar_NodeType' and re.match(r'^(audio|holo)_.*_(start|end)_activate$',x.get('factName','')) and x.get('value',0)>0]
   check('no active phone producer in inspected native '+d,not writes,{'positive_request_writers':writes})
   outside[q].extend([x for x in depots(obj) if x.endswith(('.questphase','.scene')) and not x.startswith('base\\quest\\minor_quests\\'+q+'\\')])
for q in qscope:check(q+' native graph/scene closure has no unreviewed external graph',not outside[q],{'resources':qscope[q],'external_graphs':outside[q]})
for q in ['mq030_melisa','mq032_sacrum','mq026_conspiracy']:
 f=W/'prealpha/quest_restoration_qr3/agents/agent_e/quests'/q/'contracts.json';d=read(f)
 check(q+' ten explicit dispositions',len(d['contracts'])==10 and all(x['proven'] and x['evidence'] and x['status'] in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'] for x in d['contracts'].values()),{'contracts_file':str(f),'sha256':sha(f)})
 check(q+' no full static certificate over unresolved placement',not d.get('static_verified'),{'presentation':d['contracts']['presentation']['status']})
 if q!='mq030_melisa':check(q+' unresolved reward definitions not falsely PASS',d['contracts']['completion_rewards_cleanup']['status']=='CONDITIONAL',d['contracts']['completion_rewards_cleanup']['remaining'])
O.mkdir(parents=True,exist_ok=True);out=O/'progression.json';assert not out.exists()
write(out,{'status':'PASS_INDEPENDENT_RAW_REVIEW_WITH_MQ030_REPAIR_LIMITS','reviewer':'AgentB own raw-handle/socket parser, AgentE verifier not imported or executed','quests':['mq030_melisa','mq032_sacrum','mq026_conspiracy'],'checks':checks,'count':len(checks),'inputs':inputs,'mq030_actual_candidate':{'raw':str(after_raw),'sha256':sha(after_raw),'after_json':str(repair/'after.json'),'after_json_sha256':sha(repair/'after.json')},'confirmed_runtime_defects':['QR3-E-MQ030-LEASE baseline early release retains live helper/rearm route with same shared prefab'],'review_disposition':'Candidate structurally repairs the source-confirmed early-release/rearm defect using existing native terminating-output acknowledgement; current baseline AgentE FAIL findings require root after-repair adjudication, not deletion. No new speculative patch justified for MQ032/MQ026.','remaining':['Actual helper teardown output dispatch and saved pending-condition reevaluation remain engine/live boundaries. Previously overlapping saved owners are not automatically repaired.','World placement, reward TweakDB target definitions, original/private saved-owner adoption and actual combat/dialogue/reward delivery remain as stated by AgentE.','Current and historical MQ026 seams are disjoint; no presumed simultaneous-admission race patch is justified.'],'runtime_changes_performed':[]})
print({'status':'PASS_INDEPENDENT_RAW_REVIEW_WITH_MQ030_REPAIR_LIMITS','checks':len(checks),'binary_pins':len(inputs)})
