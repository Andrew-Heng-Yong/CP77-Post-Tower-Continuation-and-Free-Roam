import copy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;WS=OUT.parents[2]
s=(OUT/'census_02.py').read_text();q={'__file__':str(OUT/'census_02.py')};exec(s[:s.index('\nmanifest=read')],q)
read,sha,handles,norm,lookup,walk=[q[n] for n in ('read','sha','handles','norm','lookup','walk')]
ba=read(WS/'prealpha/bottle_actions_ba1/native_review/fresh_candidate_01.json');base=norm(ba['Data']['RootChunk'],handles(ba))
n=read(OUT/'fresh_sources_01/base_open_world_combat_events_pacifica_coastview_ce_pac_cvi_phase.questphase.json');nh=handles(n)
contracts=read(OUT/'action_contracts_02.json');graphs=read(OUT/'candidate_172173_graph_proof_01.json')
bp=read(WS/'prealpha/bottle_actions_ba1/native_review/fresh_graph_proof_01.json')
checks=[]
def ck(ok,label):assert ok,label;checks.append(label)
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
for group,owner,cid,alias in [(172,7,64,'#ce_pac_cvi_105_com'),(173,8,61,'#ce_pac_cvi_106_com')]:
    c=read(OUT/f'fresh_candidate_{group}_01.json');actual=norm(c['Data']['RootChunk'],handles(c))
    con=next(x for x in contracts['contracts'] if x['group']==group);full=con['community_refs'][0]
    original=norm(lookup(n['Data']['RootChunk'],f'root/28/{owner}/{cid}',nh),nh)
    edits=0
    for p,v in walk(original):
        if isinstance(v,dict) and v.get('$type')=='NodeRef' and v.get('$value')==alias:v['$value']=full;edits+=1
    candidate=node(node(actual['graph'],10)['phaseGraph'],cid)
    ck(edits==10,f'{group}:exacttenqualifiedrefs')
    ck(candidate==original,f'{group}:completecontrollerpayloadexactexcepttenrefs')
    expected=copy.deepcopy(base)
    oldfull=next(x for x in contracts['contracts'] if x['group']==179)['community_refs'][0]
    def rewrite(v):
        if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
        if isinstance(v,list):return [rewrite(x) for x in v]
        if isinstance(v,str):return v.replace('PTFRBA1_',f'PTFRWA2_{group}_').replace('PTFRWW2_179_',f'PTFRWW2_{group}_').replace(oldfull,full)
        return v
    expected=rewrite(expected)
    loop=node(expected['graph'],10)['phaseGraph'];ix=next(i for i,n in enumerate(loop['nodes']) if n['id']==61);loop['nodes'][ix]=copy.deepcopy(original)
    ck(actual==expected,f'{group}:entirewrapperpayloadidenticaltoverifiedBA1exceptnamespacedreceiptsandnativecontroller')
    gp=next(g for g in graphs['groups'] if g['group']==group)
    ck(gp['root_edges']==bp['root_edges'],f'{group}:rootwholeloopcutrearmexactBA1')
    ck(gp['loop_edges']==sorted(x.replace('61.',str(cid)+'.') for x in bp['loop_edges']),f'{group}:innerReadygateandnativeexitrearmexactBA1')
    ck(gp['nodes']==32 and gp['edges']==43,f'{group}:freshnative32nodes43edges')
    ck(not any(isinstance(v,dict) and v.get('$type') in ('questSpawnManagerNodeDefinition','questCheckpointNodeDefinition','questSceneNodeDefinition') for _,v in walk(actual)),f'{group}:nospawncheckpointscene')
    ck(all(not v.get('phaseInstancePrefabs') for _,v in walk(actual) if isinstance(v,dict) and v.get('$type')=='questPhaseNodeDefinition'),f'{group}:noprefabownership')
    writes=[v for _,v in walk(actual) if isinstance(v,dict) and v.get('$type')=='questSetVar_NodeType']
    ck(all(v['factName'].startswith(f'PTFRWA2_{group}_') and v['setExactValue']==1 for v in writes),f'{group}:onlyexactnewownreceiptwrites')
    bad=copy.deepcopy(actual);node(bad['graph'],12)['permanent']=1
    ck(bad!=expected,f'{group}:negativepermanentcutchangefailswrappercomparison')
out={'status':'PASS_INDEPENDENT_172_173_NATIVE_PAYLOAD_AND_BA1_WRAPPER_EQUIVALENCE','checks':len(checks),'assertions':checks,
 'groups':[{'id':g['group'],'sha256':g['sha256']} for g in graphs['groups']],
 'guard_proof_reuse':'Whole wrapper payload and actual edges equal independently verified BA1 after exact fact namespaces/community refs and full native controller substitution. BA1 32768-state/5negativecontrol proof applies to equivalent guard logic.',
 'game_writes':0,'save_writes':0,'live_verified':False,
 'source_pins':[{'path':str(p),'sha256':sha(p)} for p in [OUT/'verify_172173_01.py',OUT/'verify_172173_01.ps1',OUT/'candidate_172173_graph_proof_01.json',WS/'prealpha/bottle_actions_ba1/native_review/assessment_01.json']]}
(OUT/'candidate_172173_assessment_01.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ('source_pins','assertions')},indent=2))
