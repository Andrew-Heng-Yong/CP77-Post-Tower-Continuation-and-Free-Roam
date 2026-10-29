"""Classify exact external phase payloads; no implementation or game edits."""
import collections,hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def value(x):return x.get('$value') if isinstance(x,dict) else x
def graph_index(doc):
    handles={d['HandleId']:d['Data'] for d in walk(doc) if 'HandleId' in d and 'Data' in d}
    def unhandle(x):return None if not x else x.get('Data') or handles.get(x.get('HandleRefId'))
    result={}
    def visit(g,path):
        for h in g.get('nodes',[]):
            n=unhandle(h);p=path+'/'+str(n['id']);result[p]=n
            child=unhandle(n.get('phaseGraph'))
            if child:visit(child,p)
    visit(unhandle(doc['Data']['RootChunk']['graph']),'root')
    return result
inventory=read(OUT/'external_01/report_01.json')
coverage=read(OUT/'coverage_01.json')
byres=collections.defaultdict(list)
for r in coverage['rows']:
    if r['external_phase'] not in (None,'0'):byres[r['external_phase']].append(r['candidate_index'])
rows=[]
for hit in inventory['hits']:
    assert hit['parsed'],hit
    assert '\\archive\\pc\\mod\\' not in hit['archive'].lower(),hit
    assert sha(Path(hit['raw']))==hit['sha256'],hit
    idx=graph_index(read(Path(hit['json'])))
    ns={p:{k:v for k,v in n.items() if k not in ('phaseGraph','sockets')} for p,n in idx.items()}
    objects=list(walk(ns))
    command_nodes={p:n for p,n in ns.items() if any(v.get('$type','').startswith('AI') and 'Command' in v.get('$type','') for v in walk(n))}
    phases=[]
    for p,n in ns.items():
        if n['$type']!='questPhaseNodeDefinition':continue
        sub={q:v for q,v in ns.items() if q.startswith(p+'/')}
        phases.append({'path':p,'node_count':len(sub),'types':dict(collections.Counter(v['$type'] for v in sub.values())),
            'prefabs':[value(v) for v in n.get('phaseInstancePrefabs',[])],
            'external_phase':value(n.get('phaseResource',{}).get('DepotPath')),
            'AI_command_types':sorted({v['$type'] for v in walk(sub) if v.get('$type','').startswith('AI') and 'Command' in v.get('$type','')})})
    rows.append({'resource':hit['depot'],'source':hit['json'],'sha256':hit['sha256'],'archive':hit['archive'],
        'candidate_indices':byres[hit['depot']],'W3_group1':not bool(byres[hit['depot']]),
        'node_count':len(idx),'node_types':dict(collections.Counter(n['$type'] for n in idx.values())),
        'AI_command_types':sorted({v['$type'] for v in objects if v.get('$type','').startswith('AI') and 'Command' in v.get('$type','')}),
        'command_nodes':command_nodes,'nested_phases':phases,
        'community_actions':sorted({v['action'] for v in objects if v.get('$type')=='questCommunityTemplate_NodeType'}),
        'write_node_types':sorted({v['$type'] for v in objects if any(s in v.get('$type','') for s in ('ManagerNodeDefinition','CheckpointNodeDefinition','SceneNodeDefinition'))}),
        'shooting_dependencies':sorted({v['$value'] for n in command_nodes.values() for v in walk(n) if v.get('$type') in ('NodeRef','ResourcePath') and v.get('$value') not in ('0',None)})})
assert len(rows)==168 and len({r['resource'] for r in rows})==168
result={'status':'PASS_EXACT_EXTERNAL_PHASE_PAYLOAD_CENSUS_NOT_ALLOWLIST',
    'counts':{'archives':inventory['archives'],'resources':len(rows),'unique_single_native_hits':len(rows),
        'outside_W3_resources':167,'W3_resources':1,'mod_overrides':0,
        'resources_with_AI_commands':sum(bool(r['AI_command_types']) for r in rows),
        'resources_with_ForceShoot':sum('AIForceShootCommandParams' in r['AI_command_types'] for r in rows),
        'resources_with_nested_external_phases':sum(any(p['external_phase'] not in (None,'0') for p in r['nested_phases']) for r in rows)},
    'rows':rows,'game_writes':0,'save_writes':0}
dest=OUT/'external_assessment_01.json';assert not dest.exists()
dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['counts'],indent=2))
print(json.dumps([{'resource':r['resource'],'id':r['candidate_indices'],'AI':r['AI_command_types'],'community_actions':r['community_actions'],'nodes':r['node_count'],'types':r['node_types']} for r in rows if r['AI_command_types'] or r['W3_group1']],indent=2))
