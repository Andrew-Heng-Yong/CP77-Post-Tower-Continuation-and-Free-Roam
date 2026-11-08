"""Source-only Moving Heat future-resume prefab proposal. Never serializes a binary."""
from lib import *
import argparse,copy,zlib
H=Path(__file__).parent
N=r'ep1\quest\main_quests\q304\phases\q304_car_retrieval.questphase';B=r'towercontinued\sidejobs_s22\moving_heat_boot.questphase';R=r'towercontinued\sidejobs_s22\moving_heat_resume.questphase';P=r'ep1\quest\ep1_persistent_content.questphase';A=r'ep1\quest\ep1_additional_game_elements.questphase';EP=r'ep1\quest\ep1.questphase';F=r'towercontinued\sidejobs_s24\ep1\q304_fresh_boot.questphase'
def run(O):
 assert not O.exists();O.mkdir(parents=True);(O/'mutations').mkdir();T=[];M={};D={};pins=read(H/'raw_exports_01/manifest.json')
 def ck(k,v,e):
  T.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:save(O/'failed_tests.json',T);raise AssertionError(k)
 def n(d,i,g='root'):return M[d]['graphs'][g]['nodes'][str(i)]
 def e(d,a,s,b,t,g='root'):return[str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 for row in pins:
  d=row['depot'];ck('actual raw/readback pins '+d,sha(row['raw'])==row['raw_sha256']and sha(row['json'])==row['json_sha256'],row);D[d]=read(row['json']);M[d]=Resource(D[d]).normalize();ck('fresh decode '+d,not M[d]['errors'],M[d]['errors'])
 epoch0=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');epoch5=read(W/'prealpha/quest_restoration_qr5/source_epoch_05.json')
 for d in[B,R,F]:ck('frozen/current effective source '+d,sha(next(x['raw']for x in pins if x['depot']==d))==epoch0['source_resources'][d]==epoch5['source_resources'][d],epoch0['source_resources'][d])
 ck('original sole dedicated root prefab',M[N]['root_prefabs']==['#q304_pr_car_retrieval'],M[N]['root_prefabs'])
 ck('current resume and boot have no root or nested lease',not M[R]['root_prefabs']and not M[B]['root_prefabs']and not any(x['prefabs']for d in[B,R]for g in M[d]['graphs'].values()for x in g['nodes'].values()),'Scope is accepted-stage S22; fresh S24 still calls original whole body')
 for d in [x for x in M if 'car_retrieval'in x and x!=N]:ck('native selected children do not own whole support '+d,not M[d]['root_prefabs']and not any(x['prefabs']for g in M[d]['graphs'].values()for x in g['nodes'].values()),'No child lease substitutes original resource root')
 ck('original persistent caller owns entire car body',N in n(P,4,'root/30/6')['refs']and e(P,8,'Out1',4,'In1','root/30/6'),n(P,4,'root/30/6')['payload'])
 ck('actual retired original ancestry',P in n(A,2)['refs']and A in n(EP,4,'root/10')['refs']and e(EP,9,'CutSource',4,'CutDestination','root/10')and e(EP,9,'Out',10,'In','root/10'),'Genuine Tower cuts additional4; killed fact follows cut, not a shortcut')
 census=read(H/'ownership_census_01/census.json');ck('independent all-model prefab census pin',sha(H/'ownership_census_01/census.json')=='9FD10E173F8A2E72AF93A44C9D2841FD3099976366109CDE95F414DB949A2380'and census['models']==5136 and census['all_actual_gzip_hashes_checked'],str(H/'ownership_census_01/census.json'))
 ck('only native whole body provides dedicated prefab',{x['depot']for x in census['prefab_owners']if x['prefab']=='#q304_pr_car_retrieval'}=={N},census['prefab_owners'])
 ck('only original and S24 call native whole body',{x['depot']for x in census['reverse_refs']if x['target']==N}=={P,F},'S24 caller is an independently admitted fresh controller, not guaranteed support for S22')
 # Exact accepted-stage extraction: preserve every selected original body node and nested edge.
 nr=M[N]['graphs']['root'];rr=M[R]['graphs']['root'];ck('resume removes exactly native fresh-message prefix',set(nr['nodes'])-set(rr['nodes'])=={'2','252','253'}and not(set(rr['nodes'])-set(nr['nodes'])),{'original':len(nr['nodes']),'resume':len(rr['nodes'])})
 for i,nd in rr['nodes'].items():ck('unchanged accepted native root node '+i,nd==nr['nodes'][i],nd['payload_sha256'])
 for gp,g in M[R]['graphs'].items():
  if gp!='root':ck('unchanged nested native graph '+gp,g==M[N]['graphs'][gp],gp)
 ck('boot actual future resume edge',e(B,9,'True',10,'In1')and R in n(B,10)['refs']and e(B,10,'Out1',11,'In'),'Saved external body owner10 and output receipt remain unchanged')
 # Existing admission lets a known S24 fresh receipt through; new support must not borrow that owner's lease.
 guard=n(B,2)['payload']['condition'];facts={};journals={}
 for x in walk(guard):
  if x.get('$type')=='questVarComparison_ConditionType':facts.setdefault(x['factName'],x['value'])
  if x.get('$type')=='questJournalEntryState_ConditionType':journals.setdefault(x['path']['realPath'],x['state'])
 trigger_fixture={'#q304_tr_car_retrieval_main_trigger':True,'#q304_tr_car_retrieval_entire_garage':True}
 def ev(c,f,j):
  if c['$type']=='questTriggerCondition':return trigger_fixture.get(val(c['triggerAreaRef']))if c['type']=='IsOutside'else None
  if c['$type']=='questLogicalCondition':
   values=[ev(z,f,j)for z in c['conditions']]
   if any(z is None for z in values):return None
   return all(values)if c['operation']=='AND'else any(values)if c['operation']=='OR'else not any(values)if c['operation']=='NOR'else None
  return evaluate(c,f,j)
 ck('bounded original supported-stage predicate fixture',ev(guard,facts,journals)is True,{'facts':facts,'journals':journals,'explicit_fixture_outside_native_triggers':trigger_fixture})
 ck('native S24 positive ownership is not an existing fence',not any(x.get('factName')=='PTFRS24_Q304_FRESH_Issued'for x in walk(guard)),'This alone is not a proven runtime duplicate-owner interleaving; native JournalManager propagation remains separate')
 atom={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS24_Q304_FRESH_Issued','value':0}}
 pg=copy.deepcopy(guard);assert pg['$type']=='questLogicalCondition'and pg['operation']=='AND';pg['conditions'].append(atom);f0={**facts,'PTFRS24_Q304_FRESH_Issued':0};f1={**facts,'PTFRS24_Q304_FRESH_Issued':1}
 ck('future old-stage0 retained known fresh-owner1 refused',ev(guard,f1,journals)is True and ev(pg,f0,journals)is True and ev(pg,f1,journals)is False,'Explicit scalar0 means absent engine key0; no manufactured old history; both original IsOutside fixtures remain required')
 ck('proposed local wrapper ID unused','1200'not in M[B]['graphs']['root']['nodes'],'No new external resource/ArchiveXL registration')
 native_prefabs=copy.deepcopy(D[N]['Data']['RootChunk']['phasePrefabs']);ck('exact complete native prefab entry',len(native_prefabs)==1 and native_prefabs[0]['prefabNodeRef']['$value']=='#q304_pr_car_retrieval',native_prefabs)
 # Source-only exact proposal, not a generated runtime resource.
 wrapper={'outer_id':1200,'type':'questPhaseNodeDefinition','phaseInstancePrefabs':native_prefabs,'phaseResource':{'DepotPath':{'$type':'ResourcePath','$storage':'uint64','$value':'0'},'Flags':'Soft'},'saveLock':n(B,10)['payload'].get('saveLock',0),'inner_nodes':{'0':copy.deepcopy(n(B,0)['payload']),'10':copy.deepcopy(n(B,10)['payload']),'1':copy.deepcopy(n(N,1)['payload'])},'inner_edges':[['0','Out','10','In1'],['10','Out1','1','In']]}
 ck('wrapper preserves native terminal handoff',wrapper['inner_nodes']['1']['type']=='Terminating'and val(wrapper['inner_nodes']['1']['socketName'])=='Out1'and wrapper['inner_nodes']['10']==n(B,10)['payload'],'Whole native support held for existing accepted body lifetime; only new wrapper output→existing11')
 proposal={'id':'QR5-G18-Q304-S22-MISSING-CAR-PREFAB','status':'SOURCE_ONLY_PROPOSAL_REQUIRES_INDEPENDENT_REVIEW','resource':B,'before_sha256':epoch0['source_resources'][B],'native_donor':N,'native_donor_sha256':next(x['raw_sha256']for x in pins if x['depot']==N),'preserve_resources':[R,F],'guard_updates':{'node_ids':[2,3,9],'append_exact_AND_atom':atom,'scope':'Only future unentered S22 initial guard/rechecks. Existing already-executing root10 saved owner payload/edges remain unchanged.'},'remove_edges':[['9','True','10','In1']],'add_edges':[['9','True','1200','In1'],['1200','Out1','11','In']],'new_wrapper':wrapper,'preserve_old_nodes':'All existing node payloads exact except appended condition atom2/3/9; root10/external resource path and root10.Out1→11 survive for old executing saved descendants.','future_only':'No onattach recovery/new root registration/phase-resource rename. The new PIP wrapper only starts on future9.True; old saved phase10 does not gain a root prefab property. No counter/fact/journal/reward reset or original mission replay.','scope_rationale':'Exact original dedicated car-retrieval root prefab held around the exact accepted native body, restoring the original resource-lifetime support obligation; do not rehost full q304/main/default parents.','conditional_limits':['Opaque world placement and actual reference-count/streaming/reload require live fixtures.','S24 private owner fence prevents borrowing/duplicating known fresh restoration; this does not assert all old save owners are retired from journal state alone.','Already-issued/active old S22 owners remain unchanged and are not retroactively repaired; explicit future event only.'],'evidence':str(O/'evidence.json')}
 save(O/'proposal.json',proposal)
 raw=copy.deepcopy(D[N]);raw['Data']['RootChunk']['phasePrefabs']=[];mm=Resource(raw).normalize();ck('actual native root-prefab deletion mutation detected',M[N]['root_prefabs']==['#q304_pr_car_retrieval']and not mm['root_prefabs'],'Representative PH3 support failure reproduced in actual native serialized-source JSON');save(O/'mutations/native_missing_root_prefab.json',raw)
 ck('proposal does not touch external native/old resume payloads',wrapper['inner_nodes']['10']['phaseResource']==n(B,10)['payload']['phaseResource']and proposal['preserve_resources']==[R,F],'One existing private boot resource; no REDscript or external native-resource edit required')
 save(O/'tests.json',{'count':len(T),'checks':T,'mutations':[{'name':'native_missing_root_prefab','path':str(O/'mutations/native_missing_root_prefab.json'),'detected':True}]});save(O/'source_pins.json',pins);save(O/'models.json',M)
 evidence={'id':proposal['id'],'status':'SOURCE_CONFIRMED_MISSING_FUTURE_ACCEPTED_RESUME_SUPPORT_LEASE_PROPOSAL_PENDING_REVIEW','quest_id':'q304_car_retrieval','checks':len(T),'actual_raw_mutations':1,'raw_resources':len(pins),'source_epoch':'QR5epoch00; these resources equal canonical05','native_expectation':'Original complete car body holds #q304_pr_car_retrieval for body lifetime. Current S22 copied accepted body retains exact native handlers but no root/nested matching provider; original caller cut by genuine Tower, S24 fresh owner is separate.','current_fault':'Supported old accepted-stage S22 bootstrap invokes copied body without its original dedicated prefab lease. Exact world placement/gameplay symptom not claimed.','affected_contracts':['ownership','presentation','shared_dependencies'],'source_census':str(H/'ownership_census_01/census.json'),'proposal':str(O/'proposal.json'),'proposal_sha256':sha(O/'proposal.json'),'test_path':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'runtime_changes':[],'limits':proposal['conditional_limits']};save(O/'evidence.json',evidence);print(json.dumps({'checks':len(T),'evidence_sha256':sha(O/'evidence.json'),'proposal_sha256':sha(O/'proposal.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())
