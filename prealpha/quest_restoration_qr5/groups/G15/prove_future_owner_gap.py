"""Prove separate U9 Steven message versus default-owner obligations; no patch."""
from pathlib import Path
import sys,copy,collections
W=Path(__file__).resolve().parents[4];H=Path(__file__).resolve().parent;O=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource,reachable
out=H/'steven_gap_01';assert not out.exists();I=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json');E=read(O/'source_epoch_00.json');M=read(H/'inspection_01/models.json');pins=read(H/'inspection_01/pins.json');tests=[]
def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
def load(d):
 if d in M:return M[d]
 r=I[d];j=Path(r['json']);raw=j.with_suffix('')
 if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 assert sha(raw)==r['sha256'];m=Resource(read(j)).normalize();assert not m['errors'];M[d]=m;pins.append({'depot':d,'binary':str(raw),'sha256':r['sha256'],'json':str(j),'json_sha256':sha(j),'provider':r['archive']});return m
spy='towercontinued\\native_gigs_u9\\sts_ep1_08_entry.questphase';boot='towercontinued\\sidejobs_s23\\ep1\\steven_boot.questphase';cleanup='ep1\\openworld\\street_stories\\sts_ep1_08\\phases\\sts_ep1_08_cleanup.questphase';default='ep1\\quest\\ep1_default_dialogs.questphase';additional='ep1\\quest\\ep1_additional_game_elements.questphase';ep1='ep1\\quest\\ep1.questphase';actor='ep1\\quest\\tertiary_characters\\default_dialogs\\steven_santos_default\\steven_default.questphase'
sg=M[spy]['graphs']['root/50'];bg=M[boot]['graphs']['root'];cg=M[cleanup]['graphs']['root/3'];ag=load(ep1)['graphs']['root/10'];ad=load(additional)
ck('genuine_Tower_condition_in_EP1_cut',any(x.get('state')=='Succeeded'and x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'for x in ag['nodes']['8']['reads']),'Native8 OR also handlesPONR; actual Tower journal path, not receipt alone')
ck('native_cut_precedes_retired_receipt',all(e in ag['edges']for e in [['8','Out','9','In'],['9','CutSource','4','CutDestination'],['9','Out','10','In']])and ag['nodes']['10']['writes'][0]['factName']=='q307_ep1_killed',ag['edges'])
ck('cut_contains_additional_default_owner',additional in ag['nodes']['4']['refs']and default in ad['graphs']['root']['nodes']['1']['refs'],'EP1root10/4→additionalroot1→default17')
dg=M[default]['graphs']['root'];ck('native_default_wait_call_loop',all(e in dg['edges']for e in [['19','Out','17','In1'],['17','Out1','19','In']])and actor in dg['nodes']['17']['refs'],'Native19 waits default_on>0 and q304escape0')
ck('private_gig_rehosts_real_native_cleanup',all(e in sg['edges']for e in [['23','Out1','64000','In1'],['23','Out1','65005','In']])and cleanup in sg['nodes']['64000']['refs'],'Unchanged native cleanup plus genuine MainFinished callback')
ck('private_native_cleanup_reaches_followup',all(e in M[cleanup]['graphs']['root']['edges']for e in [['0','Out','88','In'],['88','Out','3','In1']]),'Main23.Out1→cleanup.In1→root0→88→3')
ck('native_nightcity_invitation_and_default_signal',all(e in cg['edges']for e in [['3','False','5','In'],['56','Out','8','In'],['8','Out','58','Active'],['17','Out','59','Succeeded'],['59','Out','9','Active'],['9','Out','2','In']])and cg['nodes']['2']['writes']==[{'$type':'questSetVar_NodeType','factName':'steven_santos_default_on','setExactValue':1,'value':1}],'66hour invitation→visited→meeting→real default_on1')
ck('native_wait_retains_66hours',cg['nodes']['5']['payload']['condition']['type']['hours']==66,cg['nodes']['5']['payload'])
for i in ['2','3','90']:
 reads=bg['nodes'][i]['reads'];ck('only_private_actor_owner_excludes_U9 '+i,all(any(r.get('factName')==f and r.get('comparisonType')=='Equal'and r.get('value')==0 for r in reads)for f in ['PTFRU9_sts_ep1_08_ParentEntered','PTFRU9_sts_ep1_08_Started','steven_santos_default_on']),reads)
hits=read(H/'context_scan_01/hits.json');private_actor_readers=[x for x in hits if x['depot'].startswith('towercontinued')and actor in x['refs']]
ck('unique_private_default_actor_reader',len(private_actor_readers)==1 and private_actor_readers[0]['depot']==boot,private_actor_readers)
ck('no_private_call_of_broader_default_parent',not[d for d,r in I.items()if d.startswith('towercontinued')and any(x in r.get('refs',[])for x in [default,additional,ep1])],'Do not confuse absent direct actor refs with a hidden broad parent')
subset=M[boot]['graphs']['root/100/501'];ck('existing_preTower_message_slice_exact_native_subset',all(cg['nodes'][i]==n for i,n in subset['nodes'].items())and subset['edges']==[e for e in cg['edges']if e[0]in subset['nodes']and e[2]in subset['nodes']],'Current supported preTower adapter itself remains correct; do not relax it/replay messages')
for i in ['17','19']:ck('existing_private_actor_payload_native '+i,M[boot]['graphs']['root/100']['nodes'][i]==dg['nodes'][i],i)
ck('native_actor_scopes_have_no_phase_prefabs',not M[actor]['root_prefabs']and not M[default]['root_prefabs']and not ad['root_prefabs']and all(not n['prefabs']for g in M[actor]['graphs'].values()for n in g['nodes'].values()),'World/community binding still needs exact placement review; no new prefab invented')
counterexample={'future_spy_parent_entered':1,'future_spy_started':1,'native_cleanup_invitation_sent_and_visited':True,'native_default_on':1,'private_steven_boot_guard':'REFUSES_U9_ParentEntered_andStarted1_andDefaultOn1','sole_original_default_owner':'Cut under genuine Tower','missing':'Native NightCity actor/dialogue owner; SMS is already owned by real native cleanup'}
write(out/'tests.json',{'status':'PASS_SOURCE_CONFIRMED_FUTURE_U9_ACTOR_OWNER_GAP','checks':len(tests),'tests':tests});write(out/'source_pins.json',pins);write(out/'models.json',M)
write(out/'evidence.json',{'id':'QR5-STEVEN-U9-FUTURE-DEFAULT-OWNER','status':'SOURCE_CONFIRMED_PENDING_INDEPENDENT_REVIEW','quest_id':'sts_ep1_08_steven_meeting_night_city','carrier_resource':spy,'carrier_sha256':E['source_resources'][spy],'native_actor':actor,'counterexample':counterexample,'global_scan':str(H/'context_scan_01/summary.json'),'tests':str(out/'tests.json'),'tests_sha256':sha(out/'tests.json'),'source_pins':str(out/'source_pins.json'),'existing_policy':'S23 excludes U9 because it owns its followup: native message producer is indeed owned, but separate default actor owner is not. Preserve exclusion; add only missing future actor consumer.','limits':['Original provider/world/community runtime resolution and saved executing state remain bounded/opaque.','Already-entered U9 saved owners require separate adoption review, not retroactive replay.'],'runtime_changes':[]})
print({'status':'SOURCE_CONFIRMED_FUTURE_U9_STEVEN_ACTOR_OWNER_GAP','checks':len(tests),'source_resources':len(pins)})
