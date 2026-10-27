"""Independent corrective-resource tests, with required broken-S30 negative control.

No CR1 builder function is imported. Assertions come from original S25, SR1,
JD1 and S30 contracts and freshly decoded candidate resources. No game APIs run.
"""
import argparse,collections,copy,hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;W=HERE.parents[2]
AUDIT=W/'diagnostics/sidejob_entry_phone_audit_20261026_01'
S30=W/'prealpha/sidejobs_s30/candidate_02'
sys.path.insert(0,str(W/'tools'))
from test_rite_g2 import SafeResource
from audit_activity_batches_b1 import flatten

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)
def value(x):return x.get('$value') if isinstance(x,dict) else x
def gs(p):
    r=SafeResource(read(p));return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def scene(p):
    r=SafeResource(read(p));root=r.payload(r.obj['Data']['RootChunk'])
    return root,{n['nodeId']['id']:n for n in root['sceneGraph']['graph']}
def nodes(g):return {n['id']:n for n in g['nodes']}
def edges(g):return set(map(tuple,g['edges']))
def fact_eq(c,name,num):
    return any(v.get('$type')=='questVarComparison_ConditionType' and v.get('factName')==name and v.get('comparisonType')=='Equal' and v.get('value')==num for v in walk(c))
def journals(c):return [v for v in walk(c) if v.get('$type')=='questJournalEntryState_ConditionType']
def compare(a,b,op):
    return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[op]
def evaluate(c,f,j,external=True):
    kind=c['$type']
    if kind=='questLogicalCondition':
        vals=[evaluate(x,f,j,external) for x in c['conditions']]
        return {'AND':all(vals),'OR':any(vals),'NOR':not any(vals)}[c['operation']]
    if kind=='questJournalCondition':
        t=c['type'];matched=j.get(t['path']['realPath'])==t['state']
        return not matched if t.get('inverted',0) else matched
    if kind=='questFactsDBCondition':
        t=c['type']
        if t['$type']=='questVarVsVarComparison_ConditionType':return compare(f.get(t['factName1'],0),f.get(t['factName2'],0),t['comparisonType'])
        return compare(f.get(t['factName'],0),t['value'],t['comparisonType'])
    if kind in ('questObjectCondition','questTriggerCondition','questDistanceCondition'):return external
    raise ValueError('Unmodelled condition '+kind)
def seed(c):
    f={};j={};constraints=collections.defaultdict(list)
    for v in walk(c):
        if v.get('$type')=='questVarComparison_ConditionType':constraints[v['factName']].append((v['comparisonType'],v['value']))
        if v.get('$type')=='questVarVsVarComparison_ConditionType':f.setdefault(v['factName1'],0);f.setdefault(v['factName2'],0)
        if v.get('$type')=='questJournalEntryState_ConditionType':
            p=v['path']['realPath'];j.setdefault(p,v['state'])
            if v['state']=='Inactive':j[p]='Inactive'
    for name,checks in constraints.items():
        possibilities=sorted({0,1}|{n+d for _,n in checks for d in (-1,0,1)})
        choices=[n for n in possibilities if all(compare(n,want,op) for op,want in checks)]
        assert choices,(name,checks)
        f[name]=choices[0]
    assert evaluate(c,f,j),'Native positive witness unavailable'
    return f,j

parser=argparse.ArgumentParser()
parser.add_argument('--index',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--expect-regression',action='store_true')
args=parser.parse_args()
assert re.fullmatch(r'[A-Za-z0-9_]+\.json',args.output)
output=HERE/args.output;assert not output.exists(),output
index=read(args.index);candidate=Path(index['candidate']);rawroot=candidate/'archive_source'
contract=read(HERE/'checks_contract_01.json')
for p,h in contract['sources'].items():assert sha(W/p)==h,('Independent source pin changed',p)
decoded={r['depot']:r for r in index['resources']}
assert set(decoded)==set(contract['depots'])
for depot,r in decoded.items():
    assert sha(r['raw'])==r['raw_sha256']==sha(rawroot/depot),depot
    assert sha(r['json'])==r['json_sha256'],depot
donors={r['depot']:r for r in read(AUDIT/'collision_decoded_01/inventory.json')}
results=[];count=0
def ck(value,message):
    global count
    count+=1
    assert value,message
def run(name,fn):
    start=count
    try:fn();results.append({'id':name,'result':'PASS','checks':count-start})
    except Exception as e:results.append({'id':name,'result':'FAIL','checks':count-start,'detail':str(e),'exception':type(e).__name__})
def graph(dep,path='root'):return gs(decoded[dep]['json'])[path]
def exact_donor(dep):
    ck(sha(rawroot/dep)==donors[dep]['donor_sha256'],'Resource does not match previously installed corrective donor')
def coherent_graph(g):
    ns=nodes(g)
    ck(len(ns)==len(g['nodes']),'Duplicate native node IDs')
    ck(all(a in ns and b in ns for a,_,b,_ in edges(g)),'Edge points outside graph')

def preservation():
    baseline=read(S30/'manifest.json');expected={p.relative_to(S30/'archive_source').as_posix():sha(p) for p in (S30/'archive_source').rglob('*') if p.is_file()}
    actual={p.relative_to(rawroot).as_posix():sha(p) for p in rawroot.rglob('*') if p.is_file()}
    ck(len(actual)==len(expected)==1172 and actual.keys()==expected.keys(),'Resource set drift')
    changed={d.replace('\\','/'):r['donor_sha256'] for d,r in donors.items()}
    for dep,h in expected.items():ck(actual[dep]==changed.get(dep,h),'Unexpected resource payload '+dep)
    files={p.relative_to(candidate/'package').as_posix():p for p in (candidate/'package').rglob('*') if p.is_file()}
    expected_files={r['path']:r['sha256'] for r in baseline['files']}
    ck(len(files)==51 and files.keys()==expected_files.keys(),'Install path set drift')
    for rel,h in expected_files.items():
        if not rel.endswith('zzzz_PTFR_Combined.archive'):ck(sha(files[rel])==h,'Unexpected non-archive install file change '+rel)
run('full_preservation',preservation)

def yoko():
    dep=r'towercontinued\b0_story_eight\yoko.scene'
    _,ns=scene(decoded[dep]['json']);_,old=scene(W/'prealpha/sidejob_repair_sr1/candidate_02/baseline_yoko.json')
    _,repaired=scene(W/'prealpha/sidejob_repair_sr1/candidate_02/readback/yoko_scene.json')
    ck(ns.keys()==old.keys(),'Scene node identity drift')
    for n in ns:
        if n!=779:ck(ns[n]==old[n],'Unrelated Yoko node changed '+str(n))
    target=ns[779]
    for i in range(len(target['options'])):
        if i in (4,5,6,7):
            ck(bool(target['outputSockets'][i]['destinations']),'Yoko component choice has no output')
            ck(target['options'][i]==repaired[779]['options'][i],'Yoko original scoped component choice changed')
            ck(target['outputSockets'][i]==repaired[779]['outputSockets'][i],'Yoko native destination changed')
            c=target['options'][i]['questCondition']
            for name,num in [('PTFRS29_q305_postcontent_Issued',1),('PTFRS29_q305_postcontent_Entered',1),('PTFRS29_q305_postcontent_Fault',0)]:ck(fact_eq(c,name,num),'Yoko owner/entry/fault guard absent '+name)
            ck(any(j['path']['realPath']=='ep1/quests/main_quest/q305_postcontent' and j['state']=='Active' for j in journals(c)),'Yoko active-root guard absent')
        else:ck(target['options'][i]==old[779]['options'][i] and target['outputSockets'][i]==old[779]['outputSockets'][i],'Unrelated Yoko option changed')
    exact_donor(dep)
run('yoko_component_choices',yoko)

def viktor():
    dep=r'towercontinued\b0_story_eight\viktor.scene';_,ns=scene(decoded[dep]['json']);_,donor=scene(donors[dep]['donor_json'])
    for i,dest in [(351,388),(840,324)]:
        n=ns[i];c=n['options'][1]['questCondition'];outs=n['outputSockets'][1]['destinations']
        ck(any(d['nodeId']['id']==dest for d in outs),'Viktor debt choice disconnected')
        ck(c['operation']=='AND' and len(c['conditions'])==5,'Viktor paid-owner scoped guard shape')
        ck(n==donor[i],'Viktor native payment choice/payload changed')
        bounded=copy.deepcopy(c);bounded['conditions'].pop(3)
        f={'PTFRS25_PAID_Issued':1,'PTFRS25_PAID_Finished':0,'PTFRS25_PAID_Fault':0};j={'quests/minor_quest/mq045_victor_debt':'Active'}
        # Resolve the durable owner spelling from the existing original guard.
        f={v['factName']:v['value'] for v in walk(bounded) if v.get('$type')=='questVarComparison_ConditionType'}
        ck(evaluate(bounded,f,j),'Eligible unpaid owner refused')
        for state in (None,'Inactive','Succeeded','Failed'):ck(not evaluate(bounded,f,{k:state for k in j}),'Terminal/inactive debt option exposed')
        for name in f:
            if name.endswith(('_Issued','_Finished','_Fault')):ck(not evaluate(bounded,f|{name:0 if name.endswith('_Issued') else 1},j),'Debt choice bypasses '+name)
    ck(ns[454]['questNode']['type']['factName']=='victor_debt_paid_full','Native payment receipt removed')
    exact_donor(dep)
run('viktor_debt_choices',viktor)

def wilson_body():
    dep=r'towercontinued\b0_wilson_vendor\body.questphase';g=graph(dep);ns=nodes(g);es=edges(g)
    ck({100,101}<=ns.keys(),'Wilson order selector/scene missing')
    ck(value(ns[101]['sceneFile']['DepotPath'])==r'towercontinued\sidejobs_s25\services\gun_order.scene','Wilson lost dedicated gun order scene')
    ck({(4,'Out',100,'In'),(100,'False',5,'wilson_default_in'),(100,'True',101,'wilson_default_in'),(12,'CutSource',101,'CutDestination')}<=es,'Wilson scene selection/interruption edges missing')
    c=ns[100]['condition'];f,j=seed(c)
    root='quests/side_quest/sq_q001_wilson'
    for state in (None,'Inactive','Active','Succeeded','Failed'):ck(evaluate(c,f,{root:state})==(state in ('Inactive','Active')),'Wilson terminal protection')
    for name in f:
        if name.endswith(('_Issued','_Finished','_Fault')):ck(not evaluate(c,f|{name:0 if name.endswith('_Issued') else 1},j),'Wilson selector bypasses '+name)
    exact_donor(dep)
run('wilson_gun_dispatch',wilson_body)

def wilson_owner():
    dep=r'towercontinued\b0_wilson_vendor\owner.questphase';g=graph(dep);ns=nodes(g);es=edges(g)
    ck({100,101,102,103}<=ns.keys(),'Wilson quest-lease acknowledgement missing')
    ck(fact_eq(ns[100]['condition'],'PTFRB0WV_QuestOwns',1),'Wilson lease selector missing')
    ck(ns[101]['type']['factName']=='PTFRB0WV_Released' and ns[101]['type']['value']==1,'Wilson release receipt missing')
    ck(ns[103]['type']['factName']=='PTFRB0WV_Released' and ns[103]['type']['value']==0,'Wilson reacquire receipt missing')
    ck({(3,'Out',100,'In'),(100,'True',101,'In'),(101,'Out',102,'In'),(102,'Out',3,'In'),(100,'False',103,'In'),(103,'Out',4,'In1')}<=es,'Wilson release/reacquire edges changed')
    exact_donor(dep)
run('wilson_lease_ack',wilson_owner)

def fred():
    dep=r'towercontinued\b0_story_services\fred.questphase';g=graph(dep,'root/5/14');ns=nodes(g);es=edges(g)
    ck({300,301}<=ns.keys(),'Fred native conversation selector missing')
    ck(value(ns[300]['sceneFile']['DepotPath'])==r'base\open_world\vendors\watson\little_china\wat_lch_melee_01\wat_lch_melee_01.scene','Fred native boxing conversation not selected')
    ck({(202,'Out',301,'In'),(301,'False',3,'wat_lch_melee_01_default_start'),(301,'True',300,'wat_lch_melee_01_default_start')}<=es,'Fred native/private scene routes changed')
    for issued in (0,1,2):
        for fault in (0,1):ck(evaluate(ns[301]['condition'],{'PTFRS25_MQ025_FRESH_Issued':issued,'PTFRS25_MQ025_FRESH_Fault':fault},{})==(issued==1 and fault==0),'Fred scoped native scene protection')
    exact_donor(dep)
run('fred_native_intro',fred)

def bullets():
    dep=r'towercontinued\sidejobs_s23\base_b\mq030.questphase';g=graph(dep);ns=nodes(g)
    ck(1021 in ns,'Bullets rearm wait missing')
    ck(ns[1021]['$type']=='questPauseConditionNodeDefinition','Bullets rearm must wait for native service state')
    ck({(1020,'Out1',1021,'In'),(1021,'Out',1020,'In1')}<=edges(g),'Bullets rearm loop disconnected')
    expected=nodes(gs(W/'prealpha/sidejob_repair_sr1/candidate_02/readback/bullets_owner.json')['root'])[1021]
    ck(ns[1021]==expected,'Bullets native rearm condition differs from SR1/native donor')
    exact_donor(dep)
run('bullets_rearm',bullets)

def dennis():
    dep=r'towercontinued\sidejobs_s23\base_b\mq038.questphase';ns=nodes(graph(dep))
    ck(fact_eq(ns[1003]['condition'],'PTFRJD1_Dennis_Issued',1),'MQ038 no longer awaits its phone handler')
    exact_donor(dep)
run('dennis_entry_ack',dennis)

def cleanup():
    dep=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';gg=gs(decoded[dep]['json']);g=gg['root'];ns=nodes(g)
    ck(len(ns)==72,'Shared cleanup is missing corrective branches')
    expected=['dennis/dennis','frank/frank','mr_stud/mr_stud','ozob/ozob','sandra/sandra','wilson/wilson','lizzy/lizzy','r3no/r3no','mama_welles/mamma_welles','claire/claire','kirk/kirk','nancy/nancy','blue_moon/blue_moon','cynthia/cynthia','pepe/pepe','rachel/rachel','delamain/delamain','ncpd_dispatcher/ncpd_dispatcher']
    refs=[value(n.get('phaseResource',{}).get('DepotPath')) for n in ns.values() if n['$type']=='questPhaseNodeDefinition']
    for contact in expected:
        path='base\\quest\\holocalls\\'+contact.replace('/','\\')+'_cleanup.questphase'
        ck(refs.count(path)==1,'Missing/duplicate restored cleanup '+contact)
    ck('root/601' in gg and len(gg['root/601']['nodes'])==6,'Inline courier cleanup removed')
    for gg0 in gg.values():coherent_graph(gg0)
    ck(fact_eq(ns[1300]['condition'],'PTFRJD1_Dennis_Issued',1),'Dennis cleanup ownership receipt missing')
    ck((1301,'True',1302,'In13') in edges(g) and (1302,'Out13',6,'In2') in edges(g),'Original Dennis cleanup ports changed')
    exact_donor(dep)
run('shared_phone_cleanup',cleanup)

def s25_receipt():
    dep=r'towercontinued\sidejobs_s25\families\sq025_fresh.questphase';g=graph(dep);ns=nodes(g)
    ck(65020 in ns,'Shared Delamain phone receipt writer missing')
    ck(ns[65020]['type']=={'$type':'questSetVar_NodeType','factName':'PTFRS22_SQ025_SupportIssued','setExactValue':1,'value':1},'Shared receipt payload changed')
    ck({(92,'Out',65020,'In'),(65020,'Out',94,'In1')}<=edges(g) and (92,'Out',94,'In1') not in edges(g),'Receipt must precede original phone controller')
    exact_donor(dep)
run('s25_delamain_receipt',s25_receipt)

policy=read(W/'prealpha/sidejobs_s25/policy/plan02.json')
for row in policy['resources']:
    def policy_case(row=row):
        dep=row['depot'];actual=gs(decoded[dep]['json'])
        expected=gs(donors[dep]['donor_json'])
        for delta in row['changes']:
            n=nodes(actual[delta['graph']])[delta['node']];dn=nodes(expected[delta['graph']])[delta['node']]
            ck(n==dn,'Original corrective node payload regressed')
            c=n['condition'];f,j=seed(c)
            for root in delta['narrowed_roots']+([delta['added_root']] if 'added_root' in delta else []):
                for state in (None,'Inactive','Active','Succeeded','Failed'):ck(evaluate(c,f,j|{root:state})==(state=='Inactive'),'Native guard accepts protected journal '+root)
            for name in delta['exclusion_facts']:
                for v in (-1,0,1,2):ck(evaluate(c,f|{name:v},j)==(v==0),'Native sibling exclusion lost '+name)
        exact_donor(dep)
    run('native_policy_'+row['depot'].replace('\\','_'),policy_case)

def retained_sr1():
    sr1=read(W/'prealpha/sidejob_repair_sr1/candidate_02/build_native_02.json')
    for label,dep in [('mq058_receipt',r'towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase'),('delamain_sequel_guard',r'towercontinued\sidejobs_s29\entries\sq025b_delamain_insurgence.questphase'),('delamain_phone_guard',r'towercontinued\sidejobs_s29\phone\delamain.questphase')]:
        ck(sha(rawroot/dep)==sr1['resources'][dep],'Retained SR1 repair changed '+label)
        ck(gs(decoded[dep]['json'])==gs(W/'prealpha/sidejob_repair_sr1/candidate_02/readback'/(label+'.json')),'Retained original SR1 semantics changed '+label)
    g=graph(r'towercontinued\sidejobs_s29\entries\mq058_semimaru_crystalcoat.questphase')
    ck((64000,'End Quest',65007,'In') in edges(g) and (64000,'Out1',65007,'In') not in edges(g),'MQ058 receipt port regression')
    forbidden=set(next(e for e in sr1['edits'] if e['kind']=='sequel_not_predecessor_message_freshness')['removed_paths'])
    ns=nodes(graph(r'towercontinued\sidejobs_s29\entries\sq025b_delamain_insurgence.questphase'))
    for i in (65003,65004):ck(not ({j['path']['realPath'] for j in journals(ns[i]['condition'])}&forbidden),'Valid Delamain predecessor history blocked')
    ns=nodes(graph(r'towercontinued\sidejobs_s29\phone\delamain.questphase'))
    for i in (1002,1003):ck(fact_eq(ns[i]['condition'],'PTFRS25_SQ025_FRESH_Issued',0),'S29 duplicate-controller guard lost')
run('retained_sr1_mq058_sequel_phone',retained_sr1)

def s30():
    manifest=read(W/'prealpha/sidejobs_s30/serialized_02/entries_manifest.json')
    jobs={j['id']:j for j in read(W/'prealpha/sidejobs_s30/prepared_02/contracts.json')['jobs']}
    ck(set(jobs)=={'mq006_rollercoaster','mws_se5_07','mws_wat_08_trauma_drama'},'S30 selected scope changed')
    for rec in manifest['entries']:
        dep=rec['depot'];job=jobs[rec['id']];g=graph(dep);ns=nodes(g);es=edges(g)
        ck(es==set(map(tuple,rec['edges'])),'S30 original/native wrapper edges changed '+job['id'])
        ck(ns[65003]['condition']==ns[65004]['condition'],'S30 final atomic recheck differs')
        ck((65004,'False',65003,'In') in es and (65004,'True',65005,'In') in es,'S30 claim edges missing')
        for name,v in rec['guard'].items():ck(fact_eq(ns[65003]['condition'],name,v),'S30 guard lost '+name)
        ck(ns[65007]['type']['factName']==job['tag']+'_Finished','S30 completion receipt changed')
        ck(value(ns[rec['child']]['phaseResource']['DepotPath'])==job['private_native'],'S30 private native child changed')
        if job['id']=='mq006_rollercoaster':
            ck({(65005,'Out',65008,'In'),(65008,'Out',65006,'In'),(20,'Out1',65009,'In'),(65009,'Out',65007,'In')}<=es,'Coaster lease ownership order lost')
        if job['id']=='mws_se5_07':ck(job['vehicle_zero']==[{'record':'Vehicle.v_sport2_porsche_911turbo_cabrio_player'}],'Porsche ownership protection lost')
        if job['id']=='mws_wat_08_trauma_drama':ck(job['fact_ranges']['shooter_appeared_on_leaderboard']['min']==1,'Arcade earned-entry protection lost')
    s30base=read(S30/'manifest.json')
    for dep,h in s30base['overlays'].items():ck(sha(rawroot/dep)==h,'S30 native/dialogue/Johnny/lipmap resource changed '+dep)
    lip=read(decoded[r'towercontinued\sidejob_repair_sr1\en-us.lipmap']['json'])['Data']['RootChunk']
    ck(len(lip['scenePaths'])==len(lip['sceneEntries'])==48,'English48-scene mapping regressed')
    xl=(candidate/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl').read_text()
    for job in jobs.values():ck(xl.count('towercontinued\\sidejobs_s30\\entries\\'+job['id']+'.questphase')==1,'S30 XL registration changed')
    ck('mq057_motorbreath' not in xl,'River hold was violated')
run('retained_s30_three_entries',s30)

def runtime():
    folder=candidate/'package/r6/scripts/PTFR_Consolidated'
    s29=(folder/'PTFR_SideJobsS29.reds').read_text()
    ck('private func AdoptS25DelamainPhone()' in s29 and 'PTFRS25_SQ025_FRESH_Finished' in s29 and 'PTFRS22_SQ025_SupportIssued' in s29,'Completed S25 controller adoption lost')
    for module in ['PTFR_SideJobsS22.reds','PTFR_SideJobsS23.reds','PTFR_HistorySnapshotHS1.reds']:
        ck(sha(folder/module)==sha(S30/'package/r6/scripts/PTFR_Consolidated'/module),'Existing runtime history/root admission safeguards changed '+module)
    phone=nodes(graph(r'towercontinued\judy_dennis_jd1\dennis_phone.questphase'))
    ck(phone[1002]['condition']==phone[1003]['condition'],'Dennis phone final recheck lost')
    writes={n['type']['factName'] for n in phone.values() if n['$type']=='questFactsDBManagerNodeDefinition'}
    ck(writes=={'PTFRJD1_Dennis_Ready','PTFRJD1_Dennis_Issued'},'Phone bootstrap writes unexpected facts')
run('retained_runtime_and_dennis_initializer',runtime)

failed={r['id'] for r in results if r['result']=='FAIL'}
negative_required={'yoko_component_choices','viktor_debt_choices','wilson_gun_dispatch','wilson_lease_ack','fred_native_intro','bullets_rearm','dennis_entry_ack','shared_phone_cleanup','s25_delamain_receipt'}
retained_required={'retained_sr1_mq058_sequel_phone','retained_s30_three_entries','retained_runtime_and_dennis_initializer'}
accepted=(negative_required<=failed and not (retained_required&failed)) if args.expect_regression else not failed
status=('NEGATIVE_CONTROL_DETECTED_KNOWN_S30_REGRESSIONS' if accepted else 'NEGATIVE_CONTROL_UNEXPECTED_RESULT') if args.expect_regression else ('PASS_INDEPENDENT_SEMANTIC_REPAIR_AND_PRESERVATION_NOT_LIVE' if accepted else 'FAIL_CANDIDATE_SEMANTIC_REGRESSION')
report={'status':status,'candidate':str(candidate),'readback_index':str(Path(args.index).resolve()),'readback_index_sha256':sha(args.index),
        'checks_contract_sha256':sha(HERE/'checks_contract_01.json'),'tester_sha256':sha(__file__),
        'checks':count,'groups':len(results),'failed_groups':sorted(failed),'results':results,
        'expected_negative_control':args.expect_regression,'negative_required_groups':sorted(negative_required),
        'game_writes':0,'save_writes':0,'game_launches':0,'limits':['Offline resource/guard validation is not engine execution or saved-phase migration proof.','No11-marker investigation.','Compilation, archive packed readback, install/rollback fixtures and actual deployment are parent responsibilities.']}
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['status','checks','groups','failed_groups']},indent=2))
sys.exit(0 if accepted else 1)
