"""Independent G03 review: no G03 verifier, source loader or models imported."""
from pathlib import Path
import sys,json,argparse,gzip,collections,copy
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');WORK=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'
MINOR=r'base\quest\minor_quests\minorquests.questphase';SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
specs={
 'mq010_barry':dict(short='mq010',private=r'towercontinued\sidejobs_s24\base\mq010.questphase',body=1,native=r'base\quest\minor_quests\mq010\mq010.questphase',guards=[1002,1004],root='quests/minor_quest/mq010_barry',prefix='PTFRS24_MQ010',resources=['phases/mq010_02_barry_talk.questphase','phases/mq010_03_columbarium.questphase','phases/mq010_04_finale.questphase','phases/mq010_cleanup.questphase','scenes/versions/patch1_2/mq010_04_police_talk.scene']),
 'mq024_sandra':dict(short='mq024',private=r'towercontinued\sidejobs_s23\base_a\mq024_sandra.questphase',body=9,native=r'base\quest\minor_quests\mq024\mq024.questphase',guards=[1001,1002],root='quests/minor_quest/mq024_sandra',prefix='PTFRS23_MQ024',phone='sandra',phoneprivate=r'towercontinued\sidejobs_s23\phone\sandra.questphase',resources=['phases/mq024_02a_data_carrier.questphase','phases/mq024_03_sandra_apartment.questphase','phases/mq024_cleanup.questphase','scenes/mq024_01_call_sandra.scene','scenes/mq024_02_meet_sandra.scene']),
 'mq015_wizardbook':dict(short='mq015',private=r'towercontinued\sidejobs_s24\base\mq015.questphase',body=36,native=r'base\quest\minor_quests\mq015\mq015_wizardbook.questphase',guards=[1002,1004],root='quests/minor_quest/mq015_wizardbook',prefix='PTFRS24_MQ015',phone='r3no',phoneprivate=r'towercontinued\sidejobs_s24\phone\r3no.questphase',resources=['phases/mq015_01_hook.questphase','phases/mq015_04_afterlife.questphase','scenes/mq015_02_seller_holocall.scene','scenes/mq015_05_afterlife.scene']),
 'mq019_paparazzi':dict(short='mq019',private=r'towercontinued\sidejobs_s24\base\mq019.questphase',body=38,native=r'base\quest\minor_quests\mq019\mq019_paparazzi.questphase',guards=[1002,1004],root='quests/minor_quest/mq019_paparazzi',prefix='PTFRS24_MQ019',phone='lizzy',phoneprivate=r'towercontinued\sidejobs_s24\phone\lizzy.questphase',resources=['phases/mq019_03_night_club.questphase','phases/mq019_05_holocall.questphase','phases/mq019_06_finale.questphase','scenes/mq019_05_holocall.scene'])}
def evalcond(x,fs,js):
 t=x['$type']
 if t=='questLogicalCondition':
  vs=[evalcond(y,fs,js) for y in x['conditions']];return all(vs) if x['operation']=='AND' else any(vs) if x['operation']=='OR' else not any(vs) if x['operation']=='NOR' else False
 if t in ['questFactsDBCondition','questJournalCondition']:return evalcond(x['type'],fs,js)
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
 assert not O.exists(),'Fresh output required'
 checks=[];pins=[];models={};results={}
 def check(name,ok,evidence,q=None):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',quest_id=q,evidence=evidence));assert ok,name
 deps={MINOR,SH}
 for s in specs.values():
  deps|={s['private'],s['native']};s['depots']=['base\\quest\\minor_quests\\'+s['short']+'\\'+p.replace('/','\\') for p in s['resources']];deps.update(s['depots'])
  if 'phone' in s:
   p=s['phone'];s['hc']='base\\quest\\holocalls\\'+p+'\\'+p+'_holocall.questphase';s['hs']=s['hc'].replace('.questphase','.scene');s['cl']=s['hc'].replace('_holocall','_cleanup');deps|={s['phoneprivate'],s['hc'],s['hs'],s['cl']}
 for d in sorted(deps):
  r=IDX[d];j=Path(r['json']);raw=WORK/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
  if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
  check('current source '+d,raw.is_file() and sha(raw)==r['sha256'],str(raw));m=Resource(read(j)).normalize();check('raw decoder '+d,not m['errors'],m['errors']);models[d]=m
  pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),source_json=str(j),json_sha256=sha(j),provider=r['archive']))
 def g(d,p='root'):return models[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def edge(d,e,p='root'):return list(map(str,e)) in g(d,p)['edges']
 def w(d,i,f,v,p='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,p)['writes'])
 def reward(d,i,name,p='root'):return any(x.get('$type')=='TweakDBID' and value(x)==name for x in walk(n(d,i,p)['payload']))
 for q,s in specs.items():
  d=s['private'];body=s['body'];native=s['native'];proof={}
  check('native saved body identity '+q,n(d,body)['payload']==n(MINOR,body)['payload'] and n(d,body)['refs']==[native],dict(private=d,body=body,native=native),q)
  retained=[]
  for i,node in g(d)['nodes'].items():
   if int(i)<1000 and i in g(MINOR)['nodes']:
    check('retained ancestor payload '+q+':'+i,node['payload']==n(MINOR,i)['payload'],dict(native=MINOR,private=d,node=i),q);retained.append(i)
  proof['retained_native_ancestor_nodes']=retained
  guards=[]
  for i in s['guards']:
   cond=n(d,i)['payload']['condition'];fs,js=fixture(cond);check('actual fresh guard accepts earned stable fixture '+q+':'+str(i),evalcond(cond,fs,js),dict(node=i,facts=len(fs),journal_paths=len(js)),q)
   check('durable receipt rejects reissue '+q+':'+str(i),not evalcond(cond,fs|{s['prefix']+'_Issued':1},js),dict(fact=s['prefix']+'_Issued'),q)
   for state in ['Active','Failed','Succeeded']:
    check('root history '+q+':'+str(i)+state,not evalcond(cond,fs,js|{s['root']:state}),dict(root=s['root'],state=state),q)
   guards.append(dict(node=i,journal_paths=sorted(js),root_state=js.get(s['root']),issued=fs.get(s['prefix']+'_Issued')))
  proof['guard_evidence']=guards
  # Capture original progress/reward/journal/actor refs independently from parsed inputs.
  proof['native_root']=g(native);proof['root_prefabs']=models[native]['root_prefabs'];proof['rewards']=[];proof['fact_writers']=[];proof['journal_changes']=[]
  for nd in [native]+s['depots']:
   for gp,gr in models[nd]['graphs'].items():
    for i,node in gr['nodes'].items():
     if node['reward']:proof['rewards'].append(dict(resource=nd,graph=gp,node=i,records=[value(x) for x in walk(node['payload']) if x.get('$type')=='TweakDBID'],incoming=[e for e in gr['edges'] if e[2]==i]))
     if node['writes']:proof['fact_writers'].append(dict(resource=nd,graph=gp,node=i,writes=node['writes'],incoming=[e for e in gr['edges'] if e[2]==i]))
     if node['journal_paths']:proof['journal_changes'].append(dict(resource=nd,graph=gp,node=i,paths=node['journal_paths'],incoming=[e for e in gr['edges'] if e[2]==i]))
  results[q]=dict(status='AGREE_WITH_EXPLICIT_QUALIFICATIONS',evidence=proof,ten_contract_review={k:'Source pins/targeted native checks confirm scoped finding; original explicit remaining limits retained' for k in ['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']},remaining=['Current target TweakDB definitions/providers and fully resolved world/camera/actor/prefab bindings remain unverified.','Native and saved executing owners, already-issued orphan states, engine call/scene ordering, exactly-once delivery and transition compatibility remain live/save obligations.'])
 # Barry actual native success/failure routes and saved owner, independent of C tests.
 q='mq010_barry';s=specs[q];d=s['native'];cl=s['depots'][3]
 check('Barry parallel columbarium/finale',all(edge(d,e) for e in [(0,'Out',2,'In1'),(2,'Out1',3,'In1'),(3,'Out1',4,'In1'),(3,'Out1',5,'In1'),(5,'Out1',10,'In1'),(2,'failed',19,'In1'),(3,'failed',20,'In1'),(5,'failed',11,'In1')]),d,q)
 check('Barry original flat prefab',models[d]['root_prefabs']==['#mq010_pr_01_barry_flat'],models[d]['root_prefabs'],q)
 check('Barry actual cleanup increment and release',w(cl,8,'mq010_done',1) and n(cl,8)['writes'][0]['setExactValue']==0 and w(cl,7,'mq010_active',0) and edge(cl,[8,'Out',7,'In']),dict(resource=cl,nodes=[8,7],done_semantics='increment, not overwrite'),q)
 finale=s['depots'][2];check('Barry actual root success/failure preserved',edge(finale,[489,'Out',488,'Succeeded']) and edge(finale,[497,'Out',498,'Failed']),dict(resource=finale,nodes=[489,488,497,498]),q)
 check('Barry no phone producer in inspected branch inputs',not any(x.get('value',0)>0 and x.get('factName','').endswith('_activate') and x.get('factName','').startswith(('holo_','audio_')) for nd in [d]+s['depots'] for gr in models[nd]['graphs'].values() for nn in gr['nodes'].values() for x in nn['writes']),s['depots'],q)
 col=s['depots'][1];check('Barry Andrew discovery reward remains',any('QuestRewards.mq010_andrew_discovery'==value(x) for gr in models[col]['graphs'].values() for nn in gr['nodes'].values() for x in walk(nn['payload']) if x.get('$type')=='TweakDBID'),col,q)
 # Sandra two authored owners and original native predicates/branch choices.
 q='mq024_sandra';s=specs[q];d=s['native'];p=s['private'];cl=s['depots'][2]
 check('Sandra carrier watcher separate native owner',n(p,128)['payload']==n(MINOR,128)['payload'] and n(p,128)['refs']==[s['depots'][0]],dict(main=9,watcher=128),q)
 check('Sandra q101 AND earned kab05 before hook',all(edge(d,e) for e in [(0,'Out',13,'In'),(0,'Out',16,'In'),(13,'Out',17,'In1'),(16,'Out',17,'In2'),(17,'Out1',2,'In1')]) and n(d,13)['reads'][0]['factName']=='q101_done' and n(d,16)['reads'][0]['factName']=='kab_05_activated',dict(nodes=[13,16,17,2]),q)
 check('Sandra possession fork retains authored outcomes',all(edge(d,e) for e in [(5,'False',14,'Active'),(5,'True',15,'Active'),(14,'Out',3,'In1'),(15,'Out',4,'In1'),(3,'Out1',4,'In1'),(4,'Out1',10,'In1'),(4,'Out_door',10,'In_door')]),dict(resource=d,predicate=n(d,5)['payload']),q)
 check('Sandra active0 done1 original Succeeded',w(cl,3,'mq024_active',0) and w(cl,4,'mq024_done',1) and edge(cl,[3,'Out',4,'In']) and edge(cl,[4,'Out',2,'Succeeded']),dict(resource=cl,nodes=[3,4,2]),q)
 apt=s['depots'][1];check('Sandra native carrier reward',reward(apt,17,'QuestRewards.mq024_data_carrier_obtained'),dict(resource=apt,node=17),q)
 # Wizardbook exact native chain; Lizzy excluded SQ017 arbitration and cleanup.
 q='mq015_wizardbook';s=specs[q];d=s['native'];check('Spellbound four native phase chain',all(edge(d,e) for e in [(0,'Out',5,'In1'),(5,'Out1',6,'In1'),(6,'Out1',7,'In1'),(7,'Out1',8,'In1')]),d,q)
 after=s['depots'][1];check('Spellbound native active release done and reward path',w(after,32,'mq015_active',0) and w(after,7,'mq015_done',1) and edge(after,[32,'Out',7,'In']) and edge(after,[7,'Out',10,'In']) and reward(after,10,'QuestRewards.mq015_done'),dict(resource=after,nodes=[32,7,10]),q)
 q='mq019_paparazzi';s=specs[q];d=s['native'];check('Lizzy original sequence and SQ017 reentry',all(edge(d,e) for e in [(0,'Out',3,'In1'),(3,'Out1',2,'In1'),(2,'Out1',8,'In1'),(8,'out_sq017_active',22,'In'),(22,'Out',8,'In1'),(8,'Out1',13,'In1'),(13,'Out1',14,'In1')]) and any(r.get('factName')=='sq017_done' for r in n(d,22)['reads']),dict(nodes=[3,2,8,22,13,14]),q)
 finale=s['depots'][2];check('Lizzy native done writer',w(finale,40,'mq019_done',1),dict(resource=finale,node=40),q)
 # Independent earlier actual-raw review is pinned and its four binary inputs revalidated.
 barrier=H.parents[1]/'G01/reviews/s24_phone_barrier_review.json';br=read(barrier)
 check('independent earlier barrier review retained',br['status']=='REJECT_PROPOSED_REPAIR_EXISTING_BARRIER_CONFIRMED',str(barrier))
 for q in ['mq015_wizardbook','mq019_paparazzi']:
  s=specs[q];p=s['private'];phone=s['phone'];receipt='PTFRS24_PHONE_'+phone.upper()+'_Issued';node=n(p,1003)
  check('actual PauseCondition dominates fresh claim '+q,node['type']=='questPauseConditionNodeDefinition' and any(r.get('factName')==receipt and r.get('value')==1 for r in node['reads']) and edge(p,[1002,'Out',1003,'In']) and edge(p,[1003,'Out',54,'In']),dict(resource=p,node=1003,receipt=receipt),q)
  # Node-level control dominance, treating Cut edges as cancellation not progress.
  gr=g(p);badedges=[e for e in gr['edges'] if e[0]!='1003' and e[2]!='1003'];check('claim unreachable if phone barrier removed '+q,'1005' not in reachable(gr['nodes'],badedges,['1000']),dict(claim=1005,removed_node=1003),q)
  results[q]['evidence']['independent_barrier_review']=dict(path=str(barrier),sha256=sha(barrier))
  results[q]['qualifications']=['PhoneIssued pause orders the receipt prerequisite before the quest claim. The phone wrapper writes its receipt before invoking its native initializer; receipt presence alone is not evidence that the engine finished listener activation or delivered an acknowledgement. The rejected interleaving ignored the pause and therefore cannot justify a patch. Already-issued phone0 adoption remains separate.']
 # Sandra counter-name mismatch is actual native source, not permission to reset.
 s=specs['mq024_sandra'];scene=models[s['hs']];cleanup=models[s['cl']]
 names={x['factName'] for gr in scene['graphs'].values() for nn in gr['nodes'].values() for x in nn['writes'] if 'count' in x['factName']}
 reads={x[k] for gr in cleanup['graphs'].values() for nn in gr['nodes'].values() for x in nn['reads'] for k in ['factName1','factName2'] if k in x}
 check('Sandra inherited native counter alias remains unresolved',any('sandra_dorsett' in x for x in names) and any('sandra_' in x and 'sandra_dorsett' not in x for x in reads),dict(native_writes=sorted(names),cleanup_reads=sorted(reads)),'mq024_sandra')
 results['mq024_sandra']['qualifications']=['Sandra phoneIssued prerequisites prove a receipt barrier; activation completion and counter alias semantics remain unproved. The native counter spelling mismatch remains CONDITIONAL and is not a new mod regression.']
 report=dict(status='APPROVED_SCOPED_G03_FINDINGS_WITH_QUALIFICATIONS',reviewer='qr4_worker_a',independent=True,not_imported=['G03/verify.py','G03/lib.py','G03/inspection.json'],source_epoch='source_epoch_00',checks=len(checks),quests=results,tests=checks,source_pins=pins,rejected_repair='Original MQ015/MQ019 listener race counterexample skipped actual blocking1003; no patch justified.',runtime_changes=[],limits='This is a targeted adversarial source review, not a second full auditor run or gameplay proof.')
 write(O/'G03.json',report);return dict(checks=len(checks),resources=len(pins),status=report['status'])
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();print(json.dumps(run(Path(args.output).resolve())))
