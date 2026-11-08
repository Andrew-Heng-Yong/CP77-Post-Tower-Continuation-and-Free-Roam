"""MQ038 actual-resource contract checks. Mutations live only in Python memory.

Run: python -B verify.py --output <fresh-output.json>
No game, source resource, compiler, packer, or deployment writes.
"""
from investigate import *
import argparse,copy,re
P='towercontinued\\sidejobs_s23\\base_b\\mq038.questphase'
JD='towercontinued\\judy_dennis_jd1\\dennis_phone.questphase'
N='base\\quest\\minor_quests\\mq038\\mq038.questphase'
MP='base\\quest\\minor_quests\\minorquests.questphase'
DI='base\\quest\\holocalls\\holocall_initializers.questphase'
DH='base\\quest\\holocalls\\dennis\\dennis_holocall.questphase'
DS='base\\quest\\holocalls\\dennis\\dennis_holocall.scene'
DC='base\\quest\\holocalls\\dennis\\dennis_cleanup.questphase'
UC='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'
NC='base\\quest\\holocalls\\holocall_cleanup.questphase'
V='base\\quest\\minor_quests\\mq038\\phases\\mq038_village.questphase'
VS='base\\quest\\minor_quests\\mq038\\scenes\\mq038_01b_fisher_village.scene'
E='base\\quest\\minor_quests\\mq038\\phases\\mq038_ending.questphase'
ES='base\\quest\\minor_quests\\mq038\\scenes\\mq038_02_ending.scene'
checks=[];pins=[];mods={}
def ck(name,result,evidence):
 checks.append({'name':name,'status':'PASS' if result else 'FAIL','evidence':evidence})
 if not result:raise AssertionError(name)
def model(d):
 if d not in mods:mods[d]=load(d)
 return mods[d]
def graph(d,gp='root'):return model(d)['graphs'][gp]
def node(d,i,gp='root'):return graph(d,gp)['nodes'][str(i)]
def payload(d,i,gp='root'):return node(d,i,gp)['payload']
def fact(x,name,val,cmp='Equal'):
 return any(y.get('$type')=='questVarComparison_ConditionType' and y.get('factName')==name and y.get('comparisonType')==cmp and y.get('value')==val for y in walk(x))
def edge(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in graph(d,gp)['edges']
def path(g,start,target):
 a=collections.defaultdict(list)
 for f,s,t,_ in g['edges']:
  if s!='CutSource':a[f].append(t)
 seen=set();q=[str(start)]
 while q:
  u=q.pop()
  if u==str(target):return True
  if u in seen:continue
  seen.add(u);q.extend(a[u])
 return False
def evaluate(c,f,j):
 # Test fixtures must state every observed predicate input explicitly. Unknown
 # branch inputs remain unknown even when another OR branch could be true.
 for leaf in walk(c):
  if leaf.get('$type')=='questVarComparison_ConditionType' and leaf['factName'] not in f:return False
  if leaf.get('$type')=='questJournalEntryState_ConditionType' and leaf['path']['realPath'] not in j:return False
 typ=c['$type']
 if typ=='questLogicalCondition':
  vs=[evaluate(x,f,j) for x in c['conditions']];op=c['operation']
  return all(vs) if op=='AND' else any(vs) if op=='OR' else not any(vs) if op=='NOR' else (_ for _ in ()).throw(ValueError(op))
 if typ=='questFactsDBCondition':
  t=c['type'];a=f[t['factName']];b=t['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[t['comparisonType']]
 if typ=='questJournalCondition':
  t=c['type'];return (j[t['path']['realPath']]==t['state']) != bool(t.get('inverted',0))
 raise ValueError(typ)
def without_id(x):return {k:v for k,v in x.items() if k!='id'}
def run():
 ds=set(json.loads((OUT/'trace.json').read_text()))|{MP,DI,UC,NC}
 for d in sorted(ds):
  r=INDEX[d];bp=Path(r['json'][:-5]);actual=sha(bp)
  # Native binary hash is pinned independently of normalized model; current
  # private resource bytes are also compared to the PH3 source, not old JSON.
  ck('binary pin '+d,actual==r['sha256'],str(bp))
  pin={'depot':d,'binary':str(bp),'sha256':actual,'json':r['json'],'json_sha256':sha(r['json'])}
  if d.startswith('towercontinued\\'):
   cp=ROOT/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))
   ck('current PH3 equals decoded source '+d,sha(cp)==actual,str(cp));pin['current_source']=str(cp)
  pins.append(pin)
  ck('no graph/handle errors '+d,not model(d)['errors'],r['json'])
 for i in ['54','80','55']:
  ck('native prerequisite payload retained node '+i,payload(P,i)==payload(MP,i),{'private':P,'native':MP,'node':i})
 ck('original MQ038 parent binding and instance-prefabs retained',payload(P,11)==payload(MP,11),{'native_parent':MP,'node':11})
 ck('no omitted MQ038 root/parent phase-prefabs',not model(P)['root_prefabs'] and not model(N)['root_prefabs'] and not model(MP)['root_prefabs'] and payload(P,11)['phaseInstancePrefabs']==[],[P,N,MP])
 ck('preserved sequential native gates before recheck',all(edge(P,*e) for e in [('1003','Out','54','In'),('54','Out','80','In'),('80','Out','55','In'),('55','Out','1004','In')]),P)
 ck('admission rechecked with exact same predicate',payload(P,1002)['condition']==payload(P,1004)['condition'],{'nodes':[1002,1004]})
 native_names={'mq038_active','mq038_deliver_inactive','mq038_done','mq038_dumpster_opened','mq038_fake_01_opened','mq038_fake_02_opened','mq038_hide_inactive'}
 ck('seven untouched native state facts required at both admissions',all(fact(payload(P,i),f,0) for i in [1002,1004] for f in native_names),sorted(native_names))
 journals=[x for x in walk(payload(P,1002)) if x.get('$type')=='questJournalEntryState_ConditionType']
 ck('all thirteen bounded journal states Inactive',len(journals)==13 and all(x['state']=='Inactive' and not x['inverted'] for x in journals),[x['path']['realPath'] for x in journals])
 ac=payload(P,1002)['condition'];af={x['type']['factName']:x['type']['value'] for x in ac['conditions'] if x.get('$type')=='questFactsDBCondition'};aj={x['path']['realPath']:'Inactive' for x in journals}
 ck('actual fresh admission has a satisfying bounded state',evaluate(ac,af,aj),P)
 ck('missing journal is not Inactive',not evaluate(ac,af,{k:v for k,v in aj.items() if k!=next(iter(aj))}),P)
 ck('unknown fact is not native zero',not evaluate(ac,{k:v for k,v in af.items() if k!='mq038_done'},aj),P)
 for jp in aj:
  for state in ['Active','Succeeded','Failed']:
   ck('fresh refuses changed native journal '+jp+'='+state,not evaluate(ac,af,aj|{jp:state}),P)
 for f in sorted(native_names):
  ck('fresh refuses changed native progress '+f,not evaluate(ac,af|{f:1},aj),P)
 ck('fresh quest waits native Dennis listener receipt',fact(payload(P,1003),'PTFRJD1_Dennis_Issued',1) and edge(P,1002,'Out',1003,'In'),{'node':1003})
 ck('once receipt precedes native entry',all(edge(P,*e) for e in [(1004,'True',1005,'In'),(1005,'Out',1006,'In'),(1006,'Out',11,'In1')]),P)
 ck('finish receipt follows native complete Out1',edge(P,11,'Out1',1007,'In') and payload(P,1005)['type']['factName']=='PTFRS23_MQ038_Issued' and payload(P,1007)['type']['factName']=='PTFRS23_MQ038_Finished',P)
 writes=[x for g in model(P)['graphs'].values() for n in g['nodes'].values() for x in n['writes']]
 ck('quest adapter writes only owned positive receipts',all(x['factName'].startswith('PTFRS23_MQ038_') and x['value']==1 for x in writes),writes)
 # Independently stated truth table applied to actual serialized predicates.
 c=payload(JD,1002)['condition']; common={x['factName']:0 for x in walk(c) if x.get('$type')=='questVarComparison_ConditionType'};common|={x['factName']:x['value'] for x in c['conditions'] if x.get('$type')=='questFactsDBCondition' for x in [x['type']]}
 fresh=common|{'PTFRS23_MQ038_Permit':1}; issued=common|{'PTFRS23_MQ038_Issued':1,'PTFRS23_MQ038_Entered':1}
 root='quests/minor_quest/mq038_neweridentity'
 ck('Dennis fresh listener admits Inactive',evaluate(c,fresh,{root:'Inactive'}),JD)
 ck('Dennis existing listener admits Active queued start',evaluate(c,issued|{'holo_dennis_calls_v_start_activate':1},{root:'Active'}),JD)
 for f in ['holo_interrupt_call','holo_active_call_interrupted','holo_interrupt_call_manual','holo_interrupt_braindance']:
  ck('fresh waits but issued owner may hold '+f,not evaluate(c,fresh|{f:1},{root:'Inactive'}) and evaluate(c,issued|{f:1},{root:'Active'}),JD)
 for state in ['Succeeded','Failed']:
  ck('Dennis refuses terminal journal '+state,not evaluate(c,issued,{root:state}) and not evaluate(c,fresh,{root:state}),JD)
 for f,v in [('PTFRJD1_Dennis_Issued',1),('mq038_done',1),('holo_setup_active',1),('holo_dennis_calls_v_end_activate',1)]:
  ck('Dennis refuses '+f,not evaluate(c,issued|{f:v},{root:'Active'}),JD)
 ck('Dennis recheck unchanged',c==payload(JD,1003)['condition'],JD)
 ck('Dennis initializer native payload retained',payload(JD,106)==payload(DI,106),{'private':JD,'native':DI,'node':106})
 ck('Dennis initializer once receipt then In1',edge(JD,1003,'True',1004,'In') and edge(JD,1004,'Out',106,'In1'),JD)
 # Concrete caller protocol including interruption end branch.
 for e in [(122,'0:0',143,'0:1'),(143,'0:0',137,'0:1'),(137,'0:0',138,'0:1'),(144,'0:0',139,'0:1'),(139,'0:0',140,'0:1'),(285,'0:0',272,'0:1'),(272,'0:0',268,'0:1'),(268,'0:0',270,'0:1')]:
  ck('native call edge '+str(e),edge(VS,*e,'scene'),VS)
 for i,f,val,cmp in [(143,'holo_dennis_calls_v_start_activate',1,None),(137,'holo_dennis_calls_v_start_done',0,'Greater'),(138,'holo_dennis_calls_v_start_done',0,None),(144,'holo_dennis_calls_v_end_activate',1,None),(139,'holo_dennis_calls_v_end_done',0,'Greater'),(140,'holo_dennis_calls_v_end_done',0,None),(272,'holo_dennis_calls_v_end_activate',1,None),(268,'holo_dennis_calls_v_end_done',0,'Greater')]:
  p=payload(VS,i,'scene');ok=fact(p,f,val,cmp) if cmp else any(x.get('$type')=='questSetVar_NodeType' and x.get('factName')==f and x.get('value')==val for x in walk(p));ck('native caller protocol node '+str(i),ok,VS)
 ck('native listener consumes real start/end requests',fact(payload(DH,32),'holo_dennis_calls_v_start_activate',0,'Greater') and fact(payload(DH,2),'holo_dennis_calls_v_end_activate',0,'Greater') and edge(DH,9,'Out',26,'holo_dennis_calls_v_start') and edge(DH,10,'Out',26,'holo_dennis_calls_v_end'),DH)
 ck('real start acknowledgement reachable from native start entry',path(graph(DS,'scene'),480,41),DS)
 ck('real end acknowledgement reachable from native end entry',path(graph(DS,'scene'),481,42),DS)
 ck('native cleanup condition retained modulo node ID',without_id(payload(UC,1301))==without_id(payload(NC,439)),{'private_node':1301,'native_node':439})
 ck('native cleanup phase retained modulo node ID',without_id(payload(UC,1302))==without_id(payload(NC,303)),{'private_node':1302,'native_node':303})
 ck('receipt guards native cleanup and current chain connected',fact(payload(UC,1300),'PTFRJD1_Dennis_Issued',1) and edge(UC,1300,'True',1301,'In') and edge(UC,1301,'True',1302,'In13') and any(e[0]=='1302' and e[1]=='Out13' for e in graph(UC)['edges']),UC)
 ck('native cleanup handles unmatched actual counters',any(x.get('factName1')=='holo_dennis_calls_v_start_count' and x.get('factName2')=='holo_dennis_calls_v_end_count' for x in walk(payload(DC,3))) and edge(DC,4,'Out',0,'holo_dennis_calls_v_end'),DC)
 # Explicit body/scene branch and reward paths, no implementation-derived expectations.
 ck('normal native root delegates briefing village ending in sequence',all(edge(N,*e) for e in [(2,'Out',96,'In1'),(96,'Out1',97,'In1'),(97,'Out1',99,'In1')]),N)
 ck('both native early exits join completion cleanup',edge(N,96,'quest_ends',116,'In1') and edge(N,97,'quest_ends',116,'In1') and path(graph(N),116,102),N)
 ck('native completion facts then token/checkpoint and cleanup',all(edge(N,*e) for e in [(99,'Out1',104,'In'),(104,'Out',105,'In'),(105,'Out',122,'In'),(122,'Out',121,'In'),(121,'Out',102,'In1'),(102,'Out1',3,'In')]),N)
 ck('native completion removes contact after message visited',edge(N,46,'True',45,'In','root/102') and edge(N,45,'Out',34,'In','root/102') and 'contacts/darryl/00_msg/00_msg' in node(N,45,'root/102')['journal_paths'],N)
 rewards=[n for n in graph(E)['nodes'].values() if any(x.get('$type')=='questGiveReward_NodeType' for x in walk(n['payload']))]
 ck('one native success reward node with expected identity',len(rewards)==1 and rewards[0]['id']=='16' and any(value(x)=='QuestRewards.mq038_surgeon_saved' for x in walk(payload(E,16)) if x.get('$type')=='TweakDBID'),E)
 ck('success journal precedes reward, no normal reward cycle',edge(E,8,'Out',12,'Succeeded') and edge(E,12,'Out',16,'In') and not any(path(graph(E),e[2],16) for e in graph(E)['edges'] if e[0]=='16'),E)
 ck('katana token remains native scene reward enable',any(x.get('$type')=='questLootTokenManager_NodeTypeParams' and x['lootTokenState']=='Enabled' and value(x['tokenNodeRef'])=='#mq038_katana_token' for x in walk(payload(ES,222,'scene'))),ES)
 ck('SMS native message and contact marker paths retained','contacts/darryl/00_msg/00_msg' in node(V,157)['journal_paths'] and 'quests/minor_quest/mq038_neweridentity/mq038_neweridentity/02b_call_darryl/contact' in node(V,159)['journal_paths'],V)
 ck('native failure SMS precedes Failed journal and quest_ends',edge(V,126,'Out',157,'Active') and edge(V,157,'Out',43,'Failed') and edge(V,43,'Out',2,'In'),V)
 bf='base\\quest\\bugfixing\\minor_quests\\mq038\\mq038_quest_bugfixes.questphase'
 ck('native body includes bugfix katana-loot variant show',without_id(payload(V,158))==without_id(payload(bf,10,'root/1')),{'body':158,'historical_bugfix':'root/1/10'})
 ck('native body includes bugfix drive token unblock',without_id(payload(V,182))==without_id(payload(bf,6,'root/12')) and without_id(payload(V,184))==without_id(payload(bf,6,'root/12')),{'body':[182,184],'historical_bugfix':'root/12/6'})
 ck('native body includes bugfix car forbidden-trigger action',without_id(payload(V,202))==without_id(payload(bf,9,'root/17')),{'body':202,'historical_bugfix':'root/17/9'})
 # Real-resource mutations verify these tests reject plausible regressions.
 mutated=copy.deepcopy(payload(JD,1002)['condition'])
 # Add interruption to the whole conjunction, reproducing the old self-held gate fault.
 mutated['conditions'].append({'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','factName':'holo_interrupt_call_manual','comparisonType':'Equal','value':0}})
 ck('mutation catches issued-owner self-interrupt deadlock',evaluate(c,issued|{'holo_interrupt_call_manual':1},{root:'Active'}) and not evaluate(mutated,issued|{'holo_interrupt_call_manual':1},{root:'Active'}),JD)
 g=copy.deepcopy(graph(VS,'scene'));g['edges'].remove(['143','0:0','137','0:1'])
 ck('mutation catches missing start acknowledgement wait branch',path(graph(VS,'scene'),122,138) and not path(g,122,138),VS)
 g=copy.deepcopy(graph(UC));g['edges']=[e for e in g['edges'] if not(e[0]=='1301' and e[2]=='1302')]
 ck('mutation catches lost cleanup listener connection',path(graph(UC),1300,1302) and not path(g,1300,1302),UC)
 x=copy.deepcopy(payload(P,54));x['condition']['type']['comparisonType']='Less'
 ck('mutation catches native prerequisite change',x!=payload(MP,54),P)
 # Script boundary evidence: no native mutations are attributed to Permit scheduler.
 reds=ROOT/'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
 s=reds.read_text(encoding='utf-8-sig');meth=s[s.index('private func Permit('):s.index('private func Common(')]
 ck('Permit stops after saved Issued owner', 'this.Own(i, "Issued") != 0' in meth and 'Tag(i) + "_Permit"' in meth,str(reds))
 ck('S23 denies unsettled/missing journal and requires two tick samples','jm.HasAnyDelayedStateChanges()' in s and 'this.Same(this.previous[i], current)' in s and 'this.warmup = 3' in s,str(reds))
 pins.append({'script':str(reds),'sha256':sha(reds)})
 return {'quest_id':'mq038_neweridentity','status':'PASS_SCOPED_STATIC_CONTROLS_NOT_FULL_CERTIFICATION','count':len(checks),'checks':checks,'pins':pins,'gameplay_repairs':0,'limits':['NodeRef placement and spawn/workspot/camera resolution require current world descriptor/sector evidence.','Saved active owners and runtime interrupt/reload scheduling are not proven by file parity.','Native reward graph preserved; engine exactly-once save-resume execution is live-only.']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists(),'use fresh output'
 result=run();write(a.output,result);print(json.dumps({k:v for k,v in result.items() if k not in ['pins','checks','limits']}))
