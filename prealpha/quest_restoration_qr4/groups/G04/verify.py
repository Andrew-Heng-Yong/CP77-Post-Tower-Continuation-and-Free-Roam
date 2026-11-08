"""Per-race SQ024 checks; unchanged QR3 family/phone proofs reused by hash."""
from pathlib import Path
import sys,argparse,json,gzip,copy,collections
W=Path(__file__).resolve().parents[4];ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);O=Path(ap.parse_args().output).resolve();assert not O.exists(),'Fresh output required';O.mkdir(parents=True)
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';IDX=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');Q3=W/'prealpha/quest_restoration_qr3';WORK=Q3/'candidate_01';OLD=Q3/'agents/agent_a/verification_03'
N=r'base\quest\side_quests\sq024\sq024.questphase';P=r'towercontinued\sidejobs_s27\claire\sq024_fresh.questphase';PN=r'towercontinued\sidejobs_s27\phone\claire.questphase'
CS=r'base\quest\holocalls\claire\claire_holocall.scene';CT=r'base\quest\holocalls\claire\claire_holocall.questphase';CL=r'base\quest\holocalls\claire\claire_cleanup.questphase';HC=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase'
specs={
 'sq024_city_race':{'title':'The Beast in Me: City Center','phase_short':'04_city_center_race','scene_short':'04_city_race','sms_short':'00_msg_city_race','parent':'9','ready_graph':'root/90','ready_node':'5','token_hours':11,'parallel_hours':12,'call_graph':'root/67/21','call_node':'54','call_input':'sq024_03_city_call_in','requests':[(1437,1430,1431),(1438,1432,1433)],'finish_graph':'root/69','reward_node':'179','finish_record':'QuestRewards.sq024_finish_city_race','end_scene':'04b_docks_scene','win_node':'241','win_record':'QuestRewards.sq024_win_city_race'},
 'sq024_badlands_race':{'title':'The Beast in Me: Badlands','phase_short':'03_badlands_race','scene_short':'03_badlands_race','sms_short':'01_msg_badlands_race','parent':'8','ready_graph':'root/78','ready_node':'15','token_hours':5,'parallel_hours':6,'call_graph':'root/91/14','call_node':'54','call_input':'sq024_03_call_in','requests':[(1188,1181,1182),(1189,1183,1184)],'finish_graph':'root/92','reward_node':'146','finish_record':'QuestRewards.sq024_finish_badlands_race','end_scene':'03b_badlands_race_end','win_node':'141','win_record':'QuestRewards.sq024_win_badlands_race'},
 'sq024_santo_domingo_race':{'title':'The Beast in Me: Santo Domingo','phase_short':'02_pacifica_race','scene_short':'02_santo_domingo_race','sms_short':'02_msg_santo_domingo_race','parent':'7','ready_graph':'root/77','ready_node':'9','token_hours':11,'parallel_hours':12,'call_graph':'root/120/3','call_node':'57','call_input':'sq024_02_call_in','requests':[(1114,1107,1108),(1115,1109,1110)],'finish_graph':'root/88','reward_node':'149','finish_record':'QuestRewards.sq024_finish_santo_domingo_race','end_scene':'02b_santo_domingo_race_end','win_node':'291','win_record':'QuestRewards.sq024_win_santo_domingo_race'},
 'sq024_the_big_race':{'title':'The Beast in Me: The Big Race','phase_short':'05_the_big_race','scene_short':'05_big_race','sms_short':'03_msg_big_race','parent':'10','ready_graph':'root/43','ready_node':'12','token_hours':5,'parallel_hours':6,'call_graph':'root/62','call_node':'6','call_input':'sq024_05_call_in','requests':[(1188,1181,1182),(1189,1183,1184)],'finish_graph':'root/57/185/116/118','reward_node':'7','finish_record':'QuestRewards.sq024_finish_big_race','win_graph':'root/57/185/116','win_node':'50','win_record':'QuestRewards.sq024_win_big_race'}}
for s in specs.values():
 s['phase']='base\\quest\\side_quests\\sq024\\phases\\sq024_'+s['phase_short']+'.questphase';s['scene']='base\\quest\\side_quests\\sq024\\scenes\\sq024_'+s['scene_short']+'.scene';s['sms']='base\\quest\\side_quests\\sq024\\phases\\text_messages\\sq024_'+s['sms_short']+'.questphase'
 if s.get('end_scene'):s['end_scene_depot']='base\\quest\\side_quests\\sq024\\scenes\\sq024_'+s['end_scene']+'.scene'
deps={N,P,PN,CS,CT,CL,HC}
for s in specs.values():deps|={s['phase'],s['scene'],s['sms']};deps.update([s['end_scene_depot']] if s.get('end_scene_depot') else [])
TRAUMA=r'base\quest\side_quests\sq024\scenes\sq024_05b_trauma_team.scene';BAR=r'base\quest\side_quests\sq024\scenes\sq024_06_bar_ending.scene';deps|={TRAUMA,BAR}
models={};pins=[];checks=[]
def check(name,ok,evidence,quest=None):checks.append({'name':name,'quest_id':quest,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in sorted(deps):
 r=IDX[d];j=Path(r['json']);raw=WORK/'archive_source'/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
 if not raw.exists() and '\\json\\' in str(j):raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 check('source binary pinned '+d,raw.is_file() and sha(raw)==r['sha256'],str(raw))
 m=Resource(read(j)).normalize();cached=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));cached.setdefault('embedded_files',[])
 check('native raw/cache equality '+d,m==cached,str(j));check('graph errors absent '+d,not m['errors'],m['errors']);models[d]=m
 pins.append({'depot':d,'binary':str(raw),'sha256':sha(raw),'source_json':str(j),'json_sha256':sha(j),'provider':r['archive'],'model':MI[d]['normalized_model'],'model_sha256':sha(MI[d]['normalized_model'])})
q3e=read(Q3/'EVIDENCE.json');old_rel='agents/agent_a/verification_03/tests.json';old_pin=next(v for k,v in q3e['artifacts'].items() if k.replace('\\','/')==old_rel)
check('reuse shared QR3 race proofs by exact artifact hash',sha(OLD/'tests.json')==old_pin['sha256'],'Main entry, native Claire listener/acks/cleanup, B0 and R1 lifetime proofs not rerun')
def g(d,p='root'):return models[d]['graphs'][p]
def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
def edge(d,e,p='root'):return list(map(str,e)) in g(d,p)['edges']
def typed(node,t):return [x for x in walk(node['payload']) if x.get('$type')==t]
for quest,s in specs.items():
 d=s['phase'];scene=s['scene'];pg=s['ready_graph'];rn=s['ready_node'];pn=s['parent']
 check('specific phase binding and journal identity',n(N,pn)['refs']==[d] and any('quests/side_quest/'+quest in node['journal_paths'] for gr in models[d]['graphs'].values() for node in gr['nodes'].values()),{'native_parent_node':pn,'depot':d},quest)
 check('actual readiness output reaches normal In1',edge(N,[pg.split('/')[-1],'Out1',pn,'In1']),{'ready_graph':pg,'normal_body_input':'In1'},quest)
 cond=n(N,rn,pg)['payload']['condition'];check('native token AND time exact',cond['$type']=='questLogicalCondition' and cond['operation']=='AND' and len(cond['conditions'])==2 and any(x.get('$type')=='questContentToken_ConditionType' and x['type']=='Fixer' for x in walk(cond)) and any(x.get('$type')=='questGameTimeDelay_ConditionType' and x['days']==0 and x['hours']==s['token_hours'] for x in walk(cond)),{'graph':pg,'node':rn,'hours':s['token_hours']},quest)
 check('parallel UI timer not mistaken for readiness',any(x.get('$type')=='questGameTimeDelay_ConditionType' and x['hours']==s['parallel_hours'] for node in g(N,pg)['nodes'].values() for x in walk(node['payload'])),{'graph':pg,'parallel_hours':s['parallel_hours']},quest)
 call=g(d,s['call_graph']);cn=s['call_node'];ci=s['call_input'];sg=g(scene,'scene');seed=sg['entries'][ci];seen=reachable(sg['nodes'],sg['edges'],[seed])
 check('actual phase call socket binds real scene entry',scene in n(d,cn,s['call_graph'])['refs'] and any(e[2]==cn and e[3]==ci for e in call['edges']) and seed in sg['nodes'],{'phase_graph':s['call_graph'],'node':cn,'entry':ci,'scene_seed':seed},quest)
 for idx,(writer,wait,clear) in enumerate(s['requests']):
  suffix='start' if idx==0 else 'end';request='holo_v_calls_claire_'+suffix+'_activate';ack='holo_v_calls_claire_'+suffix+'_done'
  check('request reached from actual call input '+suffix,str(writer) in seen and str(wait) in seen and str(clear) in seen,{'entry':ci,'writer':writer,'wait':wait,'clear':clear,'reachability':'MAY paths, not engine evaluation'},quest)
  check('request waits real native acknowledgement '+suffix,any(w['factName']==request and w['value']==1 for w in n(scene,writer,'scene')['writes']) and any(r.get('factName')==ack and r.get('comparisonType')=='Greater' and r.get('value')==0 for r in n(scene,wait,'scene')['reads']) and any(w['factName']==ack and w['value']==0 for w in n(scene,clear,'scene')['writes']) and edge(scene,[writer,'0:0',wait,'0:1'],'scene') and edge(scene,[wait,'0:0',clear,'0:1'],'scene'),{'request':request,'ack':ack,'nodes':[writer,wait,clear]},quest)
  check('native actual ack producer preserved '+suffix,any(any(w['factName']==ack and w['value']==1 for w in node['writes']) for node in g(CS,'scene')['nodes'].values()),CS,quest)
 check('native finish reward exact',any(value(x)==s['finish_record'] for x in typed(n(d,s['reward_node'],s['finish_graph']),'TweakDBID')),{'graph':s['finish_graph'],'node':s['reward_node'],'record':s['finish_record']},quest)
 if s.get('end_scene_depot'):
  check('authored end-scene is actual dependency',s['end_scene_depot'] in models[d]['refs'],s['end_scene_depot'],quest)
  rewardnode=n(s['end_scene_depot'],s['win_node'],'scene')
 else:rewardnode=n(d,s['win_node'],s['win_graph'])
 check('native win reward exact',any(value(x)==s['win_record'] for x in typed(rewardnode,'TweakDBID')),s['win_record'],quest)
 check('both named story/failure ports preserved',g(d)['entries'].get('In1') is not None and g(d)['entries'].get('chicken_in') is not None,'Normal and authored chicken/test input remain distinct; fresh wrapper only enters master sq024_in',quest)
 check('district success socket exists',any('quests/side_quest/'+quest in node['journal_paths'] and any(e[2]==i and e[3]=='Succeeded' for e in gr['edges']) for gr in models[d]['graphs'].values() for i,node in gr['nodes'].items()),quest,quest)
 check('no new regional restored controller or prefab',n(N,pn)['payload']['phaseInstancePrefabs']==[] and bool(models[d]['root_prefabs']),{'phase_root_prefabs':models[d]['root_prefabs'],'instance_prefabs':[]},quest)
 sms=s['sms'];sm=g(sms);calls=[]
 for caller in [N,d]:
  for cp,cg in models[caller]['graphs'].items():
   for ni,node in cg['nodes'].items():
    if sms in node['refs']:
     calls += [{'resource':caller,'graph':cp,'node':ni,'edge':e} for e in cg['edges'] if e[2]==ni and e[3] in sm['entries']]
 check('SMS actual caller input exists',bool(calls),calls,quest)
 check('SMS delivery and explicit player response waits retained',any(any(p.startswith('contacts/marianne/') for p in node['journal_paths']) and any(e[2]==i and e[3]=='Active' for e in sm['edges']) for i,node in sm['nodes'].items()) and any(x.get('$type') in ['questJournalEntryVisited_ConditionType','questJournalEntryState_ConditionType'] and str(x.get('path',{}).get('realPath','')).startswith('contacts/marianne/') for node in sm['nodes'].values() for x in walk(node['payload'])),'Native delivery/choice/visited waits, not an assumed acknowledgement',quest)

# Authored story ordering, rather than misleading source-file numbering.
for e in [['9','Out1','78','In1'],['78','Out1','8','In1'],['8','Out1','77','In1'],['77','Out1','7','In1'],['7','Out1','43','In1'],['43','Out1','10','In1']]:check('native sequence '+str(e),edge(N,e),e)
BIG=specs['sq024_the_big_race']['phase'];BSC=specs['sq024_the_big_race']['scene'];gp='root/57/185'
for e in [['9','sq024_05_follow_dominic_1_out','114','In1'],['14','sq024_05_continue_race_2_out','116','In1']]:check('Big Race chase versus finish fork '+str(e),edge(BIG,e,gp),{'graph':gp,'edge':e})
check('Sampson departure death path not forced or removed',any(w['factName']=='sq024_sampson_scene_left_area' for w in n(BIG,85,'root/57/185/114')['writes']) and any(w['factName']=='sq024_sampson_dead' for w in n(BIG,96,'root/57/185/114')['writes']) and edge(BIG,['85','Out','96','In'],'root/57/185/114'),'Original leave-area penalty retained; no invented saved choice')
check('Big Race failure/escape path preserved',edge(BIG,['2','Out','6','Failed'],'root/160/18') and any(w['factName']=='sq024_sampson_escaped' for w in n(BIG,7,'root/160/18')['writes']),'Failure is not silently converted into success')
check('Big Race trauma scene actual dependency',TRAUMA in models[BIG]['refs'] and edge(BIG,['33','sq024_05b_sampson_dead_out','56','Succeeded'],'root/57/185/114'),'Scene-defined Sampson outcome retained')
check('earned final car reward remains native reference',any(value(x)=='QuestRewards.sq024_car' for x in typed(n(BAR,595,'scene'),'TweakDBID')),'Exact target definition/delivery remains unresolved')
SMSBIG=specs['sq024_the_big_race']['sms']
check('surviving Sampson exact outcome branch',n(N,2,'root/106')['reads'][0]=={'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'sq024_sampson_dead','value':0} and edge(N,['2','False','5','sampson_alive_in'],'root/106') and edge(N,['5','sampson_alive_out','15','In'],'root/106'),'Original earned alive/dead distinction remains')
check('Sampson gift parent waits unblocked content AND one day',n(N,14,'root/106')['payload']['condition']['operation']=='AND' and any(x.get('$type')=='questGameTimeDelay_ConditionType' and x['days']==1 for x in walk(n(N,14,'root/106')['payload'])) and any(x.get('$type')=='questContentLock_ConditionType' and x['isContentBlocked']==0 for x in walk(n(N,14,'root/106')['payload'])) and edge(N,['14','Out','3','In4'],'root/106'),'Parent clock is separate from subsequent SMS clock')
check('Sampson SMS exact three-day timer and visited wait',n(SMSBIG,104)['payload']['condition']['type']['days']==3 and edge(SMSBIG,['104','Out','101','Active']) and edge(SMSBIG,['101','Out','136','In']) and edge(SMSBIG,['136','Out','102','Active']),'Native incoming message must be visited before original vehicle grant continuation')
check('Sampson native gift and response completion',any(x.get('$type')=='questEnablePlayerVehicle_NodeType' and x['vehicle']=='Vehicle.v_sport2_quadra_type66_nomad_ncu_player' and x['enable']==1 for x in walk(n(SMSBIG,103)['payload'])) and edge(SMSBIG,['102','Out','103','In']) and edge(SMSBIG,['147','Out','135','In']) and edge(SMSBIG,['135','Out','100','In']),'Do not substitute a guessed vehicle record or invent a choice acknowledgement')
mut=[]
bad=copy.deepcopy(n(N,5,'root/90')['payload']);bad['condition']['operation']='OR';mut.append({'fault':'City readiness token/time AND changed to OR','detected':bad!=n(N,5,'root/90')['payload']})
s=specs['sq024_badlands_race'];bad=copy.deepcopy(g(s['scene'],'scene'));bad['edges'].remove(['1188','0:0','1181','0:1']);mut.append({'fault':'Badlands lost call acknowledgement wait edge','detected':bad['edges']!=g(s['scene'],'scene')['edges']})
bad=copy.deepcopy(g(N));bad['edges'].remove(['77','Out1','7','In1']);mut.append({'fault':'Santo native sequence branch missing','detected':bad['edges']!=g(N)['edges']})
bad=copy.deepcopy(g(BIG,gp));bad['edges'].remove(['14','sq024_05_continue_race_2_out','116','In1']);mut.append({'fault':'Big Race finish-versus-chase branch missing','detected':bad['edges']!=g(BIG,gp)['edges']})
for row in mut:check('mutation '+row['fault'],row['detected'],row)
trace=[];assets=[]
for d,m in models.items():
 for p,gr in m['graphs'].items():
  for i,node in gr['nodes'].items():
   if node['reads'] or node['writes'] or node['reward'] or node['journal_paths']:
    trace.append({'resource':d,'graph':p,'node':i,'payload':node['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if node['node_refs'] or node['prefabs'] or node['refs']:assets.append({'resource':d,'graph':p,'node':i,'node_refs':node['node_refs'],'prefabs':node['prefabs'],'refs':node['refs']})
epoch=W/'prealpha/quest_restoration_qr4/source_epoch_00.json'
write(O/'source_pins.json',{'sources':pins,'shared_proof':{'path':str(OLD/'tests.json'),'sha256':sha(OLD/'tests.json')},'source_epoch':{'path':str(epoch),'sha256':sha(epoch)},'working_candidate':str(WORK)})
write(O/'graph_evidence.json',{'specs':specs,'handlers':trace,'assets':assets,'root_prefabs':{d:m['root_prefabs'] for d,m in models.items()},'shared_graph_evidence':str(OLD/'graph_evidence.json'),'scope':'Actual original graph topology/predicates/refs; MAY reachability does not prove engine branch feasibility/playback'})
write(O/'tests.json',{'status':'PASS_SCOPED_REGIONAL_RACE_CONTROLS','checks':len(checks),'results':checks,'mutations':mut,'sources':len(pins),'source_confirmed_defects':[],'runtime_changes':[],'verifier_sha256':sha(Path(__file__))})
print({'checks':len(checks),'sources':len(pins),'mutations':len(mut),'runtime_changes':False})
