"""Independent actual readback/source review; evidence-only condition/mutation checks."""
from investigate import *
import ast,difflib,re
def member(text,marker):
    a=text.index(marker);b=text.index('{',a);depth=1;i=b+1
    while depth:
        if text[i]=='{':depth+=1
        if text[i]=='}':depth-=1
        i+=1
    return a,i,text[b+1:i-1]
def canonical(text):return re.sub(r'\s+','',re.sub(r'//[^\n]*','',text))
def array(text,name):return json.loads('['+re.search(r'func '+name+r'\(\)\s*->\s*array<[^>]+>\s*\{\s*return\s*\[(.*?)\];',text,re.S)[1]+']')
def unique(names,values,name,missing):
    if len(names)!=len(values)or names.count(name)!=1:return missing
    return values[names.index(name)]
def evaluate(c,f,j,actor=0):
    kind=c['$type']
    if kind=='questLogicalCondition':
        vals=[evaluate(x,f,j,actor)for x in c['conditions']];return all(vals)if c['operation']=='AND'else any(vals)
    if kind=='questFactsDBCondition':
        q=c['type'];v=f.get(q['factName']);n=q['value']
        if v is None:return False
        return {'Equal':lambda:v==n,'NotEqual':lambda:v!=n,'Greater':lambda:v>n,'GreaterOrEqual':lambda:v>=n,'Less':lambda:v<n,'LessOrEqual':lambda:v<=n}[q['comparisonType']]()
    if kind=='questJournalCondition':
        q=c['type'];ok=j.get(q['path']['realPath'])=={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}[q['state']];return not ok if q.get('inverted')else ok
    if kind=='questCharacterCondition':
        p=c['type']['comparisonParams'];return actor<=p['count']if p['comparisonType']=='LessOrEqual'else actor>=p['count']
    raise AssertionError('Unsupported condition '+kind)
def main():
    out=H/'actual_brendan03_03';assert not out.exists();out.mkdir()
    base=W/'prealpha/quest_restoration_qr13/coordinator/brendan_03';plan=read(base/'serialization_plan.json');serial=read(base/'serialized_01/manifest.json');resource=serial['resources'][0]
    checks=[];negatives=[];mutations=[]
    def ck(name,ok,evidence=None):
        assert ok,name;checks.append({'name':name,'pass':True,'evidence':evidence})
    ck('serialization pins exact',sha(resource['input'])==resource['input_sha256']and sha(resource['raw'])==resource['raw_sha256']and sha(resource['readback_json'])==resource['readback_json_sha256'],resource)
    actual=Resource(read(resource['readback_json'])).normalize();before=Resource(read(W/'prealpha/quest_restoration_qr9/worker_b/resource_readbacks_01/resource_6.json')).normalize()
    ck('zero structural errors',not actual['errors'],actual['errors'])
    old=before['graphs']['root'];new=actual['graphs']['root'];removed=[['1004','True','1008','In']]
    ck('all old nodes retained',set(old['nodes'])<=set(new['nodes']))
    ck('all original payloads except two OR guards retained',all(old['nodes'][k]['payload']==new['nodes'][k]['payload']for k in old['nodes']if k not in['1002','1004']))
    ck('old predicates preserved as first OR arm',all(new['nodes'][k]['payload']['condition']['operation']=='OR'and new['nodes'][k]['payload']['condition']['conditions'][0]==old['nodes'][k]['payload']['condition']for k in['1002','1004']))
    ck('all old edges except selection fork retained',all(e in new['edges']for e in old['edges']if e not in removed))
    ck('old saved fullIn1 claim edges retained',all(e in new['edges']for e in [['1005','Out','1006','In'],['1006','Out','34','In1']]))
    ck('fresh quarantine preserved through false selector',['1004','True','1100','In']in new['edges']and['1100','False','1008','In']in new['edges'])
    ck('new claim reaches only native CYB input',['1105','Out','1106','In']in new['edges']and['1106','Out','34','CYB-661474_reinject']in new['edges'])
    ck('native safe_out aborts without claims',not any(e[0]=='1102'and e[1]=='safe_out'for e in new['edges']))
    ck('native outside/reenter loop retained',all(e in new['edges']for e in [['1102','loop_out','1103','In'],['1103','Out','1101','In']]))
    src=read(W/'prealpha/quest_restoration_qr13/worker_b/revision_02/source_pins.json');by={r['depot']:r for r in src};bug=Resource(read(by[r'base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase']['source_json'])).normalize()
    ck('actual nested native100 exact model',actual['graphs']['root/1102']==bug['graphs']['root/38/100'])
    ck('actor guard present at wait and postdelay recheck',all(any(v.get('$type')=='questCharacterSpawned_ConditionType'and v['comparisonParams']['comparisonType']=='LessOrEqual'and v['comparisonParams']['count']==0 for v in walk(new['nodes'][k]['payload']['condition']))for k in ['1101','1104']))
    ck('six exact nativeFalse scene gates retained',all([str(i),'False','7',f'In{p}']in actual['graphs']['root/1102']['edges']for i,p in[(3,1),(4,2),(5,3),(6,4),(8,6),(9,5)]))
    scripts={}
    for r in plan['redscript_changes']:
        p=Path(r['source']);original=W/'prealpha/quest_restoration_qr8/candidate_01/package'/r['path'];ck('script before/after pins '+r['path'],sha(p)==r['sha256']and sha(original)==r['before_sha256'])
        scripts[p.name]=(p.read_text(encoding='utf-8-sig'),original.read_text(encoding='utf-8-sig'))
    hs,oldhs=scripts['PTFR_HistorySnapshotHS1.reds'];s23,olds23=scripts['PTFR_SideJobsS23.reds']
    stripped=hs
    for marker in ['public abstract class BrendanFinalDataQR13','public static func AdmitsBrendanFinalQR13','public func AllowsBrendanFinalQR13']:
        a,b,_=member(stripped,marker);stripped=stripped[:a]+stripped[b:]
    ck('HS1 all previous executable text unchanged',canonical(stripped)==canonical(oldhs))
    ck('persistent field declaration sequence unchanged',re.findall(r'\b(?:private|public) persistent let [^;]+;',hs)==re.findall(r'\b(?:private|public) persistent let [^;]+;',oldhs))
    a,b,_=member(s23,'if i == 13 && SnapshotStateHS1.AdmitsBrendanFinalQR13');stripped=s23[:a]+s23[b:]
    ck('S23 all previous executable text unchanged',canonical(stripped)==canonical(olds23))
    ck('sample remains complete stable and unsettled protected','this.Same(this.previous[i], current) && this.Ready(i)'in s23 and s23.count('jm.HasAnyDelayedStateChanges()')>=3 and 'if this.Own(i, "Issued") == 0 {'in s23)
    ck('helper contains no engine/native writes',not any(x in member(hs,'public abstract class BrendanFinalDataQR13')[2]+member(hs,'public func AllowsBrendanFinalQR13')[2]for x in ['SetFact','ChangeEntryState','SetState','GiveItem','StartQuest']))
    hindex=int(re.search(r'func ID(\d+)\(\) -> String \{ return "mq037_brendan";',hs)[1]);hpaths=array(hs,'Paths'+str(hindex));hnames=array(hs,'Facts'+str(hindex));paths=array(s23,'Paths13');names=array(s23,'FactNames13')
    ck('eighteen identical named paths with different catalogue ordering supported',len(hpaths)==len(paths)==18 and set(hpaths)==set(paths))
    native_names=array(hs,'Names');ck('ten native names exact S23; HS1 has allowed merchant only',set(native_names)==set(names)and len(names)==10 and set(hnames)==set(names)|{'travelling_merchant_lives'})
    match_body=member(hs,'public static func Match(')[2];expr=re.search(r'return (BrendanFinalDataQR13\.State\(paths.*?);',match_body,re.S)[1]
    allow_body=member(hs,'public func AllowsBrendanFinalQR13')[2]
    ck('certificate gates actual source strictReady/schema/fingerprint/preEnding/stable',all(x in allow_body for x in ['!this.Ready()','this.schema!=1','SnapshotDataHS1.Fingerprint()','NotEquals(this.origin,n"pre_ending")','!this.rows[i].stable']))
    ck('actual Ready requires exported/frozen/notfaulted',canonical(member(hs,'public func Ready()')[2])=='return!this.faulted&&this.ready&&this.frozen&&this.exported;')
    witness=read(W/'prealpha/quest_restoration_qr13/worker_b/revision_02/earned_final_witness.json');facts=dict(witness['facts']);states={k:{'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}[v]for k,v in witness['journals'].items()}
    def match(ps,vs,ns,fs):
        if len(ps)!=18 or len(vs)!=18 or len(ns)!=len(fs)or len(ns)not in[10,11]:return False
        if any(not 1<=unique(ps,vs,p,-1)<=4 for p in hpaths):return False
        if any(not 0<=unique(ns,fs,n,-2147483647)<=1 for n in native_names):return False
        if len(ns)==11 and unique(ns,fs,'travelling_merchant_lives',-2147483647)==-2147483647:return False
        if any(n not in set(native_names)|{'travelling_merchant_lives'}for n in ns):return False
        ex=re.sub(r'BrendanFinalDataQR13\.State\(paths,states,"([^"]+)"\)',lambda m:str(unique(ps,vs,m[1],-1)),expr)
        ex=re.sub(r'BrendanFinalDataQR13\.Fact\(names,facts,"([^"]+)"\)',lambda m:str(unique(ns,fs,m[1],-2147483647)),ex).replace('&&',' and ')
        tree=ast.parse(re.sub(r'\s+',' ',ex).strip(),mode='eval');assert all(isinstance(n,(ast.Expression,ast.BoolOp,ast.And,ast.Compare,ast.Eq,ast.Constant,ast.Load))for n in ast.walk(tree))
        return eval(compile(tree,'<actual Match return predicate>','eval'),{'__builtins__':{}},{})
    current=[states[p]for p in paths];currentf=[facts[n]for n in names];frozen=[states[p]for p in hpaths];frozenf=[facts.get(n,73)for n in hnames]
    def certificate(ps,vs,ns,fs,oldv=frozen,oldf=frozenf,origin='pre_ending',ready=True,stable=True,exported=True,faulted=False,frozen_flag=True):
        if not ready or not stable or not exported or faulted or not frozen_flag or origin!='pre_ending':return False
        if not match(hpaths,oldv,hnames,oldf)or not match(ps,vs,ns,fs):return False
        if any(unique(ps,vs,p,-1)!=oldv[i]for i,p in enumerate(hpaths)):return False
        if any(unique(ns,fs,n,-2147483647)!=unique(hnames,oldf,n,-2147483647)for n in native_names):return False
        return True
    ck('actual-source Match and certificate accept exact earned witness',certificate(paths,current,names,currentf))
    ck('name matching survives shuffled arrays',certificate(paths[::-1],current[::-1],names[::-1],currentf[::-1]))
    ck('generic baseline gate rejects, actual serialized gate admits earned witness',not evaluate(old['nodes']['1002']['payload']['condition'],facts,states)and evaluate(new['nodes']['1002']['payload']['condition'],facts,states)and evaluate(new['nodes']['1104']['payload']['condition'],facts,states))
    for name,args in [('postEndingFallback',{'origin':'post_ending_fallback'}),('notstable',{'stable':False}),('notready',{'ready':False}),('notexported',{'exported':False}),('faulted',{'faulted':True}),('notfrozen',{'frozen_flag':False})]:
        assert not certificate(paths,current,names,currentf,**args);negatives.append({'name':name,'rejected':True})
    for index in range(18):
        v=list(current);v[index]=-1;assert not certificate(paths,v,names,currentf);negatives.append({'name':'missing journal '+paths[index],'rejected':True})
    for index in range(10):
        f=list(currentf);f[index]=1-f[index];assert not certificate(paths,current,names,f);negatives.append({'name':'native fact changed '+names[index],'rejected':True})
    for name,ps,vs,ns,fs in [('duplicatePath',paths[:-1]+[paths[0]],current,names,currentf),('unknownName',paths,current,names[:-1]+['not_real_fact'],currentf),('duplicateFact',paths,current,names[:-1]+[names[0]],currentf)]:
        assert not certificate(ps,vs,ns,fs);negatives.append({'name':name,'rejected':True})
    for fact,value in [('PTFRS23_MQ037_Issued',1),('PTFRS23_MQ037_Entered',1),('PTFRS23_MQ037_Finished',1),('PTFRS23_MQ037_Fault',1),('mq037_done',1),('mq037_final_scene_active',1),('mq037_clerk_aggroed',1),('mq037_clerk_convinced',0),('mq037_brendan_introduced',0)]:
        f=dict(facts);f[fact]=value;assert not evaluate(new['nodes']['1104']['payload']['condition'],f,states);negatives.append({'name':'actual graph rejects '+fact+'='+str(value),'rejected':True})
    for state in[3,4]:
        j=dict(states);j['quests/minor_quest/mq037_brendan']=state;assert not evaluate(new['nodes']['1104']['payload']['condition'],facts,j);negatives.append({'name':'rewarded/failed root '+str(state),'rejected':True})
    assert not evaluate(new['nodes']['1104']['payload']['condition'],facts,states,actor=1);negatives.append({'name':'Theo already present','rejected':True})
    def mutate_guard(fact):
        c=copy.deepcopy(new['nodes']['1104']['payload']['condition'])
        for x in walk(c):
            if x.get('$type')=='questVarComparison_ConditionType'and x.get('factName')==fact:x['comparisonType']='GreaterOrEqual'
        return c
    f=dict(facts);f['PTFRS23_MQ037_Issued']=1;bad=mutate_guard('PTFRS23_MQ037_Issued');assert evaluate(bad,f,states)
    mutants=out/'nonproduction_mutants';mutants.mkdir();(mutants/'issued_guard_widened.normalized.json').write_text(json.dumps(bad,indent=2)+'\n');mutations.append({'fault':'actual serialized Issued guard widened','detected':True,'counterexample':'Issued1 then wrongly passes mutated final recheck'})
    bad=copy.deepcopy(actual['graphs']['root/1102']);bad['edges']=[['3','True','7','In1']if e==['3','False','7','In1']else e for e in bad['edges']];assert bad!=bug['graphs']['root/38/100'];(mutants/'scene_guard_reversed.normalized.json').write_text(json.dumps(bad,indent=2)+'\n');mutations.append({'fault':'actual native scene False edge reversed','detected':True})
    bad=copy.deepcopy(new);bad['edges']=[['1100','False','1005','In']if e==['1100','False','1008','In']else e for e in bad['edges']];assert ['1100','False','1008','In']not in bad['edges'];(mutants/'fresh_quarantine_bypassed.normalized.json').write_text(json.dumps(bad,indent=2)+'\n');mutations.append({'fault':'actual fresh quarantine routed to fresh claim','detected':True})
    nativebody=Resource(read(by[r'base\quest\minor_quests\mq037\mq037_brendan.questphase']['source_json'])).normalize()
    missing_support={'wrapper_root_prefabs':actual['root_prefabs'],'body34_PIP':new['nodes']['34']['payload']['phaseInstancePrefabs'],'preclaim1102_PIP':new['nodes']['1102']['payload']['phaseInstancePrefabs'],'native_body_root_prefabs':nativebody['root_prefabs'],
        'preclaim_trigger':'#mq037_tr_theo_final','reference_hierarchy':'$/03_night_city/.../#mq037_pr_machine_spot/#mq037_tr_theo_final; registry_index_01.json NodeRefs20173, reference-only evidence.',
        'exact_scope':'Missing established preclaim support owner/lease before native antiScene trigger. Native bugfix assumes live originalbody owner. Newbody34 starts only after injector recheck/claim. All nativeinjector outputs Terminating; simple PIP-on1102 also needs outside-loop/recheck handoff review.',
        'not_claimed':'No live deadlock asserted from reference hierarchy alone; safe ownership required by task is not established.'}
    result={'status':'BLOCK_ACTUAL03_PRECLAIM_SUPPORT_OWNERSHIP_NOT_ESTABLISHED','script_source_status':'APPROVED_BOUNDED_SOURCE_SEMANTICS_PENDING_COMPILATION','checks':checks,'negative_controls':negatives,'actual_model_mutations':mutations,'blocking_finding':missing_support,
        'reviewed_scripts':plan['redscript_changes'],'readback_pin':resource,'limits':'Tests evaluate actual serialized conditions and extracted actualREDscript Match predicate through independent source fixtures; they do not execute compiledREDscript or engine callbacks. Finalcompile/package and corrected supportholder readback still required.',
        'other_retained_limits':['Exact saved native owners/leases unobservable offline.','No current userfixture has earned preEnding certificate.','No general Spray/freshDumpster support or nativeclock adoption.'],'runtime_resource_changes':0,'game_or_save_changes':0}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({'status':result['status'],'source_checks':len(checks),'negative_controls':len(negatives),'actual_mutations':len(mutations),'scripts':result['script_source_status']})
if __name__=='__main__':main()
