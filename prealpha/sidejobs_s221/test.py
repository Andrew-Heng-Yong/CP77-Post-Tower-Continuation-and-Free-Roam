"""Read-back regression tests for S22.1; never writes game or save files."""
import copy, itertools, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT/'prealpha/ncpd_scanner_n1'),str(ROOT/'tools')]
from native_inspect import SafeResource
from audit_activity_batches_b1 import flatten
from catalog_gig_rollout_r2 import read,sha,walk

def graphs(p):
    r=SafeResource(read(p)); return {g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def nodes(g): return {n['id']:n for n in g['nodes']}
def ev(c,f,j):
    if c['$type']=='questLogicalCondition':
        vals=[ev(x,f,j) for x in c['conditions']]
        assert c['operation'] in ('AND','OR')
        return all(vals) if c['operation']=='AND' else any(vals)
    t=c['type']
    if c['$type']=='questJournalCondition': return j.get(t['path']['realPath'])==t['state']
    assert c['$type']=='questFactsDBCondition'
    if t['$type']=='questVarVsVarComparison_ConditionType': a,b=f.get(t['factName1'],0),f.get(t['factName2'],0)
    else: a,b=f.get(t['factName'],0),t['value']
    return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'NotEqual':a!=b}[t['comparisonType']]

def verify(build):
    m=read(build/'build.json'); oldroot=ROOT/'prealpha/sidejobs_s22b/build/s22_03'
    old=read(oldroot/'build.json'); dm=read(ROOT/'prealpha/sidejobs_s22/delamain_v2/build/delamain_07/build.json')
    assert sha(oldroot/'build.json')==m['prior_sha256']=='0BEC19BF535031E465DA85F4864A2D0E4CAE15AB462DA1DFBC9E0AE8C024A08C'
    for p,h in m['source_pins'].items(): assert sha(ROOT/p)==h,p
    assert m['boots']==old['boots'] and m['injections']==old['injections']
    assert m['old_sha256']==old['files'][0]['sha256'] and m['sha256']==sha(build/Path(m['relative']).name)
    assert len(m['resources'])==8 and len(m['changes'])==4
    pairs={tuple(p) for p in dm['phone_balances']}; assert len(pairs)==16
    removed=0; unchanged=0; unchanged_resources=0; changed=[]; conditions=[]
    for depot,h in m['resources'].items():
        assert sha(build/'source'/depot)==h
        label=depot.replace('\\','_')+'.json'
        before=graphs(oldroot/'readback'/label); after=graphs(build/'readback'/label)
        assert before.keys()==after.keys()
        target=depot in ['towercontinued\\sidejobs_s22\\delamain\\support.questphase','towercontinued\\sidejobs_s22\\delamain\\owner.questphase']
        if not target: assert h==old['resources'][depot]; unchanged_resources+=1
        for path,g in before.items():
            assert g['edges']==after[path]['edges'],(depot,path,'edges')
            bn,an=nodes(g),nodes(after[path]); assert bn.keys()==an.keys()
            for i,node in bn.items():
                if target and path=='root' and i in (1002,1003):
                    expected=copy.deepcopy(node); outer=expected['condition']
                    idle=[c for c in outer['conditions'] if c['$type']=='questLogicalCondition' and len(c['conditions'])==73]
                    assert len(idle)==1 and idle[0]['operation']=='AND'
                    comparisons=[c for c in idle[0]['conditions'] if c.get('type',{}).get('$type')=='questVarVsVarComparison_ConditionType']
                    assert len(comparisons)==16
                    assert {(c['type']['factName1'],c['type']['factName2']) for c in comparisons}==pairs
                    assert all(c['type']['comparisonType']=='Equal' for c in comparisons)
                    idle[0]['conditions']=[c for c in idle[0]['conditions'] if c not in comparisons]
                    assert len(idle[0]['conditions'])==57 and an[i]==expected,(depot,i)
                    assert {c['type']['factName']:c['type']['value'] for c in idle[0]['conditions']}==dm['phone_idle_equal']
                    removed+=16; changed.append((depot,path,i)); conditions.append((depot,i,node['condition'],an[i]['condition']))
                else: assert an[i]==node,(depot,path,i); unchanged+=1
    assert removed==64 and unchanged_resources==6 and len(changed)==4
    a=dm['admission']; names={1:'Inactive',2:'Active',3:'Succeeded',4:'Failed'}
    journal={v['path']:names[v['states'][0]] for v in a['journals']}
    base=dm['common_equal']|a['facts_equal']|dm['phone_idle_equal']|{'PTFRS22_SQ025_Permit':1,'PTFRS22_SQ025_Issued':0,'PTFRS22_SQ025_Fault':0}
    history={'holo_delamain_calls_v_start_count':7,'holo_delamain_calls_v_end_count':2,'holo_delamain_sad_calls_v_start_count':0,'holo_delamain_sad_calls_v_end_count':1}
    cases=0; regression=0
    for depot,i,oldc,newc in conditions:
        good=base|history|{'PTFRS22_SQ025_SupportIssued':int(depot.endswith('owner.questphase'))}
        assert not ev(oldc,good,journal) and ev(newc,good,journal); regression+=1; cases+=1
        for key,value in (base|{'PTFRS22_SQ025_SupportIssued':good['PTFRS22_SQ025_SupportIssued']}).items():
            for wrong in (-1,0,1,2,7):
                if wrong!=value: assert not ev(newc,good|{key:wrong},journal),(key,wrong); cases+=1
        for spec in a['journals']:
            for state in (None,'Unknown','Inactive','Active','Succeeded','Failed'):
                assert ev(newc,good,journal|{spec['path']:state})==(state in [names[v] for v in spec['states']]); cases+=1
        # Historical accounting cannot bypass an active call or mutate admission;
        # exercise each pair independently, including the user's mismatches.
        for p in pairs:
            for x,y in itertools.product((-3,0,1,2,7),repeat=2):
                f=good|{p[0]:x,p[1]:y}; assert ev(newc,f,journal)
                assert not ev(newc,f|{'holo_setup_active':1},journal); cases+=2
    # Verify the native reason strict equality was invalid, from stock scene bytes.
    scene=read(ROOT/'research/sidejobs_s22/delamain/dependencies_02/json/base/quest/holocalls/delamain/delamain_holocall.scene.json')
    writes=[x for x in walk(scene) if x.get('$type')=='questSetVar_NodeType']
    facts={x['factName'] for x in writes}
    assert 'holo_delamain_sad_calls_v_active_count' in facts and 'holo_delamain_sad_calls_v_start_count' not in facts
    assert 'holo_delamain_sad_calls_v_end_count' in facts
    controller=read(ROOT/'research/sidejobs_s22/delamain/dependencies_01/json/base/quest/holocalls/delamain/delamain_holocall.questphase.json')
    assert not any('start_count' in str(x.get('factName','')) or 'end_count' in str(x.get('factName','')) for x in walk(controller))
    return dict(status='PASS_NOT_LIVE',build_sha256=sha(build/'build.json'),tester_sha256=sha(Path(__file__)),policy_cases=cases,user_regressions=regression,unchanged_nodes=unchanged,unchanged_resources=unchanged_resources,changed_nodes=changed,removed_equalities=removed,all_edges_unchanged=True,native_cleanup_unchanged=True,owner_ids_unchanged=True,no_new_writes=True,live_pending=True)

if __name__=='__main__':
    b=Path(sys.argv[1]); dst=b/'tests.json'; assert not dst.exists()
    r=verify(b); dst.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps(r,indent=2))
