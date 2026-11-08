"""Independent G16 native/current followup and owner review; no peer verifier import."""
from pathlib import Path
import sys,copy,re,json,collections
H=Path(__file__).resolve().parent;W=H.parents[3];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource
sys.path.insert(0,str(H));from review_remaining import path
sys.path.insert(0,str(W/'prealpha/quest_restoration_qr5/groups/G17'));from deep import canon
def run():
 O=H/'G16_evidence_01';assert not O.exists();P=W/'prealpha/quest_restoration_qr5/groups/G16';R=read(P/'results.json');E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');M={};D={};pins=[];ts=[];mut=[]
 def ck(k,v,e):ts.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 ck('frozen_G16_result',sha(P/'results.json')=='9016043760B6D69822EBE2BB033BCC1F1656078A0C40AEE19C3EDAA004AA66E9',sha(P/'results.json'))
 for pf in R['source_pin_paths']:
  for p in read(pf):
   if not p.get('depot'):continue
   ck('raw_and_export_pin '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p)
   m=Resource(read(p['json'])).normalize();d=p['depot']
   if d in E['source_resources']:ck('effective_epoch_pin '+d,p['sha256']==E['source_resources'][d],p['sha256'])
   if d in M:ck('same_raw_fresh_export_semantics '+d,canon(m)==canon(M[d]),{'json':p['json'],'raw':p['binary'],'limit':'TDB exact numeric identity normalization only'})
   M[d]=m;D[d]=read(p['json']);pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 world=find('ep1_world_stories.questphase');defs=find('ep1_default_dialogs.questphase');ep=find('ep1.questphase');hasan=find('hasan_boot.questphase');bill=find('bill_boot.questphase');rinder=find('rinder_boot.questphase');hw=find('wst_ep1_05.questphase');bw=find('wst_ep1_11.questphase');rw=find('wst_ep1_04.questphase')
 for cur,og,ids in [(hasan,world,[29,5]),(hasan,defs,[12,9]),(bill,world,[35,11]),(bill,defs,[14,5]),(rinder,world,[47,46,4])]:
  for i in ids:ck('exact_native_parent_owner '+cur+str(i),n(cur,i,'root/100')==n(og,i),{'native':og,'node':i,'current':'root/100'})
 for cur,edges in [(hasan,[['0','Out','29','In'],['29','Out','5','In1'],['0','Out','12','In'],['12','Out','9','In1'],['9','Out1','12','In']]),(bill,[['0','Out','35','In'],['35','Out','11','In1'],['0','Out','14','In'],['14','Out','5','In1'],['5','Out1','14','In']]),(rinder,[['0','Out','47','In'],['47','Out','46','In'],['46','Out','4','In1']])]:ck('actual_preserved_world_default_fanout '+cur,g(cur,'root/100')['edges']==sorted(edges),edges)
 ck('native_world_and_default_ancestors_cut',e(ep,9,'CutSource',5,'CutDestination','root/10')and e(ep,9,'CutSource',4,'CutDestination','root/10')and e(ep,9,'Out',10,'In','root/10'),g(ep,'root/10')['edges'])
 for cur,needed in [(hasan,['hasan_default_on','sts_ep1_04_blueprints_corpo','sts_ep1_04_mr_hands_holo_convinced']),(bill,['sts_ep1_10_finished']),(rinder,['sts_ep1_03_dogtag_obtained'])]:
  for fact in needed:ck('genuine_native_positive_outcome '+cur+fact,any(r.get('factName')==fact and r.get('comparisonType')=='GreaterOrEqual'and r.get('value')==1 for r in n(cur,2)['reads']),fact)
  ck('claim_recheck_and_existing_owner_barrier '+cur,any(r.get('factName','').startswith('PTFRS23_')and r['factName'].endswith('_Issued')and r.get('value')==0 for r in n(cur,2)['reads'])and any(r.get('factName','').startswith('PTFRS23_')and r['factName'].endswith('_Issued')and r.get('value')==1 for r in n(cur,90)['reads']),{'entry':2,'recheck':90})
  ck('no_outer_termination_of_default_or_world_owner '+cur,not any(x['type']=='questOutputNodeDefinition'and x['payload'].get('type')=='Terminating'for x in g(cur)['nodes'].values()),'Native persistent/default loops survive separate success observation')
 delay=n(hw,47)['payload']['condition']['type'];ck('Hasan_exact_3days16hours_equals88',delay['$type']=='questGameTimeDelay_ConditionType'and delay['days']*24+delay['hours']==88 and delay['days']==3 and delay['hours']==16,delay)
 correction=P/'timer_arithmetic_correction_01.json';ck('frozen_84h_prose_explicitly_superseded',read(correction)['correct_total_game_hours']==88 and read(correction)['results_sha256']==sha(P/'results.json'),{'path':str(correction),'sha256':sha(correction),'no_runtime_change':read(correction)['runtime_changes']})
 bdelays=[{'node':i,'payload':x['payload']['condition']['type']}for i,x in g(bw)['nodes'].items()if x['payload'].get('condition',{}).get('$type')=='questTimeCondition'and x['payload']['condition']['type'].get('$type')=='questGameTimeDelay_ConditionType'];ck('Bill_actual32_game_hour_timer',any(x['payload'].get('days',0)*24+x['payload'].get('hours',0)==32 for x in bdelays),bdelays)
 for ni in [2,3]:ck('Bill_B0_preclaim_exclusion '+str(ni),all(any(r.get('factName')==f and r.get('value')==0 for r in n(bill,ni)['reads'])for f in ['PTFRB0S4BILL_Enabled','PTFRB0S4BILL_OwnerActive','PTFRB0S4BILL_QuestOwns']),ni)
 ck('Bill_QuestOwns_claim_before_native_enrollment',n(bill,10)['writes'][0]['factName']=='PTFRB0S4BILL_QuestOwns'and n(bill,10)['writes'][0]['value']==1 and path(g(bill),'4','10')and path(g(bill),'10','92')and any(r.get('factName')=='PTFRB0S4BILL_QuestOwns'and r.get('value')==1 for r in n(bill,90)['reads']),{'claim':10,'path':path(g(bill),'4','92')})
 b0='towercontinued\\b0_story_eight\\bill.questphase';ck('Bill_B0_reverse_owner_exclusion',any(r.get('factName')=='PTFRB0S4BILL_QuestOwns'and r.get('value')==0 for gp,gr in M[b0]['graphs'].items()for nn in gr['nodes'].values()for r in nn['reads']),b0)
 # Native predecessor SMS is distinct from dogtag/followup ownership.
 pred=find('sts_ep1_03_openworld.questphase');matches=[(gp,gr)for gp,gr in M[pred]['graphs'].items()if all(str(i)in gr['nodes']for i in [132,135,133,134])];gp,gr=next((gp,gr)for gp,gr in matches if any(e0[0]=='132'and e0[2]=='135'for e0 in gr['edges']))
 ck('Rinder_original_prior_SMS_suppression_and_trigger',gr['nodes']['132']['payload']['condition']['operation']=='OR'and ['132','False','135','In']in gr['edges']and gr['nodes']['135']['type']=='questPauseConditionNodeDefinition'and ['135','Out','133','In']in gr['edges']and ['133','Out','134','Active']in gr['edges'],{'native':pred,'graph':gp,'nodes':{i:gr['nodes'][i]['payload']for i in ['132','135','133','134']},'meaning':'No-garage OR called-Regina true suppresses this send; false waits outside135 then adds Rinder contact133 and sends code134. The trigger is not a replay condition.'})
 requests=[]
 for d in [hw,bw,rw,find('sts_04_hasan_default.questphase'),find('sts_04_hasan_default.scene'),find('bill_default.questphase'),find('sts_10_bill_default.scene')]:
  for gp,gr in M[d]['graphs'].items():
   for i,n0 in gr['nodes'].items():
    for w in n0['writes']:
     if w['value']==1 and (re.match(r'^(holo|audio)_.*_(start|end)_activate$',w['factName'])or w['factName'].startswith('new_')and any(a in w['factName']for a in ['call','brief'])):requests.append({'depot':d,'graph':gp,'node':i,'fact':w})
 ck('bounded_own_generic_and_custom_call_inventory',not requests,{'own_request_sites':requests,'limit':'SMS/visited/journal routes are preserved; predecessor generic calls are outside this own-followup conclusion.'})
 raw=copy.deepcopy(D[hw]);changed=0
 for x in walk(raw):
  if x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==3 and x.get('hours')==16:x['hours']=12;changed+=1
 mm=Resource(raw).normalize();wrong=mm['graphs']['root']['nodes']['47']['payload']['condition']['type'];ck('actual_raw_84h_timer_fault_detected',changed==1 and wrong['days']*24+wrong['hours']!=88,wrong);mut.append({'name':'Hasan_native88h_to84h','detected':True});write(O/'Hasan_84h_fault.questphase.json',raw)
 statuses=collections.Counter()
 for row in R['quest_results']:
  ck('frozen_10_contracts '+row['quest_id'],sha(row['contracts'])==row['contracts_sha256'],row['contracts']);statuses.update(c['status']for c in read(row['contracts'])['contracts'].values())
 ck('honest_contract_counts',dict(statuses)==R['contract_status_counts']and sum(statuses.values())==30,dict(statuses))
 write(O/'tests.json',ts);write(O/'source_pins.json',pins);write(O/'mutations.json',mut);r={'status':'PASS_INDEPENDENT_SOURCE_REVIEW_WITH_LIMITS_AND_DOCUMENTED_TIMER_SUPERSESSION','group':'G16','quest_ids':R['quest_ids'],'checks':len(ts),'raw_mutations':1,'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'reviewed_results_sha256':sha(P/'results.json'),'findings':['Current S23 world-body and Hasan/Bill separate default owner copied native parent nodes and fanout/loops exactly; no Steven-like omitted root support inferred.','Actual positive native predecessor outcomes, Issued claim/rechecks and Bill B0 exclusion in both directions verified; QuestOwns is claimed before enrollment.','Hasan exact native timer3days16hours=88game hours; original84h report/check-name shorthand is explicitly superseded by frozen correction. Bill native32game-hour delay retained.','Native Rinder predecessor OR132.False→outside-trigger135→contact133→SMS134 is distinct from followup dogtag receipt. No-garage/Regina outcomes suppress this send;135 is not a replay condition. Current followup does not resend the code.','Own complete named request scan finds no generic/new_* call requests in bounded followup/default sources; this is not all predecessor phone ownership proof.'],'limits':['Exact saved owners, timed wait history and in-game SMS/default/actor acquisition remain conditional.','Original quantity0 LootTables/economic children, optional prior code SMS, vehicle-disable cleanup and opaque placement are bounded engine/source limits, not mod repair evidence.','Fresh actual exports are compared by raw hash plus exact numeric TDB semantic identity only; unsupported native ancestor decode errors are retained, not called a full parity PASS.'],'runtime_changes':[]};write(H/'G16.json',r);print(json.dumps({'checks':len(ts),'review_sha256':sha(H/'G16.json')},ensure_ascii=True))
if __name__=='__main__':run()
