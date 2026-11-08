"""Independent actual-resource peer verification; imports no investigated-worker checker."""
from pathlib import Path
import sys,json,copy,re,zlib,collections,argparse
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
ALIASES={r'towercontinued\sidejobs_s28\vehicles\mq050.questphase':r'base\quest\minor_quests\mq050\mq050.questphase',r'towercontinued\sidejobs_s28\vehicles\mq050_johnny_start.scene':r'base\quest\minor_quests\mq050\scenes\mq050_johnny_start.scene',r'towercontinued\sidejobs_s28\encounters\mq022_main.questphase':r'base\quest\minor_quests\mq022\mq022.questphase',r'towercontinued\sidejobs_s28\encounters\mq022_beginning.questphase':r'base\quest\minor_quests\mq022\phases\mq022_beginning.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_main.questphase':r'base\quest\minor_quests\mq003\mq003_orbitals.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_pod_phase.questphase':r'base\quest\minor_quests\mq003\phases\mq003_orbital_pod.questphase',r'towercontinued\sidejobs_s28\encounters\mq003_pod.scene':r'base\quest\minor_quests\mq003\scenes\mq003_03_orbital_pod.scene'}
def native(s):
 if s in ALIASES:return ALIASES[s]
 return re.sub(r'^towercontinued\\sidejobs_s(?:29|30)\\native\\','',s)
def canon(v,key=''):
 if isinstance(v,dict):
  if v.get('$type')=='TweakDBID':
   s=str(v.get('$value','0'));num=int(s) if s.isdigit() else (len(s.encode())<<32)|zlib.crc32(s.encode());return {'$type':'TweakDBID','identity':num}
  return {k:canon(x,k) for k,x in v.items() if k not in ['payload_sha256','metadata_sha256']}
 if isinstance(v,list):
  a=[canon(x) for x in v];return sorted(a,key=lambda x:json.dumps(x,sort_keys=True)) if key=='refs' else a
 if isinstance(v,str):return native(v)
 return v
def run(group,rawdir,O):
 assert not O.exists();H=W/'prealpha/quest_restoration_qr6/groups'/group;res=read(H/'results.json');fresh=read(rawdir/'manifest.json');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_08.json');M={};R={};T=[];issues=[];questproofs={};mutants=[]
 def ck(name,b,e=None):T.append({'name':name,'pass':bool(b),'evidence':e});assert b,(name,str(e)[:800])
 for p in fresh:
  ck('independent fresh source binary '+p['depot'],sha(p['raw'])==p['raw_sha256'],p['raw']);ck('independent readback exported '+p['depot'],p['status']=='EXPORTED',p)
  ck('fresh JSON pin '+p['depot'],sha(p['json'])==p['json_sha256'],p['json']);m=Resource(read(p['json'])).normalize();M[p['depot']]=m;R[p['depot']]=p
  ck('independently normalized fresh graph '+p['depot'],not m['errors'],m['errors']);ck('worker export semantic pair equality '+p['depot'],m==Resource(read(p['worker_json'])).normalize(),p['worker_json'])
  if p['depot'] in E['source_resources']:ck('exact QR5 effective payload '+p['depot'],E['source_resources'][p['depot']]==p['raw_sha256'],p['raw_sha256'])
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def node(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def loc(d,i,gp='root'):
  n=node(d,i,gp);return {'depot':d,'graph':gp,'node':str(i),'payload':n['payload'],'incoming':[e for e in g(d,gp)['edges'] if e[2]==str(i)],'outgoing':[e for e in g(d,gp)['edges'] if e[0]==str(i)]}
 K={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
 for q in res['quest_results']:
  p=Path(q['contracts']);c=read(p);ck('frozen contract hash '+q['quest_id'],sha(p)==q['contracts_sha256'],str(p));ck('all ten source-specific contracts '+q['quest_id'],set(c['contracts'])==K and c['fully_static_verified'] is False,list(c['contracts']))
  for k,v in c['contracts'].items():
   ck('actual specific evidence '+q['quest_id']+':'+k,bool(v['proven']) and bool(v['evidence']) and all(Path(x).is_file() for x in v['evidence']),v['evidence'])
   ck('nontrivial source disposition '+q['quest_id']+':'+k,v['status'] in ['PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'] and all(len(x)>50 for x in v['proven']),v['status'])
  questproofs[q['quest_id']]={'contracts':str(p),'sha256':sha(p),'stages':{k:v['status'] for k,v in c['contracts'].items()}}
 tokens={'B01':['mq050','mq042','mq059','mq060','mq058'],'B02':['mws_wat_08','mws_se5_07','mq022','mq003'],'B03':['sq023','sq025']}[group]
 comparisons=[]
 for d,m in M.items():
  if not d.startswith('towercontinued') or not any(t in d for t in tokens):continue
  nd=native(d)
  if nd==d or nd not in M:continue
  if d.endswith('.questphase') and not d.endswith(('mq022_beginning.questphase','sq025.questphase')):
   ck('independent whole native phase semantics '+d,canon(M[nd])==canon(m),{'native':nd,'restored':d,'graphs':len(m['graphs'])});comparisons.append({'native':nd,'restored':d,'whole_phase_exact':True})
  elif d.endswith('.scene'):
   ck('independent complete scene socket topology '+d,all(m['graphs'][gp]['edges']==gg['edges'] and m['graphs'][gp]['entries']==gg['entries'] for gp,gg in M[nd]['graphs'].items()),nd)
   ck('independent all scene side effects/dialogue '+d,all(canon(nn['writes'])==canon(m['graphs'][gp]['nodes'][i]['writes']) and nn['journal_paths']==m['graphs'][gp]['nodes'][i]['journal_paths'] for gp,gg in M[nd]['graphs'].items() for i,nn in gg['nodes'].items()) and canon(M[nd]['metadata'].get('screenplayStore'))==canon(m['metadata'].get('screenplayStore')),nd)
 # Exact independently selected source controls, separate from generalized equality.
 controls=[]
 def ctrl(q,name,d,i,predicate,gp='root'):
  n=node(d,i,gp);ck(name,predicate(n),loc(d,i,gp));controls.append((name,d,str(i),gp,predicate));questproofs[q].setdefault('specific_raw_controls',[]).append(loc(d,i,gp))
 if group=='B01':
  q='mq050_ken_block_tribute';d=r'towercontinued\sidejobs_s28\vehicles\mq050.questphase';ctrl(q,'Hoon actual vehicle record and acquisition',d,28,lambda n:n['payload']['type']['enable']==1 and n['payload']['type']['vehicle']=='Vehicle.v_sport2_quadra_type66_nomad_tribute');ctrl(q,'Hoon exact one-key injection',d,51,lambda n:any(x.get('quantity')==1 and x.get('itemTDBID',{}).get('$value')=='99716362400' for x in walk(n['payload'])));ck('Hoon native alternative remains XOR',node(d,84)['type']=='questLogicalXorNodeDefinition',loc(d,84))
  sc=r'towercontinued\sidejobs_s28\vehicles\mq050_johnny_start.scene';sn=ALIASES[sc];ck('Hoon only Johnny scene node4 presentation payload changes',all(canon(nn['payload'])==canon(node(sc,i,gp)['payload']) for gp,gg in M[sn]['graphs'].items() for i,nn in gg['nodes'].items() if i!='4'),sn);ck('Hoon owned workspot65000 exact binding',node(sc,4,'scene')['payload']['questNode']['paramsV1']['$type']=='scnUseSceneWorkspotParamsV1' and node(sc,4,'scene')['payload']['questNode']['paramsV1']['workspotInstanceId']['id']==65000,loc(sc,4,'scene'))
  q='mq042_nomad';d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq042\mq042_nomad.questphase';ctrl(q,'Nomad exact native earned lifepath',d,6,lambda n:any(x.get('$type')=='LifePath_ScriptConditionType' and x.get('inverted')==0 and x.get('lifePathId',{}).get('$value')=='67091901544' for x in walk(n['payload'])));ctrl(q,'Nomad distance token actual AND',d,17,lambda n:n['payload']['condition']['operation']=='AND' and any(x.get('distanceValue')==50 for x in walk(n['payload'])))
  q='mq059_freedom';d=r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq059\mq059.questphase';ctrl(q,'Freedom actual postquest SMS contact',d,575,lambda n:'contacts/muamar_el_capitan_reyes/mq059/postquest' in n['journal_paths']);ctrl(q,'Freedom existing external cleanup owner',d,604,lambda n:r'towercontinued\sidejobs_s29\native\base\quest\minor_quests\mq059\phases\mq059_cleanup.questphase' in n['refs'])
  q='mq058_semimaru_crystalcoat';d=r'towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase';ctrl(q,'Eagles exact earned native prerequisite conjunction',d,64001,lambda n:n['payload']['condition']['operation']=='AND' and {(x['factName'],x['comparisonType'],x['value']) for x in n['reads']}=={('sq024_done','Equal',1),('mq057_done','Equal',1),('mq058_failed_to_open_vvc','Equal',1)});nativeglobal=r'base\quest\bugfixing\quest_bugfixing.questphase';a=copy.deepcopy(node(nativeglobal,100,'root/3')['payload']);a['id']=64001;ck('Eagles complete executing-global predicate preserved',a==node(d,64001)['payload'],{'native':loc(nativeglobal,100,'root/3'),'current':loc(d,64001)})
  q='mq060_nitro';conflict=Path(__file__).parent/'reviews/B01_nitro/verification_01/review.json';ck('Nitro full-group conclusions preserve independently unresolved authority',read(conflict)['status']=='DIVERGENCE_CONFIRMED_REPAIR_BLOCKED_SOURCE_AUTHORITY' and all(questproofs[q]['stages'][k]=='UNKNOWN' for k in ['entry','eligibility','shared_dependencies']),str(conflict));questproofs[q]['source_authority_review']={'path':str(conflict),'sha256':sha(conflict)}
  # No generic absent phone controller error: inspect every selected actual local closure writer.
  for tok in tokens:
   requests=[{'depot':d,'graph':gp,'node':i,'write':x} for d,m in M.items() if '\\'+tok+'\\' in d or tok=='mq050' and d.startswith('towercontinued\\sidejobs_s28\\vehicles\\mq050') for gp,gg in m['graphs'].items() for i,n in gg['nodes'].items() for x in n['writes'] if x.get('factName','').startswith(('holo_','audio_')) and x.get('value',0)>0];ck('selected local closure contains no holo/audio producers '+tok,not requests,requests)
 if group=='B02':
  q='mws_wat_08_trauma_drama';d=r'towercontinued\sidejobs_s30\native\base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase';ctrl(q,'Career earned leaderboard actual predicate',d,6,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'shooter_appeared_on_leaderboard','value':0}]);ctrl(q,'Career exact starter prefab context',d,12,lambda n:n['prefabs']==['#mws_wat_08_pr_starter']);ctrl(q,'Career exact reward prefab context',d,15,lambda n:n['prefabs']==['#mws_pr_trauma_drama']);ck('Career old-notification history remains unknown',questproofs[q]['stages']['persistence']=='UNKNOWN',questproofs[q]['stages'])
  q='mws_se5_07';d=r'towercontinued\sidejobs_s30\native\base\open_world\mini_world_stories\badlands\se5\mws_se5_07\mws_se5_07.questphase';ctrl(q,'Pony earned car prerequisite',d,3,lambda n:any(x.get('factName')=='porsche_911_930_turbo_cabriolet_owned' and x.get('value')==1 for x in n['reads']));ck('Pony full native ancestor location lease',M[d]['root_prefabs']==['#mws_se5_07_shape_of_a_pony'],M[d]['root_prefabs'])
  q='mq022_ezekiel';d=r'towercontinued\sidejobs_s28\encounters\mq022_beginning.questphase';nd=ALIASES[d];ck('Ezekiel all native original node payloads exact',all(canon(nn['payload'])==canon(node(d,i,gp)['payload']) for gp,gg in M[nd]['graphs'].items() for i,nn in gg['nodes'].items()),nd);ck('Ezekiel exact readiness edge splice only',set(map(tuple,g(d)['edges']))-set(map(tuple,g(nd)['edges']))=={('58','Out','65000','In'),('65000','Out','71','In')} and set(map(tuple,g(nd)['edges']))-set(map(tuple,g(d)['edges']))=={('58','Out','71','In')},g(d)['edges']);ctrl(q,'Ezekiel readiness is private rather than completion',d,65000,lambda n:n['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRS28_mq022_ezekiel_DinerStartReady','setExactValue':1,'value':1}])
  q='mq003_orbitals';d=r'towercontinued\sidejobs_s28\encounters\mq003_pod_phase.questphase';ck('SpaceOddity exact orbital pod root obligation',M[d]['root_prefabs']==['#mq003_pr_orbital_pod'],M[d]['root_prefabs']);ctrl(q,'SpaceOddity native pod reward target',d,66,lambda n:value(n['payload']['type']['rewards'][0])=='155544231233')
 if group=='B03':
  q='sq023_hit_order';d=r'towercontinued\sidejobs_s29\entries\sq023_hit_order.questphase';ctrl(q,'SQ023 earned q104 exact native prerequisite',d,42,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'q104_done','value':1}]);ck('SQ023 one fresh owner guards all three histories',len(node(d,65003)['journal_paths'])==186 and len([x for x in M if x.startswith('towercontinued\\sidejobs_s29\\entries\\sq023')])==1,node(d,65003)['journal_paths'])
  shared=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';ctrl(q,'Current Rachel exact specialized-owner lease fence',shared,1255,lambda n:n['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS29_PHONE_rachel_Issued','value':1}])
  d=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\phases\sq023_aftermath.questphase';ctrl('sq023_real_passion','Studio native aftermath twelve game hours',d,15,lambda n:n['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':12,'minutes':0,'seconds':0});ck('Studio real doubt outcome strict Less4',node(d,25)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Less','factName':'sq023_joshua_doubting','value':4}],loc(d,25))
  d=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq025\phases\sq025_05a_messages.questphase';ctrl('sq025b_delamain_insurgence','Native Delamain message delay four game hours',d,53,lambda n:n['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':0,'hours':4,'minutes':0,'seconds':0});ctrl('sq025b_delamain_insurgence','Native Delamain real message choice acknowledgement',d,14,lambda n:n['payload']['condition']['type']['state']=='Succeeded' and n['payload']['condition']['type']['path']['realPath'].endswith('/scan04a_deeper'))
  whole=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq023\sq023.questphase'
  for edge in [['12','Out1','13','In1'],['13','Out1','15','In1'],['15','Out1','32','In1'],['32','Out1','33','In1'],['33','Out1','34','In1'],['34','Out1','48','In'],['48','Out','46','In1'],['46','Out1','36','In'],['36','Out','22','In1']]:ck('One actual SQ023 native chain '+str(edge),edge in g(whole)['edges'],edge)
  private=r'towercontinued\sidejobs_s29\native\base\quest\side_quests\sq025\sq025.questphase';donor=native(private);keep={'80','81','82','83','86','110','126','127','128','129','130','131','134','137','139','150','161','162'};ck('Delamain fixed reviewed selected-root identity',set(g(private)['nodes'])==keep|{'65000'},sorted(g(private)['nodes']))
  for i in sorted(keep):ck('Delamain exact original selected node '+i,canon(node(private,i))==canon(node(donor,i)),loc(donor,i))
  ck('Delamain only reviewed native selection and new entry edges',g(private)['edges']==sorted([e for e in g(donor)['edges'] if e[0] in keep and e[2] in keep]+[['65000','Out','134','In1']]),g(private)['edges'])
  ck('Delamain no Epistrophy scan/reward replay','79' not in g(private)['nodes'] and '124' not in g(private)['nodes'],sorted(keep))
  for gp,gg in M[private]['graphs'].items():
   if gp!='root':ck('Complete saved native Delamain nested graph '+gp,canon(gg)==canon(g(donor,gp)),gp)
  initial=r'base\quest\holocalls\holocall_initializers.questphase'
  for contact,ni in [('rachel',83),('delamain',51)]:
   pd='towercontinued\\sidejobs_s29\\phone\\'+contact+'.questphase';ck('Actual specialized native initializer '+contact,canon(node(pd,ni))==canon(node(initial,ni)),loc(pd,ni));scene='base\\quest\\holocalls\\'+contact+'\\'+contact+'_holocall.scene'
   for wi in [41,42,43,44]:ck('Real source acknowledgement '+contact+str(wi),len(node(scene,wi,'scene')['writes'])==1 and node(scene,wi,'scene')['writes'][0]['value']==1 and node(scene,wi,'scene')['writes'][0]['factName'].endswith('_done'),loc(scene,wi,'scene'))
  nativecleanup=r'base\quest\holocalls\holocall_cleanup.questphase'
  for cur,old in [(1210,473),(700,438)]:ck('Current remapped cleanup retains exact native comparison '+str(cur),node(shared,cur)['payload']['condition']==node(nativecleanup,old)['payload']['condition'],{'current':loc(shared,cur),'native':loc(nativecleanup,old)})
  for edge in [['1255','True','1210','In'],['1255','False','1300','In'],['1210','True','1211','In47'],['1211','Out47','1300','In'],['700','True','701','In12'],['701','Out12','800','In']]:ck('Actual current shared cleanup socket '+str(edge),edge in g(shared)['edges'],edge)
  ck('Current cleanup real Rachel/Delamain resource bindings',node(shared,1211)['refs']==[r'base\quest\holocalls\rachel\rachel_cleanup.questphase'] and node(shared,701)['refs']==[r'base\quest\holocalls\delamain\delamain_cleanup.questphase'],{'Rachel':loc(shared,1211),'Delamain':loc(shared,701)})
  studio=r'towercontinued\phone_studios_ph3\studio_support.questphase';allprefabs=[p for gg in M[studio]['graphs'].values() for nn in gg['nodes'].values() for p in nn['prefabs']];ck('Actual PH3 shared studio obligations retained',len(set(allprefabs))==2,allprefabs)
 # Deliberate actual raw node mutations must be rejected by independently chosen predicate.
 for ix,(name,d,i,gp,pred) in enumerate(controls):
  if ix>=4:break
  raw=copy.deepcopy(read(R[d]['json']));changed=0
  for x in walk(raw):
   if str(x.get('id'))==i and x.get('$type')==node(d,i,gp)['type']:
    for z in walk(x):
     if z.get('factName'):z['value']=999;changed+=1
     if z.get('quantity')==1:z['quantity']=0;changed+=1
     if z.get('enable')==1:z['enable']=0;changed+=1
     if z.get('$type')=='LifePath_ScriptConditionType':z['inverted']=1;changed+=1
     if z.get('distanceValue')==50:z['distanceValue']=0;changed+=1
     if z.get('$type')=='questGameTimeDelay_ConditionType':z['hours']=0;changed+=1
     if z.get('prefabNodeRef') is not None:z['prefabNodeRef']['$value']='#QR6_review_missing';changed+=1
  mm=Resource(raw).normalize();caught=not pred(mm['graphs'][gp]['nodes'][i]);ck('independent actual readback mutation '+name,changed>0 and caught,{'changes':changed,'resource':d,'node':i});p=O/'mutations'/(str(ix)+'.json');write(p,raw);mutants.append({'name':name,'path':str(p),'sha256':sha(p),'caught':caught})
 write(O/'tests.json',T);write(O/'source_pins.json',fresh);write(O/'quest_review.json',questproofs);write(O/'comparisons.json',comparisons);write(O/'mutations.json',mutants);write(O/'review.json',{'group':group,'status':'PASS_INDEPENDENT_SOURCE_REVIEW_WITH_EXPLICIT_UNRESOLVED_LIMITS','checks':len(T),'failures':0,'reviewed_quests':res['quest_ids'],'contract_count':res['contract_count'],'source_resources':len(M),'fresh_readbacks':len(fresh),'raw_mutations':len(mutants),'issues':issues,'group_results':str(H/'results.json'),'group_results_sha256':sha(H/'results.json'),'limits':['Static body/predicate/lifecycle comparisons do not prove live saved owners, world placement or execution.','MQ060 authority conflict and Career historical notification ambiguity remain unresolved if applicable.','Raw JSON mutations are source fault controls, not binary/gameplay execution.'],'runtime_changes':[]});print({'checks':len(T),'readbacks':len(fresh),'mutations':len(mutants),'review':str(O/'review.json'),'sha256':sha(O/'review.json')})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);p.add_argument('--raw',required=True);p.add_argument('--output',required=True);a=p.parse_args();run(a.group,Path(a.raw),Path(a.output))
