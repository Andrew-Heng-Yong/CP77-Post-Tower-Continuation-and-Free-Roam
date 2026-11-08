"""Read-only Paid in Full contract checks against pinned native and PH3 inputs.

Run from the repository root: python -B <this file> <fresh-output-directory>.
No historical builder, compiler, game API or deployment script is imported.
Mutations are in-memory negative controls, never runtime edits.
"""
import collections
import copy
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools/parity_audit'))
from model import Resource

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest().upper()
def write(p, x): Path(p).write_text(json.dumps(x, indent=2) + '\n', encoding='utf-8')
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

PAID = r'towercontinued\sidejobs_s25\services\paid_fresh.questphase'
SCENE = r'towercontinued\b0_story_eight\viktor.scene'
BODY = r'towercontinued\b0_story_eight\viktor.questphase'
NATIVE = r'base\quest\bugfixing\minor_quests\mq033\mq033_quest_bugfixes.questphase'
N_SCENE = r'base\quest\tertiary_characters\default_dialogues\victor_vector_default.scene'
N_BODY = r'base\quest\default_dialogs.questphase'
PHONE = r'base\quest\holocalls\victor\victor_holocall.questphase'
P_SCENE = r'base\quest\holocalls\victor\victor_holocall.scene'
CLEAN = r'base\quest\holocalls\victor\victor_cleanup.questphase'
JROOT = 'quests/minor_quest/mq045_victor_debt'
NODES = ['13', '8', '9', '12', '10', '11']
N_EDGES = [['13','Out','8','Active'], ['8','Out','9','Active'], ['9','Out','12','In'], ['12','Out','10','Succeeded'], ['10','Out','11','Succeeded']]
DEBT_SCENE_NODES = ['324','1141','1136','1129','50','156','1132','454','1144','93']

def evaluate(c, f, j):
    t = c['$type']
    if t == 'questLogicalCondition':
        v = [evaluate(x, f, j) for x in c['conditions']]
        return {'AND': all(v), 'OR': any(v), 'NOR': not any(v)}[c['operation']]
    if t == 'questFactsDBCondition':
        x=c['type']; a=f[x['factName']]; b=x['value']
        return {'Equal':a==b,'Less':a<b,'Greater':a>b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
    if t == 'questJournalCondition':
        x=c['type']; result=j.get(x['path']['realPath'])==x['state']
        return not result if x['inverted'] else result
    raise ValueError('Unsupported condition cannot be assumed: '+t)

def graph_path(g, a, b):
    todo=collections.deque([(str(a), [])]); seen=set()
    while todo:
        n, path=todo.popleft()
        if n==str(b): return path
        if n in seen: continue
        seen.add(n)
        for e in g['edges']:
            if e[0]==n and e[1]!='CutSource': todo.append((e[2],path+[e]))
    return None

def assert_slice(native, paid):
    n=native['graphs']['root/21']; p=paid['graphs']['root']
    for i in NODES:
        assert p['nodes'][i]['payload']==n['nodes'][i]['payload'], ('native_payload',i)
        assert p['nodes'][i]['sockets']==n['nodes'][i]['sockets'], ('native_sockets',i)
    assert sorted(e for e in p['edges'] if e[0] in NODES and e[2] in NODES)==sorted(N_EDGES)
    assert paid['refs']==[] and paid['root_prefabs']==[]
    assert p['nodes']['1002']['payload']['condition']==p['nodes']['1003']['payload']['condition']
    for i,node in p['nodes'].items():
        if i not in NODES:
            for w in node['writes']: assert w['factName'].startswith('PTFRS25_PAID_')
    assert ['1004','Out','1005','In'] in p['edges']
    assert ['1005','Out','13','In'] in p['edges']
    assert ['11','Out','1007','In'] in p['edges']
    assert len(p['nodes'])==13 and len(p['edges'])==13
    assert p['nodes']['1004']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRS25_PAID_Issued','setExactValue':1,'value':1}]

def assert_payment(native, restored):
    a=native['graphs']['scene']; b=restored['graphs']['scene']
    assert native['metadata']==restored['metadata'], 'actor/prop/workspot/VO/header divergence'
    for i in ['351','840']:
        x=a['nodes'][i]['payload']['options'][1]; y=b['nodes'][i]['payload']['options'][1]
        ybase=copy.deepcopy(y); ybase['questCondition']=x['questCondition']
        assert x==ybase, ('payment_metadata',i)
        c=y['questCondition']; assert c['operation']=='AND' and len(c['conditions'])==5
        assert c['conditions'][3]==x['questCondition'], ('native_payment_predicate',i)
        assert c['conditions'][0]['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS25_PAID_Issued','value':1}
        assert c['conditions'][1]['type']['factName']=='PTFRS25_PAID_Finished' and c['conditions'][1]['type']['value']==0
        assert c['conditions'][2]['type']['factName']=='PTFRS25_PAID_Fault' and c['conditions'][2]['type']['value']==0
        assert c['conditions'][4]['type']['path']['realPath']==JROOT and c['conditions'][4]['type']['state']=='Active'
        assert [e for e in a['edges'] if e[:2]==[i,'0:1']]==[e for e in b['edges'] if e[:2]==[i,'0:1']]
    assert graph_path(b,'1','840') and ['840','0:1','324','0:1'] in b['edges']
    for i in DEBT_SCENE_NODES:
        assert a['nodes'][i]['payload']==b['nodes'][i]['payload'], ('debt_scene_payload',i)
        assert [e for e in a['edges'] if e[0]==i]==[e for e in b['edges'] if e[0]==i], ('debt_scene_edges',i)
    for a1,b1 in [('1141','1144'),('324','454'),('454','93')]:
        assert graph_path(a,a1,b1)==graph_path(b,a1,b1), ('debt_path',a1,b1)

def assert_body(native, body):
    p=body['graphs']; n=native['graphs']
    a=copy.deepcopy(n['root/7/33']['nodes']['3']['payload']); b=p['root']['nodes']['5']['payload']
    a['id']=5; assert a==b, 'ancestor prefab owner changed'
    outer=n['root/7/33/3']; inner=p['root/5']
    assert outer==inner, 'entire native service outer body changed'
    outer=n['root/7/33/3/40']; inner=p['root/5/40']
    assert set(inner['nodes'])==set(outer['nodes'])|{'200','201','202','203'}
    for i,node in outer['nodes'].items():
        expected=copy.deepcopy(node['payload'])
        if i=='3': expected['sceneFile']['DepotPath']['$value']=SCENE
        assert expected==inner['nodes'][i]['payload'], ('full_service_native_payload',i)
    removed=[['11','Out','3','holocall_in'],['22','Out','3','victor_vector_default_start'],['32','Out','36','In'],['7','Out','3','victor_vector_default_start']]
    added=[['11','Out','201','In'],['200','Out','3','victor_vector_default_start'],['201','Out','3','holocall_in'],['202','Out','3','victor_vector_default_start'],['203','Out','36','In'],['22','Out','202','In'],['32','Out','203','In'],['7','Out','200','In']]
    assert sorted(inner['edges'])==sorted([e for e in outer['edges'] if e not in removed]+added)
    for i in ['200','201','202','203']:
        ws=inner['nodes'][i]['writes']; assert len(ws)==1
        assert ws[0]['factName'].startswith('PTFRB0S4VIKTOR_') and ws[0]['setExactValue']==0 and ws[0]['value']==1
    for i in ['2','10','36','38']:
        assert n['root/7/33/3/40']['nodes'][i]['payload']==p['root/5/40']['nodes'][i]['payload'], ('service_native_payload',i)
    for e in [['36','True','38','In'],['38','Out','32','In']]:
        assert e in p['root/5/40']['edges'], ('payment_departure_wait',e)

def load_models():
    resources=read(HERE/'resources.json'); models={}; pins=[]
    for d,row in resources.items():
        cached=Path(row['normalized_model']); assert sha(cached)==row['normalized_sha256'], d
        old=json.loads(gzip.decompress(cached.read_bytes())); actual=Resource(read(row['source_json'])).normalize()
        # Reparse the original serialized JSON instead of trusting the cached model alone.
        assert actual['graphs']==old['graphs'], ('cached_graph_stale',d)
        assert actual['metadata']==old['metadata'], ('cached_metadata_stale',d)
        assert not actual['errors'], ('source_structural_error',d,actual['errors'])
        models[d]=actual
        pin=dict(row,source_json_sha256=sha(row['source_json']))
        current=ROOT/'prealpha/phone_studios_ph3/candidate_01/archive_source'/Path(d.replace('\\','/'))
        if current.exists(): assert sha(current)==row['resource_sha256']; pin['actual_raw']=str(current);pin['raw_pin_verified']=True
        pins.append(dict(depot=d,**pin))
    explicit={NATIVE:ROOT/'research/sidejobs_s25/services/native_01/raw/base/quest/bugfixing/minor_quests/mq033/mq033_quest_bugfixes.questphase',N_SCENE:ROOT/'research/b0_vendor_rollout/special_scene_sources/raw/base/quest/tertiary_characters/default_dialogues/victor_vector_default.scene',N_BODY:ROOT/'research/sidejobs_s29/native_01/basegame_4_gamedata/raw/base/quest/default_dialogs.questphase'}
    for d,p in explicit.items():
        assert sha(p)==resources[d]['resource_sha256'], ('native_raw_pin',d)
        for pin in pins:
            if pin['depot']==d: pin['actual_raw']=str(p);pin['raw_pin_verified']=True
    return models,pins

def run(out):
    assert not out.exists(), 'Use a fresh output directory; preserve evidence'
    out.mkdir(parents=True)
    m,pins=load_models(); checks=[]
    def check(name,fn): fn();checks.append({'name':name,'status':'PASS'})
    check('native_six_node_debt_lifecycle_exact',lambda:assert_slice(m[NATIVE],m[PAID]))
    check('balanced_payment_scene_route_and_cleanup_exact',lambda:assert_payment(m[N_SCENE],m[SCENE]))
    check('native_ancestor_prefab_and_payment_departure_wait',lambda:assert_body(m[N_BODY],m[BODY]))
    p=m[PAID]['graphs']['root'];cond=p['nodes']['1002']['payload']['condition']
    facts={}
    for x in walk(cond):
        if x.get('$type')=='questVarComparison_ConditionType':
            if x['comparisonType'] in ('Equal','GreaterOrEqual'):facts[x['factName']]=x['value']
    journals={x['path']['realPath']:'Inactive' for x in walk(cond) if x.get('$type')=='questJournalEntryState_ConditionType'}
    assert len(journals)==4
    check('positive_earned_unstarted_native_seam',lambda:(_ for _ in ()).throw(AssertionError()) if not evaluate(cond,facts,journals) else None)
    negatives=[]
    for f in facts:
        alt=0 if facts[f]!=0 else 1
        assert not evaluate(cond,facts|{f:alt},journals),f
        negatives.append({'changed_fact':f,'value':alt,'admitted':False})
    for path in journals:
        for state in ['Active','Succeeded','Failed',None]:
            assert not evaluate(cond,facts,journals|{path:state}),(path,state)
            negatives.append({'changed_journal':path,'state':state,'admitted':False})
    checks.append({'name':'eligibility_negative_boundaries','status':'PASS','cases':len(negatives)})
    # REDscript generated data must agree with the actual admission conditions.
    script=ROOT/'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS25.reds'
    text=script.read_text(); arrays={}
    for name in ['Paths','StatesA','StatesB','FactNames','FactMin','FactMax']:
        match=re.search(r'func '+name+r'0\(\).*?return (\[.*?\]);',text)
        assert match, name
        arrays[name]=json.loads(match.group(1))
    assert arrays['Paths']==list(journals)
    assert arrays['StatesA']==arrays['StatesB']==[1]*4
    for f,a,b in zip(arrays['FactNames'],arrays['FactMin'],arrays['FactMax']):
        assert a==facts[f] and (b==a or (f in ['q001_just_after_rd_scene','victor_vector_default_on'] and b==2147483647))
    assert 'if !IsDefined(qs) || this.Own(i, "Issued") != 0 { return; }' in text
    assert 'if this.Own(i, "Issued") == 0 {' in text
    assert 'this.Same(this.previous[i], current) && this.Ready(i)' in text
    checks.append({'name':'current_S25_array_and_durable_owner_contract','status':'PASS','source':str(script),'sha256':sha(script)})
    # Native phone service is orthogonal to the debt phase: verify the exact endpoints.
    phone=m[PHONE]['graphs']['root']; ps=m[P_SCENE]['graphs']['scene']; clean=m[CLEAN]['graphs']['root']
    for request,node,clear,entry,ack in [('holo_v_calls_victor_start_activate','4','12','holo_v_calls_victor_start','43'),('holo_v_calls_victor_end_activate','5','13','holo_v_calls_victor_end','44')]:
        assert any(x.get('factName')==request and x['comparisonType']=='Greater' and x['value']==0 for x in phone['nodes'][node]['reads'])
        assert phone['nodes'][clear]['writes'][0]['factName']==request and phone['nodes'][clear]['writes'][0]['value']==0
        assert [clear,'Out','0',entry] in phone['edges']
        assert graph_path(ps,ps['entries'][entry],ack)
        assert ps['nodes'][ack]['writes'][0]['factName']==request.replace('_activate','_done')
    assert clean['nodes']['5']['reads'][0]['factName1']=='holo_v_calls_victor_start_count'
    assert clean['nodes']['5']['reads'][0]['factName2']=='holo_v_calls_victor_end_count'
    assert ['5','True','7','In'] in clean['edges'] and ['7','Out','2','holo_v_calls_victor_end'] in clean['edges']
    checks.append({'name':'shared_Viktor_native_request_ack_and_cleanup_binding','status':'PASS'})
    # Mutation controls compare real native against independently changed copies.
    controls=[]
    def rejects(name,change,fn,model):
        x=copy.deepcopy(model);change(x)
        try:fn(x)
        except AssertionError:controls.append({'name':name,'status':'DETECTED'});return
        raise AssertionError('Mutation escaped: '+name)
    rejects('delete_completion_edge',lambda x:x['graphs']['root']['edges'].remove(['12','Out','10','Succeeded']),lambda x:assert_slice(m[NATIVE],x),m[PAID])
    rejects('change_native_earned_prerequisite',lambda x:x['graphs']['root']['nodes']['13']['payload']['condition']['type'].update(value=99),lambda x:assert_slice(m[NATIVE],x),m[PAID])
    rejects('disable_actual_payment_debit',lambda x:x['graphs']['scene']['nodes']['840']['payload']['options'][1]['bluelineCondition']['type']['scriptCondition'].update(payWhenSucceded=0),lambda x:assert_payment(m[N_SCENE],x),m[SCENE])
    rejects('remove_payment_cleanup_edge',lambda x:x['graphs']['scene']['edges'].remove(['454','0:0','1144','0:1']),lambda x:assert_payment(m[N_SCENE],x),m[SCENE])
    rejects('change_debt_receipt_writer',lambda x:x['graphs']['scene']['nodes']['454']['payload']['questNode']['type'].update(value=0),lambda x:assert_payment(m[N_SCENE],x),m[SCENE])
    rejects('remove_active_root_payment_guard',lambda x:x['graphs']['scene']['nodes']['840']['payload']['options'][1]['questCondition']['conditions'].pop(),lambda x:assert_payment(m[N_SCENE],x),m[SCENE])
    rejects('omit_parent_prefab',lambda x:x['graphs']['root']['nodes']['5']['payload'].update(phaseInstancePrefabs=[]),lambda x:assert_body(m[N_BODY],x),m[BODY])
    rejects('remove_payment_departure_wait',lambda x:x['graphs']['root/5/40']['edges'].remove(['36','True','38','In']),lambda x:assert_body(m[N_BODY],x),m[BODY])
    evidence={
      'schema':1,'quest_id':'mq045_victor_debt','static_verified':False,'runtime_changes':[],
      'native_slice':{'resource':NATIVE,'graph':'root/21','nodes':NODES,'edges':N_EDGES,'removed_non_gameplay_marker':'CYB-571237 increment at native2; no quest payload removed'},
      'entry':{'resource':PAID,'graph':'root','edges':p['edges'],'guard':cond,'journal_negative_cases':negatives},
      'payment':{'resource':SCENE,'choice':'840','option':1,'economic_assignment':'EconomicAssignment.q001_victor_debt','payWhenSucceded':1,'native_in_person_path':['840','324','1141','1136','1129','50','1132','454','1144','93'],'live_only':'Balanced payment amount/engine debit, rendered VO, streaming, animation, journal-parent propagation and interrupted save/reload cannot be inferred from structural equality.'},
      'scene_metadata_exact_to_native':True,'scene_changed_nodes':[i for i,n in m[N_SCENE]['graphs']['scene']['nodes'].items() if n['payload']!=m[SCENE]['graphs']['scene']['nodes'][i]['payload']],
      'native_cleanup':{'resource':CLEAN,'graph':'root','comparison':'5','reset_writer':'7','end_scene_node':'2'},
      'inputs':pins,'static_checks':checks,'mutations':controls,
      'limits':['Full native bugfix ancestry retirement proof is integrated by root, not assumed from killed fact alone.','World node placement/actual device target binding is not decoded by this script; exact ancestor prefab identity is checked.','Not a gameplay test or saved-running-node execution proof.']}
    write(out/'evidence.json',evidence)
    write(out/'tests.json',{'status':'PASS_STATIC_PROPERTIES','checks':checks,'negative_eligibility_cases':len(negatives),'mutations':controls,'runtime_changes':False,'verifier_sha256':sha(__file__)})
    print(json.dumps({'status':'PASS_STATIC_PROPERTIES','checks':len(checks),'negative_eligibility_cases':len(negatives),'mutation_controls':len(controls),'out':str(out)}))

if __name__=='__main__':
    run(Path(sys.argv[1]).resolve())
