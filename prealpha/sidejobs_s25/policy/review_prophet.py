"""Independent read-only Prophet source/closure/ownership review, without old builder runs."""
import json, importlib.util
from pathlib import Path
from prepare import ROOT, HERE, read, sha, graphs, walk
spec=importlib.util.spec_from_file_location('policy_tests',HERE/'test.py')
policy_tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy_tests)
seed,evaluate=policy_tests.seed,policy_tests.evaluate


def main():
    build=ROOT/'prealpha/sidejobs_s25/prophet/build/prophet_01'
    manifest=read(build/'build.json');contract=read(ROOT/manifest['contract']);owner=contract['owners'][0]
    pins=dict(manifest['source_pins'])
    for name in ('prealpha/sidejobs_s25/prophet/build/prophet_01/build.json','prealpha/sidejobs_s25/prophet/build/prophet_01/tests.json','prealpha/sidejobs_s25/prophet/test.py','prealpha/sidejobs_s25/policy/build/policy_01/build.json','prealpha/sidejobs_s25/policy/plan02.json'):
        pins[name]=sha(ROOT/name)
    for name,digest in pins.items(): assert sha(ROOT/name)==digest,name
    dependencies={p.split('/raw/',1)[1].replace('/','\\'):p for p in owner['native_dependencies']}
    refs=set();writers=set();hashed=[]
    for source in dependencies.values():
        data=read(ROOT/(source.replace('/raw/','/json/')+'.json'))
        for obj in walk(data):
            if 'DepotPath' in obj:
                p=obj['DepotPath'];v=p.get('$value')
                if p.get('$storage')=='uint64' and v not in ('0',0):hashed.append(v)
                if isinstance(v,str) and v.endswith(('.scene','.questphase')): refs.add(v)
            if obj.get('$type')=='questSetVar_NodeType':writers.add(obj['factName'])
    assert not hashed and refs <= dependencies.keys()
    assert len(dependencies)==8 and len(refs)==7
    # Every modified native job fact is a fresh equality guard except only the
    # two unconditional exact-one initialization facts. No player progress erased.
    passive={'mq026_active','mq026_started'}
    assert writers-passive <= owner['facts_equal'].keys()
    assert all(owner['facts_equal'][k]==0 for k in writers-passive)
    assert owner['fact_ranges']=={k:{'min':0,'max':1} for k in passive}
    native=graphs(ROOT/(owner['native_source'].replace('/raw/','/json/')+'.json'))['root']
    nodes={n['id']:n for n in native['nodes']};edges={tuple(e) for e in native['edges']}
    assert {(0,'Out',3,'In'),(3,'Out',103,'In'),(103,'Out',4,'In'),(4,'Out',50,'In')}<=edges
    for i,key in ((3,'mq026_started'),(4,'mq026_active')):
        assert nodes[i]['type']['factName']==key and nodes[i]['type']['setExactValue']==1 and nodes[i]['type']['value']==1
    assert nodes[103]['type']['factName']=='mq027_50_prophet' and owner['facts_equal']['mq027_50_prophet']==0
    parent=graphs(ROOT/'research/sidejobs_s2/sacrum_audit/native_01/json/base/quest/minor_quests/minorquests.questphase.json')['root']
    ancestry={39}
    while True:
        previous=set(ancestry)
        ancestry.update(a for a,_,b,_ in parent['edges'] if b in previous)
        if ancestry==previous:break
    for n in parent['nodes']:
        if n['id'] in ancestry-{39}: assert n['$type'] in ('questInputNodeDefinition','questLogicalHubNodeDefinition')
    current=graphs(build/'readback/mq026_fresh.json')['root'];n={v['id']:v for v in current['nodes']}
    assert {tuple(e) for e in current['edges']}=={(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'Out',1004,'In'),(1004,'False',1002,'In'),(1004,'True',1005,'In'),(1005,'Out',1006,'In'),(1006,'Out',39,'In1'),(39,'Out1',1007,'In')}
    assert n[1002]['condition']==n[1004]['condition']
    policy=HERE/'build/policy_01';old=graphs(policy/'readback/towercontinued_sidejobs_s23_base_b_mq026.questphase.json')['root'];oldn={v['id']:v for v in old['nodes']}
    newc=n[1004]['condition'];oldc=oldn[1004]['condition'];newf,newj=seed(newc);oldf,oldj=seed(oldc)
    assert not evaluate(oldc,newf,newj) and not evaluate(newc,oldf,oldj)
    assert not evaluate(newc,newf|{'PTFRS23_MQ026_Issued':1},newj)
    assert not evaluate(oldc,oldf|{'PTFRS25_MQ026_FRESH_Issued':1},oldj)
    states=['Inactive','Active','Succeeded','Failed',None];cases=0
    for state in states:
        assert evaluate(newc,newf,newj|{owner['journals'][0]['path']:state})==(state=='Inactive');cases+=1
    result={'status':'PASS_INDEPENDENT_BOUNDED_REVIEW_NOT_LIVE','component_sha256':sha(build/'build.json'),'reviewer_sha256':sha(Path(__file__)),
            'native_closure_resources':8,'native_executable_references':7,'unresolved_hash_references':0,'passive_facts':sorted(passive),
            'stock_parent_ancestors':sorted(ancestry),'new_root_state_cases':cases,'old_new_mutual_exclusion':True,'native_progress_writers_guarded':len(writers-passive),
            'source_pins':pins,'findings':[],
            'limits':'Official installed-byte audit remains an aggregate gate. No saved-engine continuation or live dialogue/reward/Johnny proof. Fresh scene availability and regional time gates stay native.'}
    dest=ROOT/'research/sidejobs_s25/policy/prophet_review_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='source_pins'}))


if __name__=='__main__':main()
