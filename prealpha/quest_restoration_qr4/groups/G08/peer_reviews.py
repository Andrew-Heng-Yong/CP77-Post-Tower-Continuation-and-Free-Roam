"""Worker-B independent raw-source reviews of G04/G07; no peer verifier imports."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from verify import path
from common import read,write,sha,walk
def review_g04():
 O=H/'reviews/G04.json';assert not O.exists();M={};pins=[];checks=[];details=[]
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p)
  return M[d]
 def g(d,gp='root'):return load(d)['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def ck(name,ok,ev):checks.append({'name':name,'pass':bool(ok),'evidence':ev});assert ok,name
 master='base\\quest\\side_quests\\sq024\\sq024.questphase';fresh='towercontinued\\sidejobs_s27\\claire\\sq024_fresh.questphase';phone='towercontinued\\sidejobs_s27\\phone\\claire.questphase';ctl='base\\quest\\holocalls\\claire\\claire_holocall.questphase';hs='base\\quest\\holocalls\\claire\\claire_holocall.scene'
 ck('fresh_delegates_exact_native_family',n(fresh,100)['refs']==[master],n(fresh,100)['refs'])
 ck('fresh_native_listener_binding',n(phone,46)['refs']==[ctl],n(phone,46)['refs'])
 ck('postclaim_requires_listener_receipt',any(x.get('factName')=='PTFRS27_PHONE_CLAIRE_Issued'and x.get('value')==1 for x in n(fresh,90)['reads']),'fresh90 barrier before native100')
 for a,b in [(9,8),(8,7),(7,10)]:ck('native_story_sequence '+str(a)+str(b),bool(path(g(master),a,b)),path(g(master),a,b))
 cases=[('sq024_city_race',9,'sq024_04_city_center_race','root/67/21',54,'sq024_04_city_race','sq024_03_city_call_in',[(1437,1430,1431),(1438,1432,1433)]),('sq024_badlands_race',8,'sq024_03_badlands_race','root/91/14',54,'sq024_03_badlands_race','sq024_03_call_in',[(1188,1181,1182),(1189,1183,1184)]),('sq024_santo_domingo_race',7,'sq024_02_pacifica_race','root/120/3',57,'sq024_02_santo_domingo_race','sq024_02_call_in',[(1114,1107,1108),(1115,1109,1110)]),('sq024_the_big_race',10,'sq024_05_the_big_race','root/62',6,'sq024_05_big_race','sq024_05_call_in',[(1188,1181,1182),(1189,1183,1184)])]
 for q,owner,phase,gp,si,scene,entry,protocols in cases:
  d='base\\quest\\side_quests\\sq024\\phases\\'+phase+'.questphase';s='base\\quest\\side_quests\\sq024\\scenes\\'+scene+'.scene'
  ck('actual_family_race_binding '+q,n(master,owner)['refs']==[d],{'owner':owner,'target':d})
  ck('actual_race_scene_call_input '+q,n(d,si,gp)['refs']==[s]and any(x[2]==str(si)and x[3]==entry for x in g(d,gp)['edges']),{'graph':gp,'node':si,'input':entry})
  gg=g(s,'scene');start=gg['entries'][entry]
  for typ,(prod,wait,clear)in zip(['start','end'],protocols):
   req='holo_v_calls_claire_'+typ+'_activate';done='holo_v_calls_claire_'+typ+'_done';inp='holo_v_calls_claire_'+typ
   ck('actual_caller_request '+q+typ,any(x['factName']==req and x['value']==1 for x in n(s,prod,'scene')['writes'])and bool(path(gg,start,prod)),{'entry':entry,'producer':prod,'path':path(gg,start,prod)})
   ck('actual_request_wait_clear '+q+typ,bool(path(gg,prod,wait))and bool(path(gg,wait,clear))and any(x.get('factName')==done for x in n(s,wait,'scene')['reads'])and any(x['factName']==done and x['value']==0 for x in n(s,clear,'scene')['writes']),{'producer':prod,'wait':wait,'clear':clear})
   readers=[i for i,nd in g(ctl)['nodes'].items()if any(x.get('factName')==req for x in nd['reads'])];resets=[i for i,nd in g(ctl)['nodes'].items()if any(x.get('factName')==req and x.get('value')==0 for x in nd['writes'])]
   routes=[(rd,cl)for rd in readers for cl in resets if path(g(ctl),rd,cl)and [cl,'Out','21',inp]in g(ctl)['edges']]
   ck('actual_consumer_reset_scene '+q+typ,bool(routes),routes)
   ack=[i for i,nd in g(hs,'scene')['nodes'].items()if any(x.get('factName')==done and x.get('value')==1 for x in nd['writes'])and path(g(hs,'scene'),g(hs,'scene')['entries'][inp],i)]
   ck('real_reachable_ack '+q+typ,bool(ack),{'scene_input':inp,'ack_writers':ack})
  details.append({'quest_id':q,'native_phase':d,'native_phase_hash':I.IDX[d]['sha256'],'native_scene':s,'native_scene_hash':I.IDX[s]['sha256'],'actual_call_input':entry})
 big='base\\quest\\side_quests\\sq024\\phases\\sq024_05_the_big_race.questphase';bg=g(big,'root/57/185')
 ck('BigRace_actual_choice_fork',['9','sq024_05_follow_dominic_1_out','114','In1']in bg['edges']and ['14','sq024_05_continue_race_2_out','116','In1']in bg['edges'],'follow/chase versus finish race, full native socket prefixes retained')
 ck('G04_limits_visible',all(not read(H.parent/'G04/quests'/q/'contracts.json')['fully_static_verified']for q,*_ in cases),'opaque world/TDB/saved/engine limits remain')
 write(O,{'reviewer':'worker_B','method':'Independent raw pins and Resource normalization; no G04 verifier imports/runs.','status':'NO_NEW_SOURCE_DEFECT_FOUND_WITH_LIMITS','checks':checks,'total_checks':len(checks),'source_pins':pins,'quests':details,'remaining':['Shared family original retirement/HS1 and all race actor/world/reward definitions not independently recertified here.','MAY reachability proves connected protocols, not exact race gameplay, times, phone arbitration or engine scheduling.','Review assertion initially copied abbreviated G04 prose socket names; actual native names include sq024_05_ prefix. Source proved the retained fork; no resource defect.'],'runtime_changes':[]})
 return len(checks)
def review_g07():
 O=H/'reviews/G07.json';assert not O.exists();M={};pins=[];checks=[];cases=[]
 def load(d):
  if d not in M:m,p=I.load(d);M[d]=m;pins.append(p)
  return M[d]
 def g(d,gp='root'):return load(d)['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def ck(name,ok,ev):checks.append({'name':name,'pass':bool(ok),'evidence':ev});assert ok,name
 core=H.parent/'G02/shared_core.json';ck('frozen_G02_core_unchanged',sha(core)=='6C7DAF85ED6345729092B3BF22EF6E1C176E95B6829824D11BD19A49D6DED4EC',str(core))
 native='base\\quest\\side_quests\\sq025\\phases\\sq025_04_scan.questphase';private='towercontinued\\sidejobs_s22\\delamain\\scan.questphase';scene='base\\quest\\side_quests\\sq025\\scenes\\sq025_05_scan.scene';ctl='base\\quest\\holocalls\\delamain\\delamain_holocall.questphase';hs='base\\quest\\holocalls\\delamain\\delamain_holocall.scene'
 for q,emotion,case in [('sq025c04_manic','manic',192),('sq025c01_angry','angry',189),('sq025c02_sad','sad',190),('sq025c03_mean','mean',191),('sq025c06_mean','deep',194)]:
  gp='root/'+str(case);ck('whole_case_native_graph '+q,g(private,gp)==g(native,gp),{'graph':gp,'native':native,'private':private})
  entrances=[(i,e[3])for i,nd in g(native,gp)['nodes'].items()if scene in nd['refs']for e in g(native,gp)['edges']if e[2]==i];ck('both_actual_owned_scene_inputs '+q,sorted(t for i,t in entrances)==[emotion+'_in',emotion+'_in_talk'],entrances)
  seeds=[g(scene,'scene')['entries'][t]for i,t in entrances];protocol=[]
  for ni,nd in g(scene,'scene')['nodes'].items():
   requests=[x for x in nd['writes']if x['value']==1 and x['factName'].startswith('holo_delamain_'+emotion+'_calls_v_')and x['factName'].endswith('_activate')]
   for req in requests:
    r=req['factName'];done=r[:-9]+'_done';inp=r[:-9];reach=any(path(g(scene,'scene'),s,ni)for s in seeds)
    ck('case_actual_producer_reachable '+q+ni,reach,{'producer':ni,'request':r,'owned_inputs':entrances})
    wait=[i for i,x in g(scene,'scene')['nodes'].items()if any(z.get('factName')==done for z in x['reads'])and path(g(scene,'scene'),ni,i)]
    clear=[i for i,x in g(scene,'scene')['nodes'].items()if any(z.get('factName')==done and z.get('value')==0 for z in x['writes'])and any(path(g(scene,'scene'),w,i)for w in wait)]
    ck('case_request_wait_clear '+q+ni,bool(wait)and bool(clear),{'producer':ni,'wait':wait,'clear':clear,'done':done})
    readers=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==r for z in x['reads'])];resets=[i for i,x in g(ctl)['nodes'].items()if any(z.get('factName')==r and z.get('value')==0 for z in x['writes'])]
    paths=[(a,b)for a in readers for b in resets if path(g(ctl),a,b)and [b,'Out','21',inp]in g(ctl)['edges']]
    ck('case_real_handler '+q+ni,bool(paths),paths)
    ack=[i for i,x in g(hs,'scene')['nodes'].items()if any(z.get('factName')==done and z.get('value')==1 for z in x['writes'])and path(g(hs,'scene'),g(hs,'scene')['entries'][inp],i)]
    ck('case_real_ack '+q+ni,bool(ack),ack);protocol.append({'producer':ni,'request':r,'waits':wait,'clears':clear,'controller_routes':paths,'acknowledgements':ack})
  claim=read(H.parent/'G07/quests'/q/'contracts.json');ck('outer154_gap_retained '+q,any('154'in x for x in claim['contracts']['eligibility']['remaining']),'original outer token/mail arbitration not silently approved')
  cases.append({'quest_id':q,'emotion':emotion,'native_graph':gp,'protocols':protocol,'case_payload':g(native,gp)})
 # Specific thresholds branch independently checked, avoiding generic equality alone.
 ck('Manic_flamingo_threshold',any(x.get('factName')=='sq025_flamingos_destroyed'and x.get('comparisonType')=='Greater'and x.get('value')==7 for x in n(scene,2617,'scene')['reads']),'destroy8, original>7')
 angry=n(scene,2580,'scene')['payload'];ck('Angry_original_20percent_vehicle',any(x.get('$type')=='questCharacterHealth_ConditionType'and x.get('percent')==20 and x.get('comparisonType')=='LessOrEqual'and x.get('objectRef',{}).get('reference',{}).get('$value')=='#sq025_com_delamain_angry'for x in walk(angry)),'exact native vehicle <=20 percent predicate')
 ck('Sad_roundabout_shared_gate',any(x.get('factName')=='mq014_roundabout'and x.get('comparisonType')=='Less'and x.get('value')==1 for x in n(scene,3476,'scene')['reads']),'original mq014 shared prerequisite')
 ck('Deep_separate_done_fanout',any(x.get('factName')=='sq025_deep_done'and x.get('value')==1 for x in n(scene,936,'scene')['writes']),'journal suffix mean is emotion deep; native counter/done siblings not invented ordering')
 write(O,{'reviewer':'worker_B','method':'Independent raw/model pins, whole native case comparisons and explicit owned scene-input→producer→wait/clear→controller→real-ack checks. No G07 verifier imported or run. Frozen G02 core reused without redoing it.','status':'NO_NEW_SOURCE_DEFECT_FOUND_WITH_LIMITS','checks':checks,'total_checks':len(checks),'source_pins':pins,'cases':cases,'remaining':['Stable source paths/MAY reachability do not prove live callbacks, counters, placement or saved descendant retirement.','Frozen G02 correction in G06/G02_self_correction.json applies: fresh body and listener fanout are concurrent, not strict listener-before-body proof.','Native angry/deep cleanup label mismatches are inherited; no synthetic counter resets or old disproved Delamain patch.'],'runtime_changes':[]})
 return len(checks)
if __name__=='__main__':print(json.dumps({'G04_checks':review_g04(),'G07_checks':review_g07()}))
