"""Exact native support census; payload labels do not automatically exclude owners."""
import collections,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def indexed(doc):
    hs={v['HandleId']:v['Data'] for v in walk(doc) if 'HandleId'in v and 'Data'in v}
    def res(v):return v.get('Data',hs.get(v.get('HandleRefId'),v))
    def norm(v):
        if isinstance(v,dict):
            if 'HandleId'in v or 'HandleRefId'in v:return norm(res(v))
            return {k:norm(x) for k,x in v.items() if k not in ('sockets','phaseGraph')}
        if isinstance(v,list):return[norm(x) for x in v]
        return v
    idx={}
    def visit(g,p):
        for h in g['nodes']:
            n=res(h);q=p+'/'+str(n['id']);idx[q]=norm(n)
            if n.get('phaseGraph'):visit(res(n['phaseGraph']),q)
    visit(res(doc['Data']['RootChunk']['graph']),'root');return idx
c=read(W/'diagnostics/world_npc_idle_20261026_02/families/census_03.json')
m=read(W/'prealpha/world_workspots_w2/manifest_03.json');installed={g['id']:g for g in m['groups']};installed[250]=read(W/'prealpha/world_actions_wa2/candidate_01/script_source/support_build_01.json')['new_group']
sectors={s['full_ref']:s for s in c['sectors']};cache={};extcache={}
ext=read(W/'prealpha/world_actions_wa2/coverage_review/external_01/report_01.json');hits={h['depot']:h for h in ext['hits']}
always=W/'prealpha/world_actions_wa2/coverage_review/shooting_sources_01/ep1_1_nightcity.archive/always_loaded_0.streamingsector.json'
worldrefs=set(re.findall(r'"\$value": "(\$/[^"\r\n]*)"',always.read_text(encoding='utf-8-sig')))
aliases={}
for s in worldrefs:
    for alias in s.split(';')[1:]:aliases.setdefault(alias,set()).add(s.split(';')[0])
rows=[]
for row in c['rows']:
    r=dict(row);id=r['candidate_index'];s=r['source']
    if s not in cache:cache[s]=indexed(read(W/s))
    owner=cache[s][r['node_path']]
    ns={p:n for p,n in cache[s].items() if p.startswith(r['node_path']+'/')}
    external=owner.get('phaseResource',{}).get('DepotPath',{}).get('$value')
    extpin=None
    if external in hits:
        hit=hits[external]
        if external not in extcache:extcache[external]=indexed(read(Path(hit['json'])))
        ns=extcache[external];extpin={'resource':external,'binary':hit['raw'],'sha256':hit['sha256'],'json':hit['json']}
    nrefs={v['$value'] for v in walk(ns) if v.get('$type')=='NodeRef' and isinstance(v.get('$value'),str)}
    communities={v.get('spawnerReference',{}).get('$value') for v in walk(ns) if v.get('$type')=='questCommunityTemplate_NodeType'}-{None,'0'}
    full=r.get('full_ref');candidates=set()
    if not full:
        alias=r['alias']
        for ref in nrefs|worldrefs:
            base=ref.split(';')[0]
            if not base.startswith('$/'):continue
            seg=base.split('/')
            if alias in seg:candidates.add('/'.join(seg[:seg.index(alias)+1]))
        candidates.update(aliases.get(alias,set()))
        if len(candidates)==1:full=next(iter(candidates))
    refs=[];unresolved=[]
    for ref in sorted(communities|set(r.get('community_spawners',[]))|{e['ref'] for e in r.get('registry_evidence',[])}):
        vals={ref.split(';')[0]} if ref.startswith('$/') else aliases.get(ref,set())
        if len(vals)==1:refs.extend(vals)
        else:unresolved.append(ref)
    refs=sorted(set(refs));within=[ref for ref in refs if full and ref.startswith(full+'/')]
    sec=sectors.get(full)
    r.update({'id':id,'already_supported':id in installed,'resolved_prefab':full,'additional_full_ref_candidates':sorted(candidates),
      'community_refs':refs,'communities_within_prefab':within,'unresolved_community_refs':unresolved,
      'external_source':extpin,'owner_prefabs':owner.get('phaseInstancePrefabs'),
      'decoded_sector':None if not sec else {'json':sec.get('json'),'resource':sec.get('resource'),'parsed':sec.get('parsed'),'winner':sec.get('winner'),'node_types':sec.get('node_types'),'population_spawners':sec.get('population_spawners'),'devices':sec.get('devices'),'ambient_nodes':sec.get('ambient_nodes'),'outside_node_refs':sec.get('outside_node_refs'),'outside_placements':sec.get('outside_placements'),'unclassified_nodes':sec.get('unclassified_nodes'),'suspicious_nested_types':sec.get('suspicious_nested_types')},
      'native_binary':str(W/Path(s).with_suffix('')),'native_binary_sha256':sha(W/Path(s).with_suffix(''))})
    rows.append(r)
result={'status':'WA3_ALL477_SUPPORT_BINDING_INPUT_NOT_ALLOWLIST','counts':{'all_rows':477,'already_supported':238,'remaining':239,'newly_resolved_prefab_refs':sum(not r['full_ref'] and bool(r['resolved_prefab']) for r in rows),'remaining_with_community_ref':sum(bool(r['community_refs']) and not r['already_supported'] for r in rows)},'rows':rows,'game_writes':0,'save_writes':0}
dest=H/'census_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['counts'],indent=2))
print('Unresolved prefabs:',[(r['id'],r['alias'],r['unresolved_community_refs']) for r in rows if not r['already_supported'] and not r['resolved_prefab']])
