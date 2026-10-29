"""Independent W3-compatible support review and frozen 26-resource aggregate."""
import copy,json,re
from pathlib import Path
OUT=Path(__file__).resolve().parent;H=OUT.parent;WS=H.parents[1];C=H/'candidate_01'
ss=(OUT/'census_02.py').read_text();q={'__file__':str(OUT/'census_02.py')};exec(ss[:ss.index('\nmanifest=read')],q)
read,sha,handles,norm,lookup,walk=[q[n] for n in ('read','sha','handles','norm','lookup','walk')]
checks=[]
def ck(ok,label):assert ok,label;checks.append(label)
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
s=read(OUT/'fresh_support_01.json');sn=norm(s['Data']['RootChunk'],handles(s));w=read(OUT/'fresh_W3_reference_01.json');wn=norm(w['Data']['RootChunk'],handles(w))
n=read(OUT/'fresh_sources_01/base_open_world_combat_events_santo_domingo_arroyo_ce_std_arr_phase.questphase.json');native=norm(lookup(n['Data']['RootChunk'],'root/24/95',handles(n)),handles(n))
def rewrite(v):
    if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
    if isinstance(v,list):return [rewrite(x) for x in v]
    if isinstance(v,str):return v.replace('PTFRWW2_179_','PTFRWW2_250_')
    return v
expected=[copy.deepcopy(node(wn['graph'],0))]
for i in range(210,216):
    x=rewrite(copy.deepcopy(node(wn['graph'],i)));x['id']=i-110
    if i==215:x['phaseInstancePrefabs']=native['phaseInstancePrefabs']
    expected.append(x)
ck(sn['graph']['nodes']==expected,'All7supportnodespayloadexactW3exceptgroupnamespaceIDsandexactnativeprefab')
ck(node(sn['graph'],105)['phaseInstancePrefabs']==native['phaseInstancePrefabs'],'Exactlyoneauthored250prefabentrypreserved')
sp=read(OUT/'fresh_support_graph_01.json')
ck(sp['root_edges']==sorted(['0.Out -> 100.In','100.Out -> 101.In','101.Out -> 102.In','102.Out -> 103.In','103.Out -> 104.In','104.Out -> 105.In1']),'Freshsupportrootedgesexact')
ck(sp['inner_edges']==sp['W3_inner_edges']==['0.Out -> 1.In','1.Out -> 2.In'],'FreshsupportinnerholdlifetimeexactW3')
writers=[v for _,v in walk(sn) if isinstance(v,dict) and v.get('$type')=='questSetVar_NodeType']
ck(len(writers)==5 and all(v['factName'].startswith('PTFRWW2_250_') and v['setExactValue']==1 for v in writers),'Only5exactnewownedreceiptwrites')
ck(not any(v.get('$type') in ('questSpawnManagerNodeDefinition','questSceneNodeDefinition','questCombatNodeDefinition','questMovePuppetNodeDefinition','questWorldDataManagerNodeDefinition') for _,v in walk(sn) if isinstance(v,dict)),'NoactualspawnAIsceneworldstateoperation')
build=read(C/'script_source/support_build_01.json');before=Path(build['source']);after=Path(build['candidate']);b=before.read_bytes();a=after.read_bytes();lines=a.splitlines(keepends=True)
starts=[i for i,l in enumerate(lines) if b'g.id = 250; g.prefix = "PTFRWW2_250_"' in l];ck(len(starts)==1,'Onegroup250driverrow')
insert=b''.join(lines[starts[0]:starts[0]+3]);proof=read(H/'coverage_review/support_assessment_01.json')
ck(a.replace(insert,b'',1)==b,'Exact3lineappendalloldruntimebytespreserved')
ck(b'3323904054656225535ul' in insert and proof['candidate250']['community_ref'].encode() in insert,'ExactcurrentcommunityhashandNodeRefmapping')
ck(sha(before)==build['original_sha256'] and sha(after)==build['candidate_sha256'],'Baselineandcandidatebytepinsunchanged')
oldids=re.findall(rb'g.id = (\d+); g.prefix = "([^"]+)";',b);newids=re.findall(rb'g.id = (\d+); g.prefix = "([^"]+)";',a)
ck(len(oldids)==237 and newids==oldids+[(b'250',b'PTFRWW2_250_')],'All237existinggrouporderandmappingpreserved')
compile=read(C/'compile_01/result.json');ck(compile['status']=='PASS' and compile['source_count']==64 and compile['candidate_sha256']==sha(after),'Fresh64sourcecompilematchesexactcandidate')
actions=read(OUT/'candidate_assessment_03.json');ck(actions['action_resources']==25 and actions['checks']==295,'Final25actionindependentsemanticproof')
resources=[{'depot':r['resource'].replace('/','\\'),'sha256':r['sha256']} for r in actions['resources']]
res=C/'source/towercontinued/world_actions_wa2/group250_support.questphase';ck(sha(res)==sp['support_sha256'],'Supportcookedhashunchanged')
resources.append({'depot':'towercontinued\\world_actions_wa2\\group250_support.questphase','sha256':sha(res)})
actual={p.relative_to(C/'source').as_posix().replace('/','\\'):sha(p) for p in (C/'source').rglob('*') if p.is_file()}
ck(len(resources)==26 and {r['depot']:r['sha256'] for r in resources}==actual,'Exactly26finalsourcefilescovered')
pinfiles=[OUT/'finalize_26_01.py',OUT/'candidate_assessment_03.json',OUT/'verify_candidates_01.py',OUT/'fresh_candidates_03/proof.json',
 OUT/'action_contracts_02.json',OUT/'census_raw_02.json',OUT/'coverage_02.md',OUT/'fresh_source_proof_01.json',OUT/'fresh_support_01.json',OUT/'fresh_W3_reference_01.json',OUT/'fresh_support_graph_01.json',OUT/'fresh_support_01.ps1',
 H/'environment_review/assessment_01.json',H/'environment_review/community_rebinds_01.json',H/'coverage_review/support_assessment_01.json',H/'coverage_review/assessment_02.json',C/'support_validation_01.json',C/'compile_01/result.json',C/'script_source/support_build_01.json',after]
out={'status':'PASS_INDEPENDENT_26_RESOURCE_WA2_SEMANTIC_COHORT','resources':sorted(resources,key=lambda r:r['depot']),
 'pins':[{'path':str(p),'sha256':sha(p)} for p in pinfiles],
 'checks':actions['checks']+len(checks),'independent_support_checks':len(checks),'support_assertions':checks,'action_resources':25,'support_resources':1,
 'shooting_groups':[172,173,246,250,289],'vehicle_groups':[98,122,199,204,242,243,251,252,253,256,275,280,287,291,305,311,318,319,342,343],
 'BA1_179':'Preserved by parent package; no new179owner or receipt reset.','vehicle_lifetime':'20controllers issue once percommunityReady lifetime; onlyNotReady terminates. Global safety bounce does not replay events.',
 'shooting_lifetime':'5controllers retain fullwholeloopsafetycut andReadyrearm; nativecuts/targets/timerspreserved.',
 'source_census':'237W3owners/257inlinephases freshlybinaryverified plus soleexternalowner fullydecoded. 26slicecontracts include existingBA1preserve and outside250; actualnewcohort25actions+one250support.',
 'game_writes':0,'save_writes':0,'runtime':'BA1 userconfirmed; expandedWA2livebehaviorandsavereloadunverified.'}
(OUT/'final_assessment_01.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'resources':len(resources),'checks':out['checks'],'support_checks':len(checks),'proof_sha256':sha(OUT/'final_assessment_01.json')},indent=2))
