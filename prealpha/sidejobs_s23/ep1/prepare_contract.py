"""Derive bounded S23 EP1 admissions from the frozen live capture and stock sources."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CAPTURE='research/sidejobs_s23/live_20261016_01/capture.json'
PIN='47084A3833CFE507D184A19CDD1276215A15F917F6B97AA4130E6A6E6919748A'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
assert sha(ROOT/CAPTURE)==PIN
capture=json.loads((ROOT/CAPTURE).read_text())
jobs={j['id']:j for j in capture['second']['jobs']}
states={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}
prefix='towercontinued\\sidejobs_s23\\ep1\\'
common={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'PTFRPA2_Finished':1,'PTFRPA2_Fault':0,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_active':0,'q307_main_game_killed':1,'q307_ep1_killed':1,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'q307_debug_reset':0,'q115_point_of_no_return':0,'q305_johnny_scene_active':0}
out=[]
def add(id,key,facts=None,ranges=None):
 j=jobs[id]
 c=dict(id=id,key=key,tag='PTFRS23_'+key,depot=prefix+key.lower()+'_boot.questphase',entry='In1',facts_equal=facts or {},fact_ranges=ranges or {},journals=[dict(path=r['path'],**{'class':r['class']},states=[states[r['state']]]) for r in j['journals']],reactivate_paths=[],native_only_guards=[],observed_facts=j['facts'],observed_journals=j['journals'],capture_sha256=PIN)
 out.append(c);return c
mq=add('mq306_dumpster','MQ306',{k:jobs['mq306_dumpster']['facts'][k] for k in ['mq306_active','mq306_started','mq306_quest_accepted','mq306_done','mq306_finished','mq306_animals_dead','mq306_fight_clean','mq306_dive','mq306_intimidate','mq306_truth','mq306_aaron_intimidate_end','mq306_aaron_path','mq306_angie_path','mq306_offer_declined','mq306_bartender_done','mq306_03_angie_turned','mq306_clinic_reached','mq306_leaving_ripper','mq306_testdef']})
mq['reactivate_paths']=[jobs[mq['id']]['root'],jobs[mq['id']]['root']+'/04a_aaron_meeting',jobs[mq['id']]['root']+'/04a_aaron_meeting/01_reply_text']
for j in mq['journals']:
 if j['path'] in mq['reactivate_paths']:j['states']=[1,4]
for path,cls,ss in [('01a_aaron_dive','gameJournalPhoneMessage',[2,3]),('02a_ch_dive_reply','gameJournalPhoneChoiceGroup',[2,3]),('03a_aaron_disgraced','gameJournalPhoneMessage',[1]),('03a_aaron_disgraced_reply','gameJournalPhoneChoiceGroup',[1]),('03b_aaron_abroad','gameJournalPhoneMessage',[1])]:
 mq['journals'].append({'path':'ep1/contacts/aaron/mq306/'+path,'class':cls,'states':ss,'observed':False})
mq['route']='Resume original Aaron dive-reply wait (root/25 node24), preserve prior objectives and choices; native SMS, Aaron reward, Fred message and original parent final reward/cleanup.'
vo=add('q304_splinter_stash','VOODOO')
vo['native_only_guards']=['Stock #q304_dvc_slider_stash_door loaded AND NOT IsOpen before issue; unloaded does not mean fresh.']
vo['route']='Original persistent root/30 node4 In1; native information-download gate retained; no free hint or synthetic journal activation.'
bill=add('wst_ep1_11_bill_meeting','BILL',{'wst_ep1_11_hotdog_finished':0,'wst_ep1_11_ncpd_start':0,'wst_ep1_11_ncpd_finished':0,'bill_default_on':0,'sts_ep1_10_debug_fact_1111':0,'ws_ep1_11_chicken_test_journal_start':0,'PTFRB0S4BILL_Enabled':0,'PTFRB0S4BILL_OwnerActive':0,'PTFRB0S4BILL_QuestOwns':0},{'sts_ep1_10_finished':{'min':1,'max':2147483647}})
bill['route']='Original world-story node35 ->11; original default-dialog parent14->5 loop. Acquire existing B0 QuestOwns lease before both; retained while native default alive, not released on quest completion.'
bill['lease_facts']={'PTFRB0S4BILL_QuestOwns':1}
hasan=add('wst_ep1_05','HASAN',{'wst_ep1_05_active':0,'wst_ep1_05_start':0,'wst_ep1_05_finished':0,'wst_ep1_05_gun_taken':0,'wst_ep1_05_gun_reveal':0,'sts_ep1_04_blueprints_hasan':0},{'hasan_default_on':{'min':1,'max':2147483647},'sts_ep1_04_blueprints_corpo':{'min':1,'max':2147483647},'sts_ep1_04_mr_hands_holo_convinced':{'min':1,'max':2147483647}})
hasan['route']='Original world-story29->5 and default-dialog12->9 loop; wst05 eligibility, delay, messages, dialogue, gun reward untouched.'
rinder=add('wst_ep1_04','RINDER',{'wst_ep1_04_active':0,'wst_ep1_04_start':0,'wst_ep1_04_finished':0,'wst_ep1_04_gun_taken':0},{'sts_ep1_03_dogtag_obtained':{'min':1,'max':2147483647}})
rinder['route']='Original world-story deletion-marker47->prerequisite46->4; native garage, code, loot and completion.'
steven=add('sts_ep1_08_steven_meeting_night_city','STEVEN',{'sts_ep1_08_biomonitor_ana':0,'steven_santos_default_on':0,'PTFRU9_sts_ep1_08_ParentEntered':0,'PTFRU9_sts_ep1_08_Started':0},{'sts_ep1_08_finished':{'min':1,'max':2147483647}})
steven['route']='Only night-city Steven invitation branch of original gig cleanup root/3; original Steven default parent19->17. U9-entered gig excluded because it owns its own follow-up.'
steven['journals'].append({'path':'ep1/contacts/steven_santos/sts_ep1_08/biomonitor_destroyed_meeting_invitation','class':'gameJournalPhoneMessage','states':[1],'observed':False})
for id,key,num,vehicle in [('mq046_cave_vehicle','MQ046','40','Vehicle.v_sport1_rayfield_caliburn_02_player'),('mq047_ad_vehicle','MQ047','44','Vehicle.v_standard25_thorton_colby_pickup_02_player')]:
 c=add(id,key,{'ma_bls_ina_se1_'+num+'_start':0,'ma_bls_ina_se1_'+num+'_finished':0})
 c['native_only_guards']=['NOR(questVehicleAvailable SpecificVehicle '+vehicle+')','Original district parent173 seven-tick startup delay retained; native gameplay progression gates retained.']
 c['vehicle_not_available']=vehicle
 c['route']='Original district parent173 -> '+('141' if num=='40' else '145')+' In1, direct native gameplay, original car reward and Johnny scenes; no legacy reset.'
data={'schema':'S23_EP1_COMPONENT_CONTRACT_1','status':'PREPARED_NOT_LIVE','common_equal':common,'capture':CAPTURE,'capture_sha256':PIN,'owners':out,'policy':'Whitelist actual Failed/Inactive at bounded native stage. All successful history protected; unsupported partial variants defer. Runtime must treat missing entries as unknown, not Inactive. Only three MQ306 entries reactivated. No fresh-history claim.'}
p=Path(__file__).with_name('contract.json')
if p.exists() and '--replace-unfrozen' not in sys.argv:raise SystemExit('Refuse overwrite existing contract')
p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'path':str(p),'sha256':sha(p),'owners':len(out)}))
