"""Five SQ025 car contracts; source-pinned checks and raw-resource mutations.

Requires --output NEW_DIRECTORY. Does not import G02's verifier or write inputs.
The frozen G02 core is reused by hash, with G06's explicit concurrency correction.
"""
from pathlib import Path
import sys,argparse,json,copy,collections,gzip
W=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
BASE=W/'prealpha/quest_restoration_qr4';WORK=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json')
NS=r'base\quest\side_quests\sq025\phases\sq025_04_scan.questphase';SC=r'base\quest\side_quests\sq025\scenes\sq025_05_scan.scene'
SCAN=r'towercontinued\sidejobs_s22\delamain\scan.questphase';P=r'towercontinued\sidejobs_s25\families\sq025_fresh.questphase';OWN=r'towercontinued\sidejobs_s22\delamain\owner.questphase';SUP=r'towercontinued\sidejobs_s22\delamain\support.questphase'
HC=r'base\quest\holocalls\delamain\delamain_holocall.questphase';HS=r'base\quest\holocalls\delamain\delamain_holocall.scene';CL=r'base\quest\holocalls\delamain\delamain_cleanup.questphase'
SPECS={
 'sq025c04_manic':dict(case='manic',title='Epistrophy: Rancho Coronado',phase=192,index=4,activate=263,hub=303,scene=12,talk=22,split=23,done=942,counter=3820,journal=1283,reward=4175,cleanup=106,cleanup_target=6,ready=3515,distance=60,normal_request=7372,mechanism='Destroy eight flamingos: scene/2617 requires sq025_flamingos_destroyed >7; repeat conversation has second start request7513.'),
 'sq025c01_angry':dict(case='angry',title='Epistrophy: Wellsprings',phase=189,index=1,activate=259,hub=313,scene=17,talk=58,split=57,done=927,counter=3770,journal=1264,reward=1157,cleanup=102,cleanup_target=2,ready=3467,distance=40,normal_request=6918,mechanism='Native destructive pursuit: scene/2580 requires the angry car health <=20%; combat release9789 precedes done927.'),
 'sq025c02_sad':dict(case='sad',title='Epistrophy: North Oak',phase=190,index=2,activate=260,hub=301,scene=12,talk=23,split=24,done=7693,counter=3782,journal=1267,reward=3941,cleanup=103,cleanup_target=3,ready=3476,distance=30,normal_request=7257,mechanism='North Oak escort: readiness3476 additionally ANDs mq014_roundabout <1; vehicle door1541, player mount1106, native stop trigger1112 and unmount2689 remain; damaged/crowd/water/breaks reactions bind the default Delamain scene.'),
 'sq025c03_mean':dict(case='mean',title='Epistrophy: Coastview',phase=191,index=3,activate=261,hub=302,scene=12,talk=32,split=31,done=945,counter=3829,journal=1287,reward=4165,cleanup=104,cleanup_target=4,ready=3526,distance=60,normal_request=7410,mechanism='Coastview ambush: talk_end3130, talk_02_end3412, combat_done1039 and talk_03_end3428 remain; native case tail41 fans to terminating output and wait42 mean_cleanup_started>0 before cleanup40.'),
 'sq025c06_mean':dict(case='deep',title='Epistrophy: Badlands',phase=194,index=6,activate=265,hub=305,scene=12,talk=24,split=25,done=936,counter=3801,journal=1276,reward=4047,cleanup=107,cleanup_target=7,ready=None,distance=None,normal_request=7324,mechanism='Badlands uses native deep emotion despite journal suffix mean. root/194 entry writes sq025_deep_active1; scene includes player mount/dialogue and authored damaged/destroyed parallel branches7729/7733 (70%/16%). Dialogue choices1000/1359 preserve other-world/organic mention guards; done936 is a separate authored fan-out from counter3801.'),
}
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,so,y,si in g['edges']:
   if x==p[-1] and so!='CutSource' and si!='CutDestination' and y not in seen:seen.add(y);q.append(p+[y])
 return None
def evaluate(x,fs,js):
 t=x['$type']
 if t=='questLogicalCondition':
  v=[evaluate(y,fs,js) for y in x['conditions']]
  return all(v) if x['operation']=='AND' else any(v) if x['operation']=='OR' else not any(v) if x['operation']=='NOR' else False
 if t in ['questFactsDBCondition','questJournalCondition']:return evaluate(x['type'],fs,js)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in fs:return False
  a=fs[x['factName']];b=x['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return x['path']['realPath'] in js and ((js[x['path']['realPath']]==x['state'])!=bool(x.get('inverted',0)))
 raise ValueError(t)
def fixture(cond):
 fs={};js={}
 for x in walk(cond):
  if x.get('$type')=='questVarComparison_ConditionType':fs[x['factName']]=x['value']+1 if x['comparisonType']=='Greater' else x['value']-1 if x['comparisonType']=='Less' else x['value']
  if x.get('$type')=='questJournalEntryState_ConditionType':js.setdefault(x['path']['realPath'],x['state'])
 return fs,js
def run(O):
 assert not O.exists(),'Fresh --output directory required'
 tests=[];pins=[];models={};rawjson={}
 def check(name,ok,evidence,quest=None):
  tests.append(dict(name=name,status='PASS' if ok else 'FAIL',quest_id=quest,evidence=evidence));assert ok,name
 corepath=BASE/'groups/G02/shared_core.json';core=read(corepath)
 check('frozen independent shared core',sha(corepath)=='6C7DAF85ED6345729092B3BF22EF6E1C176E95B6829824D11BD19A49D6DED4EC',str(corepath))
 correction=BASE/'groups/G06/G02_self_correction.json';corr=read(correction)
 check('shared correction explicitly retained',corr['shared_core_sha256']==sha(corepath) and 'concurrent' in corr['corrections'][0]['actual'],str(correction))
 for key in ['source_pins','graph_evidence','tests']:
  p=corepath.parent/core[key];check('reuse core artifact '+key,sha(p)==core[key+'_sha256'],str(p))
 for d,pin in core['resources'].items():
  check('current core binary '+d,sha(pin['binary'])==pin['sha256'],pin['binary'])
 for d in [NS,SC,SCAN,P,OWN,SUP,HC,HS,CL]:
  r=IDX[d];j=Path(r['json']);raw=WORK/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
  if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
  check('exact current binary '+d,raw.is_file() and sha(raw)==r['sha256'],str(raw))
  rawjson[d]=read(j);m=Resource(rawjson[d]).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
  check('raw parsed model equals pinned cache '+d,m==cached,str(j));check('no graph decoding errors '+d,not m['errors'],m['errors']);models[d]=m
  pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),source_json=str(j),json_sha256=sha(j),model=MI[d]['normalized_model'],model_sha256=sha(MI[d]['normalized_model']),provider=r['archive']))
 def g(d,p='root'):return models[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def edge(d,e,p='root'):return list(map(str,e)) in g(d,p)['edges']
 def typed(node,t):return [x for x in walk(node['payload']) if x.get('$type')==t]
 def writes(node,f,v):return any(x.get('factName')==f and x.get('value')==v for x in node['writes'])
 sg=g(SC,'scene');hg=g(HS,'scene');cg=g(HC);evidence={};protocols=[];mutations=[]
 for q,s in SPECS.items():
  c=s['case'];gp='root/'+str(s['phase']);journal='quests/side_quest/'+q
  check('case graph native exact '+q,g(SCAN,gp)==g(NS,gp),dict(native=NS,private=SCAN,graph=gp),q)
  check('native case prefab and saved phase identity '+q,n(SCAN,s['phase'])['payload']==n(NS,s['phase'])['payload'] and n(SCAN,s['phase'])['prefabs']==['#sq025_pr_'+c],n(SCAN,s['phase'])['prefabs'],q)
  check('native main and talk scene inputs '+q,edge(NS,[s['split'],'Out2',s['scene'],c+'_in'],gp) and edge(NS,[s['split'],'Out1',s['talk'],c+'_in_talk'],gp) and SC in n(NS,s['scene'],gp)['refs'] and SC in n(NS,s['talk'],gp)['refs'],dict(graph=gp,scene=s['scene'],talk=s['talk']),q)
  check('native case output into seven-car AND '+q,edge(NS,[s['phase'],'Out1',198,'In'+str(s['index'])]),dict(node=198,input=s['index']),q)
  # Explicitly solve the serialized Boolean trees; do not flatten facts into AND.
  seams=[]
  for d,ni in [(P,3),(P,90),(OWN,1003)]:
   cond=n(d,ni)['payload']['condition'];fs,js=fixture(cond);check('native actual admission fixture '+q+d+str(ni),evaluate(cond,fs,js),dict(resource=d,node=ni),q)
   expected=1 if d==OWN and c in ['sad','mean'] else 0
   check('case done seam exact '+q+d+str(ni),fs.get('sq025_'+c+'_done')==expected,dict(fact='sq025_'+c+'_done',expected=expected),q)
   check('opposite done history rejected '+q+d+str(ni),not evaluate(cond,fs|{'sq025_'+c+'_done':1-expected},js),dict(expected=expected),q)
   check('succeeded case history protects fresh or admits bounded seam '+q+d+str(ni),evaluate(cond,fs,js|{journal:'Succeeded'})==bool(expected),dict(journal=journal,resource=d,node=ni,expected=bool(expected)),q)
   seams.append(dict(resource=d,node=ni,case_done=expected,scan_count=fs.get('sq025_scans_done'),fresh_issued=fs.get('PTFRS25_SQ025_FRESH_Issued')))
  skip=n(SCAN,1000+s['index'])['payload']['condition'];fs,js=fixture(skip)
  check('progressed done and Succeeded skip actual native restart '+q,evaluate(skip,fs,js) and not evaluate(skip,fs|{'sq025_'+c+'_done':0},js) and not evaluate(skip,fs,js|{journal:'Inactive'}) and edge(SCAN,[1000+s['index'],'True',198,'In'+str(s['index'])]) and edge(SCAN,[1000+s['index'],'False',s['activate'],'In']),dict(condition=skip,node=1000+s['index']),q)
  cleanup=g(SCAN,'root/267');cn=s['cleanup'];ct=s['cleanup_target']
  check('cleanup protects Succeeded journal '+q,n(SCAN,cn,'root/267')['reads'][0]['state']=='Succeeded' and journal in n(SCAN,cn,'root/267')['journal_paths'] and [str(cn),'False',str(ct),'Inactive'] in cleanup['edges'] and any(e[0]==str(cn) and e[1]=='True' and e[2]!=str(ct) for e in cleanup['edges']),dict(graph='root/267',guard=cn,journal_node=ct),q)
  entry=sg['entries'][c+'_in'];talkentry=sg['entries'][c+'_in_talk'];seen=reachable(sg['nodes'],sg['edges'],[entry]);case_seen=seen|reachable(sg['nodes'],sg['edges'],[talkentry]);normal=s['normal_request']
  check('case normal request and native outputs reachable '+q,all(str(i) in seen for i in [normal,s['done'],s['counter'],s['journal'],s['reward']]),dict(entry=entry,normal_request=normal,targets=[s['done'],s['counter'],s['journal'],s['reward']],semantics='MAY reachability, conditions/scene choices still apply'),q)
  check('native specific completion receipt '+q,writes(n(SC,s['done'],'scene'),'sq025_'+c+'_done',1),dict(node=s['done'],fact='sq025_'+c+'_done'),q)
  inc=n(SC,s['counter'],'scene')['writes'];check('native additive scan counter '+q,len(inc)==1 and inc[0]['factName']=='sq025_scans_done' and inc[0]['value']==1 and inc[0]['setExactValue']==0,dict(node=s['counter'],write=inc),q)
  check('specific journal Succeeded input '+q,journal in n(SC,s['journal'],'scene')['journal_paths'] and any(e[2]==str(s['journal']) and e[3]=='0:3' for e in sg['edges']),dict(node=s['journal'],input='0:3'),q)
  check('specific native reward binding '+q,any(value(x)=='QuestRewards.sq025_each_scan_completed' for x in typed(n(SC,s['reward'],'scene'),'TweakDBID')) and bool(path(sg,s['counter'],s['reward'])),dict(reward_node=s['reward'],record='QuestRewards.sq025_each_scan_completed'),q)
  if s['ready']:
   cond=typed(n(SC,s['ready'],'scene'),'questLogicalCondition')[0]
   check('case distance AND unblocked content '+q,cond['operation']=='AND' and any(x.get('$type')=='questValueDistance' and x.get('distanceValue')==s['distance'] for x in walk(cond)) and any(x.get('$type')=='questContentLock_ConditionType' and x.get('isContentBlocked')==0 for x in walk(cond)),dict(node=s['ready'],distance=s['distance'],condition=cond),q)
  caseprotocol=[]
  # Inventory every case request producer, including alternate/repeated end branches.
  for ni,node in sg['nodes'].items():
   requests=[x['factName'] for x in node['writes'] if x.get('value')==1 and x.get('factName','').endswith('_activate') and (x['factName'].startswith('holo_delamain_'+c+'_') or x['factName'].startswith('holo_v_calls_delamain_'+c+'_'))]
   for req in requests:
    base=req.removesuffix('_activate');done=base+'_done';targets=[e[2] for e in sg['edges'] if e[0]==ni];waits=[i for i in targets if any(r.get('factName')==done and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in sg['nodes'][i]['reads'])]
    clears=[e[2] for wa in waits for e in sg['edges'] if e[0]==wa and writes(sg['nodes'][e[2]],done,0)]
    rd=[i for i,nn in cg['nodes'].items() if any(r.get('factName')==req and r.get('comparisonType')=='Greater' for r in nn['reads'])]
    cl=[i for i,nn in cg['nodes'].items() if writes(nn,req,0) and [i,'Out','21',base] in cg['edges']]
    ak=[i for i,nn in hg['nodes'].items() if writes(nn,done,1) and base in hg['entries'] and path(hg,hg['entries'][base],i)]
    check('every connected case request waits and clears '+q+':'+ni,bool(waits and clears) and ni in case_seen,dict(producer=ni,request=req,waits=waits,clears=clears,actual_case_input=c+'_in' if ni in seen else c+'_in_talk'),q)
    check('every native listener and real acknowledgement '+q+':'+ni,bool(rd and cl and ak) and bool(path(cg,rd[0],cl[0])),dict(request=req,readers=rd,controller_clears=cl,scene_input=base,actual_ack_writers=ak),q)
    caseprotocol.append(dict(producer=ni,request=req,waits=waits,clears=clears,controller_readers=rd,controller_clears=cl,ack_writers=ak,actual_case_input=c+'_in' if ni in seen else c+'_in_talk',producer_path=path(sg,entry if ni in seen else talkentry,ni),ack_paths=[path(hg,hg['entries'][base],i) for i in ak]))
  # Native cleanup counter labels are recorded literally; no manufactured reset.
  rd=[(i,nn) for i,nn in g(CL)['nodes'].items() if any(r.get('factName1')=='holo_delamain_'+c+'_calls_v_start_count' and r.get('factName2')=='holo_delamain_'+c+'_calls_v_end_count' for r in nn['reads'])]
  check('native case interrupt cleanup route '+q,len(rd)==1 and any(e[0]==rd[0][0] and e[1]=='True' for e in g(CL)['edges']),dict(native_cleanup_reader=rd[0][0] if rd else None,reads=rd[0][1]['reads'] if rd else []),q)
  # Every raw scene counter is mutated and re-normalized independently of writes metadata.
  bad=copy.deepcopy(rawjson[SC]);target=next(x for x in walk(bad) if x.get('$type')=='scnQuestNode' and x.get('nodeId',{}).get('id')==s['counter']);setvar=next(x for x in walk(target) if x.get('$type')=='questSetVar_NodeType' and x.get('factName')=='sq025_scans_done');setvar['value']=2
  bm=Resource(bad).normalize();det=bm['graphs']['scene']['nodes'][str(s['counter'])]['writes'][0]['value']!=1
  mutations.append(dict(quest_id=q,fault='Raw scene scan increment changed1to2',node=s['counter'],detected=det));check('raw counter mutation detected '+q,det,mutations[-1],q)
  evidence[q]=dict(spec=s,scene_entry=entry,case_graph=gp,seams=seams,normal_request_path=path(sg,entry,normal),normal_request_to_done=path(sg,normal,s['done']),normal_request_to_counter=path(sg,normal,s['counter']),entry_to_done=path(sg,entry,s['done']),counter_to_success=path(sg,s['counter'],s['journal']),counter_to_reward=path(sg,s['counter'],s['reward']),phone_protocols=caseprotocol,case_phase_graph=g(NS,gp),native_phase_prefab=n(NS,s['phase'])['prefabs'],native_cleanup_reader=rd[0][0],journal_nodes=[dict(node=i,paths=nn['journal_paths'],incoming=[e for e in sg['edges'] if e[2]==i]) for i,nn in sg['nodes'].items() if any(p.startswith(journal) for p in nn['journal_paths'])])
  protocols+=caseprotocol
 # Specific mechanisms are checked against actual source fields, beyond source equality.
 check('angry health threshold20percent',any(x.get('percent')==20 and x.get('comparisonType')=='LessOrEqual' for x in typed(n(SC,2580,'scene'),'questCharacterHealth_ConditionType')),2580,'sq025c01_angry')
 check('sad roundabout exclusion exact',any(r.get('factName')=='mq014_roundabout' and r.get('comparisonType')=='Less' and r.get('value')==1 for r in n(SC,3476,'scene')['reads']),3476,'sq025c02_sad')
 check('sad stop trigger bound',any(value(x)=='#sq025_tr_sad_stop' for x in typed(n(SC,1112,'scene'),'NodeRef')),1112,'sq025c02_sad')
 check('mean combat ack required',any(r.get('factName')=='sq025_mean_combat_done' and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in n(SC,1039,'scene')['reads']),1039,'sq025c03_mean')
 check('mean cleanup wait native retained',edge(NS,[41,'Out1',42,'In'],'root/191') and edge(NS,[42,'Out',40,'In'],'root/191') and n(NS,42,'root/191')['reads'][0]['factName']=='mean_cleanup_started',dict(graph='root/191',nodes=[41,42,40]),'sq025c03_mean')
 check('manic exact eight-flamingo predicate',any(r.get('factName')=='sq025_flamingos_destroyed' and r.get('comparisonType')=='Greater' and r.get('value')==7 for r in n(SC,2617,'scene')['reads']),2617,'sq025c04_manic')
 check('deep emotion ownership distinct from mean',writes(n(NS,18,'root/194'),'sq025_deep_active',1) and 'quests/side_quest/sq025c06_mean' in n(NS,17,'root/194')['journal_paths'],dict(phase=194,active=18,journal=17),'sq025c06_mean')
 for ni,pct in [(7729,70),(7733,16)]:check('deep native damage branch '+str(ni),any(x.get('percent')==pct for x in typed(n(SC,ni,'scene'),'questCharacterHealth_ConditionType')),dict(node=ni,percent=pct),'sq025c06_mean')
 # Remove a real raw call connection, not a derived metadata field.
 bad=copy.deepcopy(rawjson[SC]);target=next(x for x in walk(bad) if x.get('$type')=='scnQuestNode' and x.get('nodeId',{}).get('id')==7372)
 for so in target['outputSockets']:so['destinations']=[x for x in so['destinations'] if x['nodeId']['id']!=7369]
 bm=Resource(bad).normalize();det=['7372','0:0','7369','0:1'] not in bm['graphs']['scene']['edges'];mutations.append(dict(fault='Raw manic phone wait connection removed',detected=det));check('raw phone edge mutation',det,mutations[-1])
 # Raw predicate mutation catches a plausible wrong threshold in the source.
 bad=copy.deepcopy(rawjson[SC]);target=next(x for x in walk(bad) if x.get('$type')=='scnQuestNode' and x.get('nodeId',{}).get('id')==2617);next(x for x in walk(target) if x.get('$type')=='questVarComparison_ConditionType')['value']=6
 det=Resource(bad).normalize()['graphs']['scene']['nodes']['2617']['reads'][0]['value']!=7;mutations.append(dict(fault='Raw flamingo eligibility threshold changed7to6',detected=det));check('raw prerequisite mutation',det,mutations[-1])
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',dict(quests=evidence,phone_protocol_count=len(protocols),shared_core=str(corepath),shared_core_sha256=sha(corepath),concurrency_correction=str(correction),concurrency_correction_sha256=sha(correction),root_prefabs={d:models[d]['root_prefabs'] for d in models},limits=core['other_limits']+[core['unresolved_parent_gate']]))
 write(O/'tests.json',dict(status='PASS_SCOPED_STATIC_CHECKS',count=len(tests),checks=tests,mutations=mutations,source_epoch='source_epoch_00',runtime_changes=[],limits='MAY reachability is structural, never proof of branch feasibility, delivery, engine ordering, reward receipt or saved-owner retirement.'))
 return dict(checks=len(tests),mutations=len(mutations),resources=len(pins),protocols=len(protocols))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args();print(json.dumps(run(Path(args.output).resolve())))
