"""Independent Moving Heat source/PF/owner census and exact proposal review."""
from pathlib import Path
import sys,json,copy,gzip,collections
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent;sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,fnv
from model import Resource
sys.path.insert(0,str(W/'prealpha/quest_restoration_qr5/reviews/worker_b'));from review_remaining import path
sys.path.insert(0,str(W/'prealpha/quest_restoration_qr5/groups/G17'));from verify import ev
def guard_eval(c,f,j,external):
 if c['$type']=='questLogicalCondition':
  a=[guard_eval(x,f,j,external)for x in c['conditions']];return all(a)if c['operation']=='AND'else any(a)if c['operation']=='OR'else not any(a)if c['operation']=='NOR'else False
 if c['$type']in ['questFactsDBCondition','questJournalCondition']:return guard_eval(c['type'],f,j,external)
 if c['$type']in ['questVarComparison_ConditionType','questJournalEntryState_ConditionType']:return ev(c,f,j)
 return external[json.dumps(c,sort_keys=True)]
def external_predicates(c):
 if c['$type']=='questLogicalCondition':return [p for x in c['conditions']for p in external_predicates(x)]
 if c['$type']in ['questFactsDBCondition','questJournalCondition']:return external_predicates(c['type'])
 return []if c['$type']in ['questVarComparison_ConditionType','questJournalEntryState_ConditionType']else[c]
def run():
 O=H/'verification_01';assert not O.exists();P=W/'prealpha/quest_restoration_qr5/groups/G18/moving_heat_prefab_03';ts=[];pins=[];M={};D={}
 def ck(k,v,e):ts.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 ep=P/'evidence.json';pp=P/'proposal.json';ck('exact_frozen_defect',sha(ep)=='DA8DFDE166EF0E1B8A769D2D1CCD7E77E8567ED85CCE25E73324085EE92808BC',str(ep));ck('exact_frozen_proposal',sha(pp)=='96611DFB60C246C52DDAFA18144CCE142373EA9403657ABA8A285340C5738036',str(pp));Q=read(pp)
 E=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json')
 for p in read(P/'source_pins.json'):
  d=p['depot'];ck('actual_raw_source_export_pin '+d,sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p)
  if d in E['source_resources']:ck('frozen_current_payload '+d,p['raw_sha256']==E['source_resources'][d],p['raw_sha256'])
  D[d]=read(p['json']);M[d]=Resource(D[d]).normalize();pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,i,p='root'):return g(d,p)['nodes'][str(i)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 boot=find('moving_heat_boot.questphase');resume=find('moving_heat_resume.questphase');native=find('q304_car_retrieval.questphase');fresh=find('q304_fresh_boot.questphase');ep1=find('ep1.questphase');persistent=find('ep1_persistent_content.questphase');additional=find('ep1_additional_game_elements.questphase');pf='#q304_pr_car_retrieval'
 ck('native_dedicated_root_lease',M[native]['root_prefabs']==[pf]and not M[native]['errors'],M[native]['metadata']['phasePrefabs'])
 for d in [boot,resume]:ck('current_S22_entire_missing_matching_support '+d,pf not in M[d]['root_prefabs']and not any(pf in nn['prefabs']for gr in M[d]['graphs'].values()for nn in gr['nodes'].values()),{'root_prefabs':M[d]['root_prefabs'],'graphs':list(M[d]['graphs'])})
 ck('S22_exact_supported_future_entry',e(boot,9,'True',10,'In1')and resume in n(boot,10)['refs']and e(boot,10,'Out1',11,'In'),'Actual root9 condition→external native resume10→private Finished11')
 ck('S22_claim_precedes_postcheck_and_body',path(g(boot),'3','4')and path(g(boot),'4','9')and n(boot,4)['writes'][0]['factName']=='PTFRS22_Q304_Issued'and any(r.get('factName')=='PTFRS22_Q304_Issued'and r.get('value')==1 for r in n(boot,9)['reads']),{'claim_to_postcheck':path(g(boot),'4','9')})
 for f in ['q304_car_retrieval_accepted','q304_car_retrieval_active','q304_car_retrieval_started']:ck('actual_native_accepted_stage_'+f,any(r.get('factName')==f and r.get('value')==1 for r in n(boot,2)['reads']),f)
 ck('native_current_source_nodes_preserved',all(n(resume,i)['payload']==n(native,i)['payload']for i in g(resume)['nodes']if i!='0'),{'native':native,'resume':resume,'scope':'All retained original top-level native node payloads, not initializer presence alone'})
 for gp,gr in M[resume]['graphs'].items():
  if gp!='root':ck('complete_native_resume_descendant '+gp,gr==g(native,gp),gp)
 ck('original_owner_exact_ancestry',additional in n(ep1,4,'root/10')['refs']and persistent in n(additional,2)['refs']and native in n(persistent,4,'root/30/6')['refs']and e(ep1,9,'CutSource',4,'CutDestination','root/10')and e(ep1,9,'Out',10,'In','root/10'),'EP1root/10/4 additional→persistent2→root30/6/4carbody; exact Tower cut9, not a killed receipt alone')
 ck('S24_separate_native_body_support',any(native in nn['refs']for gr in M[fresh]['graphs'].values()for nn in gr['nodes'].values()),fresh)
 ck('proposal_preserves_old_external_resource_and_fresh_owner',set(Q['preserve_resources'])=={resume,fresh}and Q['resource']==boot and Q['before_sha256']==next(p['raw_sha256']for p in pins if p['depot']==boot),Q['preserve_resources'])
 expected_atom={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS24_Q304_FRESH_Issued','value':0}}
 ck('proposal_only_extra_fresh_owner_zero_atom',Q['guard_updates']['node_ids']==[2,3,9]and Q['guard_updates']['append_exact_AND_atom']==expected_atom,Q['guard_updates'])
 ck('proposal_exact_future_edge_and_completion',Q['remove_edges']==[['9','True','10','In1']]and Q['add_edges']==[['9','True','1200','In1'],['1200','Out1','11','In']],{'remove':Q['remove_edges'],'add':Q['add_edges'],'old10_completion_retained':e(boot,10,'Out1',11,'In')})
 wrapper=Q['new_wrapper'];ck('new_wrapper_unused_local_ID',str(wrapper['outer_id'])not in g(boot)['nodes']and wrapper['outer_id']==1200,wrapper['outer_id'])
 ck('wrapper_exact_native_prefab_entry',wrapper['phaseInstancePrefabs']==M[native]['metadata']['phasePrefabs']and wrapper['phaseResource']['DepotPath']['$value']=='0'and wrapper['saveLock']==0,wrapper)
 ck('wrapper_child_exact_old10_payload',wrapper['inner_nodes']['10']==n(boot,10)['payload'],wrapper['inner_nodes']['10'])
 ck('wrapper_single_lease_lifetime_entry_and_exit',set(wrapper['inner_nodes'])=={'0','10','1'}and wrapper['inner_edges']==[['0','Out','10','In1'],['10','Out1','1','In']]and wrapper['inner_nodes']['1']['type']=='Terminating'and wrapper['inner_nodes']['1']['socketName']['$value']=='Out1',wrapper['inner_edges'])
 ck('native_resume_output_contract',any(nn['type']=='questOutputNodeDefinition'and nn['payload'].get('socketName',{}).get('$value')=='Out1'for nn in g(resume)['nodes'].values()),'Hold original dedicated car PIP for exact accepted resume resource lifetime; wrapper ends only after its Out1')
 # Evaluate actual guards before/after the appended atom, not an invented engine status model.
 fixtures=[]
 for ni in [2,3,9]:
  original=n(boot,ni)['payload']['condition'];fs={r['factName']:r['value']for r in n(boot,ni)['reads']if r.get('factName')and r.get('comparisonType')in ['Equal','GreaterOrEqual']};js={r['path']['realPath']:r['state']for r in n(boot,ni)['reads']if r.get('$type')=='questJournalEntryState_ConditionType'};opaque=external_predicates(original);external={json.dumps(c,sort_keys=True):True for c in opaque};fixture={'facts':fs,'journals':js,'external_predicates_required_true':opaque,'limit':'Explicit symbolic original world/trigger fixture; no claim actual in-game trigger state is true.'};ck('actual_old_supported_guard_fixture_'+str(ni),guard_eval(original,fs,js,external),fixture);modified=copy.deepcopy(original);assert modified['operation']=='AND';modified['conditions'].append(expected_atom)
  ck('extra_atom_preserves_supported_future_'+str(ni),guard_eval(modified,fs|{'PTFRS24_Q304_FRESH_Issued':0},js,external),fixture);ck('extra_atom_blocks_known_S24_owner_'+str(ni),not guard_eval(modified,fs|{'PTFRS24_Q304_FRESH_Issued':1},js,external),ni);fixtures.append({'guard':ni,**fixture})
 # Independent complete pinned graph-source universe census, including numeric spelling.
 mi=W/'diagnostics/vanilla_parity_20261029_01/analysis_02/model_inventory.json';inventory=read(mi);aliases={pf,fnv(pf)};leases=[];parents=[]
 for d,row in inventory.items():
  ck0=sha(row['normalized_model'])==row['normalized_sha256'];assert ck0,d
  mm=json.loads(gzip.decompress(Path(row['normalized_model']).read_bytes()))
  if aliases&set(mm.get('root_prefabs',[])):leases.append({'depot':d,'scope':'resource_root','prefabs':mm['root_prefabs']})
  for gp,gr in mm['graphs'].items():
   for ni,nn in gr['nodes'].items():
    if aliases&set(nn.get('prefabs',[])):leases.append({'depot':d,'graph':gp,'node':ni,'scope':'phase_instance','prefabs':nn['prefabs']})
    if native in nn.get('refs',[]):parents.append({'depot':d,'graph':gp,'node':ni,'target':native})
 ck('full_graph_cache_lease_census',leases and {x['depot']for x in leases}=={native},leases)
 ck('known_S24_is_separate_borrowed_owner_not_S22',any(x['depot']==fresh for x in parents)and not any(x['depot']in [boot,resume]for x in parents),parents)
 # Exact native PF loss is an actual raw mutation, not a fixture-only arbitrary flag.
 raw=copy.deepcopy(D[native]);raw['Data']['RootChunk']['phasePrefabs']=[];mut=Resource(raw).normalize();ck('actual_raw_native_root_PF_loss_detected',mut['root_prefabs']!=M[native]['root_prefabs'],{'native':M[native]['root_prefabs'],'mutated':mut['root_prefabs']});write(O/'missing_native_car_PF.questphase.json',raw)
 write(O/'tests.json',ts);write(O/'source_pins.json',pins);write(O/'guard_fixtures.json',fixtures);write(O/'census.json',{'model_inventory':str(mi),'model_inventory_sha256':sha(mi),'models':len(inventory),'all_gzip_hashes_checked':True,'prefab_aliases':sorted(aliases),'leases':leases,'native_body_reverse_refs':parents,'limit':'Complete pinned graph universe, not arbitrary world/runtime/saved owner proof.'})
 report={'status':'APPROVED_EXACT_SOURCE_PROPOSAL_WITH_PRECISE_SAVE_BOUNDARY','quest_id':'q304_car_retrieval','defect':str(ep),'defect_sha256':sha(ep),'proposal':str(pp),'proposal_sha256':sha(pp),'checks':len(ts),'raw_mutations':1,'raw_resources':len(pins),'models_censused':len(inventory),'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'findings':['Native car body alone owns dedicated root #q304_pr_car_retrieval; current S22 accepted resume has no matching root/recursive lease, original additional/persistent caller is explicitly cut by Tower, and separate S24 full owner cannot supply that obligation for S22.','Exact retained native resume nodes/descendants verified; proposal adds only a future wrapper with the identical native PF entry, exact old external resume10 payload, input→child→Terminating output and old11 callback. No full original/main/default rehost.','Old root10 payload/empty inline graph, external path, already executing descendants and original10.Out1→11 must remain exact. Append only explicit S24_FRESH_Issued0 to existing2/3/9 AND guards; actual supported positive fixtures remain supported, known S24 owners reject.','No new registration/depot, native fact/journal/reward/counter reset, fake acknowledgement or game/save write approved. Serialized candidate and final package must receive separate preservation/readback gates.'],'save_boundary_clarification':'Source strictly guarantees already-executing root10/descendants are unchanged. Claim4 precedes9. A previously claimed save still pending a future9.True before child10 begins may use the new wrapper after updating; broad prose saying every already-Issued owner is unchanged is too strong. This is a supported before-child event, not retroactive attachment to an executing child. No engine save scheduling guarantee is asserted.','limits':['Exact native PF reference/scoping is reviewed; placement, streaming/reference counting, actor/community acquisition and cross-version save scheduling remain opaque/live-only. Existing pre-wrapper guards require IsOutside on main_trigger and entire_garage. Their availability before PIP acquisition is unproved; this approves body-lifetime support for an actual future9.True, not a fix for every entry/guard stall.','Unknown external providers or saved owners are not ruled out solely by journal facts; captured source census and explicit known S24 fence are bounded.','This approves only exact declarative proposal, not an implementation, packaged build, installed result or gameplay repair.'],'runtime_changes':[]}
 write(H/'review.json',report);print(json.dumps({'checks':len(ts),'review_sha256':sha(H/'review.json')},ensure_ascii=True))
if __name__=='__main__':run()
