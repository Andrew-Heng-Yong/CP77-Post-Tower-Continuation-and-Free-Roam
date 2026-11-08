"""Source-level MQ060 admission conflict witness; never edits runtime resources."""
from prepare import *
from inspect_sources import walk,val
import copy,itertools,collections
H=Path(__file__).parent;O=H/'nitro_admission_01';assert not O.exists();O.mkdir()
ex=read(H/'raw_exports_01/manifest.json')+read(H/'standalone_exports_01/manifest.json')+read(H/'additional_exports_01/manifest.json')
M={r['depot']:Resource(read(r['json'])).normalize()for r in ex if r['status']=='EXPORTED'}
PIN={r['depot']:r for r in ex};T=[]
def ck(name,b,e):
 T.append({'name':name,'pass':bool(b),'evidence':e});assert b,name
N=r'base\quest\bugfixing\quest_bugfixing.questphase';D=r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase';S=r'base\quest\minor_quests\mq060\mq060.quest'
g=M[N]['graphs']['root/3'];c=M[D]['graphs']['root'];s=M[S]['graphs']['root']
native_vehicles=g['nodes']['93']['payload']['condition'];purchase=g['nodes']['104']['payload']['condition'];current_vehicles=[c['nodes'][str(i)]['payload']['condition']for i in range(8,12)]
def ev(x,vehicles,count):
 t=x['$type']
 if t=='questLogicalCondition':
  a=[ev(v,vehicles,count)for v in x['conditions']];return all(a)if x['operation']=='AND'else any(a)if x['operation']=='OR'else not any(a)
 if t in ['questVehicleCondition','questFactsDBCondition']:return ev(x['type'],vehicles,count)
 if t=='questVehicleAvailable_ConditionType':return x['vehicleName']in vehicles
 if t=='questVarComparison_ConditionType':
  assert x['factName']=='carbought_counter';return count>=x['value']if x['comparisonType']=='GreaterOrEqual'else None
 raise ValueError(t)
for r in ex:ck('pinned raw and fresh JSON '+r['depot'],sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r['raw_sha256'])
for e in [('88','Out','93','In'),('88','Out','104','In'),('93','Out','106','In1'),('104','Out','106','In2'),('106','Out1','89','Start')]:ck('executing global gate '+str(e),list(e)in g['edges'],e)
ck('global two-input AND',g['nodes']['106']['type']=='questLogicalAndNodeDefinition'and g['nodes']['106']['payload']['inputSocketCount']==2,g['nodes']['106'])
ck('native purchase exact >=3',purchase['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'carbought_counter','value':3},purchase)
ck('current missing purchase atom',not any(x.get('factName')=='carbought_counter'for x in walk(M[D])),D)
ck('standalone authored four vehicle XOR selected by S29',s['nodes']['12']['type']=='questLogicalXorNodeDefinition'and all(c['nodes'][str(i)]==s['nodes'][str(i)]for i in range(8,13)),PIN[S])
ck('global vehicle OR has exactly3',native_vehicles['operation']=='OR'and len(native_vehicles['conditions'])==3,native_vehicles)
ck('current adds Tyger alternative',any(x['type']['vehicleName']=='Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player'for x in current_vehicles)and not any(x.get('vehicleName')=='Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player'for x in walk(native_vehicles)),current_vehicles)
plan=W/'prealpha/sidejobs_s29/plan_01.py';review=W/'research/sidejobs_s29/contracts_review_01.json';rr=next(x for x in read(review)['jobs']if x['id']=='mq060_nitro');ck('selection rationale exactly standalone parent',rr['parent']['depot']==S,rr['parent'])
# Complete captured-model reverse reference census (not every possible engine startup mechanism).
rev=[];census=[]
for d,r in MI.items():
 p=Path(r['normalized_model']);m=json.loads(gzip.decompress(p.read_bytes()));census.append({'depot':d,'model':str(p),'sha256':sha(p)})
 for gp,gg in m.get('graphs',{}).items():
  for i,n in gg['nodes'].items():
   if S in n.get('refs',[]):rev.append({'depot':d,'graph':gp,'node':i,'refs':n['refs']})
ck('no standalone parent reference among captured5136 models',not rev,{'models':len(census),'matches':rev,'limit':'Does not prove no native engine quest registry can independently start a .quest root.'})
vehicles=sorted({x['type']['vehicleName']for x in current_vehicles});fixtures=[]
for bits in itertools.product([False,True],repeat=4):
 v={name for name,b in zip(vehicles,bits)if b}
 for count in range(5):
  native=ev(native_vehicles,v,count)and ev(purchase,v,count);current=any(ev(x,v,count)for x in current_vehicles);proposed=current and native
  fixtures.append({'vehicles':sorted(v),'carbought_counter':count,'global_native':native,'current_standalone_adapter':current,'proposed_conservative_intersection':proposed})
ck('positive witness current admits earned vehicle with only0purchases',any(f['carbought_counter']==0 and len(f['vehicles'])==1 and f['global_native']is False and f['current_standalone_adapter']is True for f in fixtures),'All other Tower/history/permit predicates assumed satisfied; witness is gate discrepancy, not observed gameplay.')
ck('conservative proposal matches global gate across80boundedfixtures',all(f['global_native']==f['proposed_conservative_intersection']for f in fixtures),len(fixtures))
# Actual source-leaf mutation controls, independent expected table is the pinned original global route.
mutations=[]
for label,mut in [('remove_purchase_gate',copy.deepcopy(purchase)),('weaken_purchase_threshold',copy.deepcopy(purchase))]:
 mut['type']['value']=0 if label=='weaken_purchase_threshold'else-1
 failures=sum((ev(native_vehicles,set(f['vehicles']),f['carbought_counter'])and ev(mut,set(f['vehicles']),f['carbought_counter']))!=f['global_native']for f in fixtures)
 ck('detect altered actual native condition '+label,failures>0,failures);save(O/(label+'.json'),mut);mutations.append({'name':label,'failing_fixtures':failures,'source':'Native104 actual condition; raw condition-document mutant, no binary/engine mutant'})
root=r'base\quest\cyberpunk2077.questphase';bg=r'base\quest\bugfixing.questphase';rg=M[root]['graphs']['root'];bn=M[bg]['graphs']['root']
ck('native Tower terminal107 is terminating',rg['nodes']['107']['payload']['type']=='Terminating',rg['nodes']['107']['payload'])
for e in [('106','Out','109','In'),('109','Out','107','In')]:ck('genuine Tower retirement '+str(e),list(e)in rg['edges'],e)
ck('native bugfixing enclosing reference',bg in M[root]['graphs']['root/82']['nodes']['4']['refs'],M[root]['graphs']['root/82']['nodes']['4'])
ck('native quest_bugfixing reference',N in bn['nodes']['9']['refs'],bn['nodes']['9'])
proof={'id':'QR6-MQ060-ENTRY-PARENT-CONFLICT','status':'SOURCE_CONFIRMED_DIVERGENCE_BETWEEN_EXECUTING_GLOBAL_GATE_AND_STANDALONE_AUTHORED_PARENT; INDEPENDENT_ADJUDICATION_REQUIRED','quest_id':'mq060_nitro','depot':D,'baseline_sha256':PIN[D]['raw_sha256'],'native_route':{'depot':N,'graph':'root/3','nodes':[88,93,104,106,89],'vehicle_OR':native_vehicles,'purchase_gate':purchase,'edges':[e for e in g['edges']if e[0]in['88','93','104','106']and e[2]in['93','104','106','89']]},'current_route':{'depot':D,'graph':'root','nodes':[65005,8,9,10,11,12,65006,4],'vehicle_alternatives':current_vehicles,'carbought_counter_gate':False},'standalone_parent':{'source':PIN[S],'S29_plan':str(plan),'S29_plan_sha256':sha(plan),'selection':rr['parent'],'reverse_references':rev,'reverse_census_count':len(census)},'native_retirement':'Exact genuine Tower106→109→Terminating107 encloses root82/4→bugfixing9→quest_bugfixing/root3. Source structural retirement only, not saved-owner liveness.','candidate_proposal':{'scope':'Only future admission in the single existing entry resource; retain node IDs, existing vehicle nodes/XOR and already executing descendants','guards':[65003,65004],'append_conditions':[native_vehicles,purchase],'effect':'Conservative intersection retains existing standalone selector and additionally requires exact executing-global native vehicle OR plus purchase>=3. No facts written, timers reset, rewards or already-issued bodies changed.','pending':'Independent judgment of source authority and old pending admission boundary. No runtime edit by investigator.'},'fixture_count':len(fixtures),'mutations':mutations,'tests':len(T),'source_pins':ex,'runtime_changes':[],'limits':['Standalone .quest is native authored evidence, but captured reverse-reference census does not prove every native engine startup mechanism. Need independent review before choosing repair policy.','Current Permit and history unrelated atoms are assumed satisfied in bounded witness; no save/game executed.','Already issued owner paths remain unchanged by proposed future-guard append; old pending XOR may still reflect prior admission.']}
save(O/'fixtures.json',fixtures);save(O/'census.json',census);save(O/'tests.json',{'count':len(T),'checks':T,'mutations':mutations});save(O/'evidence.json',proof)
print(json.dumps({'checks':len(T),'fixtures':len(fixtures),'discrepancies':sum(f['global_native']!=f['current_standalone_adapter']for f in fixtures),'mutations':len(mutations),'evidence_sha256':sha(O/'evidence.json')}))
