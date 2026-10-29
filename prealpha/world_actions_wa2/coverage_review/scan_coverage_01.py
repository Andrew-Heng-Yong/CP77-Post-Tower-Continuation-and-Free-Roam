"""Read-only graph census of 240 native prefab references outside W3."""
import collections, hashlib, json
from pathlib import Path

OUT=Path(__file__).resolve().parent
WS=OUT.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x,list):
        for v in x: yield from walk(v)
def value(x): return x.get('$value') if isinstance(x,dict) else x
def unhandle(x,handles):
    if not x:return None
    return x.get('Data') or handles.get(x.get('HandleRefId'))
def graph_index(doc):
    handles={d['HandleId']:d['Data'] for d in walk(doc) if 'HandleId' in d and 'Data' in d}
    root=unhandle(doc['Data']['RootChunk']['graph'],handles)
    result={}
    def visit(g,path):
        for h in g.get('nodes',[]):
            n=unhandle(h,handles)
            assert n is not None, (path,h)
            p=path+'/'+str(n['id']);result[p]=n
            child=unhandle(n.get('phaseGraph'),handles)
            if child:visit(child,p)
    visit(root,'root')
    return result,handles
def payload(n):return {k:v for k,v in n.items() if k not in ('phaseGraph','sockets')}

cp=WS/'diagnostics/world_npc_idle_20261026_02/families/census_03.json'
mp=WS/'prealpha/world_workspots_w2/manifest_03.json'
ap=WS/'prealpha/world_workspots_w2/audit_01.json'
native=read(cp);manifest=read(mp);old=read(ap)
groups={g['id']:g for g in manifest['groups']}
assert len(groups)==237 and len(native['rows'])==477
excluded={r['candidate_index']:r for r in old['excluded']}
sources={}
for r in native['rows']:
    if r['candidate_index'] not in groups:
        s=r['source']
        if s not in sources:sources[s]=graph_index(read(WS/s))
rows=[]
for r in native['rows']:
    if r['candidate_index'] in groups:continue
    idx,handles=sources[r['source']]
    owner=idx[r['node_path']]
    descendants={p:n for p,n in idx.items() if p.startswith(r['node_path']+'/')}
    own_payload=payload(owner)
    ns={p:payload(n) for p,n in descendants.items()}
    types=collections.Counter(n['$type'] for n in descendants.values())
    allpayload=list(walk(ns))
    action_payloads=[{'path':p,'type':n['$type'],'definition':v} for p,n in ns.items() for v in walk(n) if v.get('$type','').startswith('AI') and ('Command' in v.get('$type','') or 'Action' in v.get('$type',''))]
    refs=[v['$value'] for v in allpayload if v.get('$type') in ('NodeRef','ResourcePath') and v.get('$value') not in ('0',None)]
    child_phases=[]
    for p,n in descendants.items():
        if n['$type']!='questPhaseNodeDefinition':continue
        sub={q:payload(v) for q,v in descendants.items() if q.startswith(p+'/')}
        child_phases.append({'path':p,'node_count':len(sub),'types':dict(collections.Counter(v['$type'] for v in sub.values())),
            'prefabs':[value(v) for v in n.get('phaseInstancePrefabs',[])],
            'external_phase':value(n.get('phaseResource',{}).get('DepotPath')),
            'ai_commands':sorted({v['$type'] for v in walk(sub) if v.get('$type','').startswith('AI') and 'Command' in v.get('$type','')}),
            'community_actions':sorted({v['action'] for v in walk(sub) if v.get('$type')=='questCommunityTemplate_NodeType'})})
    community_refs=set(r.get('community_spawners',[]))
    support_aliases=[{'id':g['id'],'prefab':g['prefab'],'shared_community_refs':sorted(community_refs & set(g['community_refs']))} for g in groups.values() if community_refs & set(g['community_refs'])]
    rows.append({
        'candidate_index':r['candidate_index'],'source':r['source'],'node_path':r['node_path'],'full_ref':r.get('full_ref'),
        'exclusion':excluded[r['candidate_index']]['reason'],'asset_classification':r['asset_classification'],'asset_reasons':r.get('asset_reasons'),
        'binding':r['binding_classification'],'community_refs':sorted(community_refs),'registry_evidence':r.get('registry_evidence',[]),
        'existing_W3_shared_community_owners':support_aliases,
        'external_phase':value(owner.get('phaseResource',{}).get('DepotPath')),
        'descendant_nodes':len(descendants),'descendant_types':dict(types),'nested_phases':child_phases,
        'ai_command_payloads':action_payloads,'native_dependency_refs':sorted(set(refs)),
        'interesting_node_payloads':{p:n for p,n in ns.items() if n['$type'] in ('questCombatNodeDefinition','questMovePuppetNodeDefinition','questWorkspotNodeDefinition','questSceneNodeDefinition','questAudioNodeDefinition','questAudioManagerNodeDefinition','questVehicleNodeDefinition','questCrowdManagerNodeDefinition','questPuppetAIManagerNodeDefinition')}
    })
assert len(rows)==240
result={'status':'READ_ONLY_OUTSIDE_W3_ACTION_CENSUS_NOT_ALLOWLIST','counts':{
    'native_prefab_references':477,'W3_restored_references':237,'outside_W3_references':len(rows),
    'outside_unique_owners':len({(r['source'],r['node_path']) for r in rows}),
    'exclusion_counts':dict(collections.Counter(r['exclusion'] for r in rows)),
    'outside_with_AI_commands':sum(bool(r['ai_command_payloads']) for r in rows),
    'outside_with_nested_phases':sum(bool(r['nested_phases']) for r in rows),
    'outside_external_phase':sum(r['external_phase'] not in (None,'0') for r in rows),
    'outside_shared_W3_community':sum(bool(r['existing_W3_shared_community_owners']) for r in rows)},
    'rows':rows,'source_pins':[{'path':p,'sha256':sha(WS/p)} for p in sorted(sources)],
    'input_pins':[{'path':str(p.relative_to(WS)),'sha256':sha(p)} for p in (cp,mp,ap)],'game_writes':0,'save_writes':0}
dest=OUT/'coverage_01.json'
assert not dest.exists(),'Preserve evidence'
dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['counts'],indent=2))
print(json.dumps([{'id':r['candidate_index'],'path':r['node_path'],'prefab':r['full_ref'],'reason':r['exclusion'],'types':r['descendant_types'],'AI':sorted({a['definition']['$type'] for a in r['ai_command_payloads']}),'shared_W3':r['existing_W3_shared_community_owners']} for r in rows if r['ai_command_payloads']],indent=2))
