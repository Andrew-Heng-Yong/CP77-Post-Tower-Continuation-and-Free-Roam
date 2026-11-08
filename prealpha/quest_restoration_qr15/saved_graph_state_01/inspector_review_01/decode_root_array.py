"""Independently decode the already-extracted 17 parent bytes; never reads a save."""
from pathlib import Path
import hashlib,json,struct,sys
from inspect_lock import Image,HERE
W=HERE.parents[3]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def fnv(data,seed,prime,mask):
    for byte in data:seed=((seed^byte)*prime)&mask
    return seed
def fnv32(data,seed=0x811c9dc5):return fnv(data,seed,0x1000193,0xffffffff)
def path64(p):return fnv(p.lower().replace('/','\\').encode(),0xcbf29ce484222325,0x100000001b3,0xffffffffffffffff)
def vlq(data):
    assert data
    first=data[0];value=first&0x3f;cursor=1;cont=bool(first&0x40)
    for shift in [6,13,20,27]:
        if not cont:break
        assert cursor<len(data)
        b=data[cursor];cursor+=1
        assert shift!=27 or b&0x7f<=0xf
        value|=(b&0x7f)<<shift;cont=bool(b&0x80)
    assert not cont
    return -value if first&0x80 else value,cursor

def main():
    out=HERE/'root_binding_decode_01.json';assert not out.exists()
    base=W/'prealpha/quest_restoration_qr15'
    extraction=read(base/'root_saved_resource_array_01/extraction.json')
    gap=Path(extraction['gap_path']);data=gap.read_bytes()
    assert sha(gap)==extraction['gap_sha256'] and len(data)==extraction['bytes']==17
    assert extraction['source_unchanged'] and extraction['save_writes']==extraction['game_calls']==0
    bnd={r['name']:r for r in extraction['boundaries']}
    assert extraction['start']==bnd['FactsDB']['offset']+bnd['FactsDB']['size']
    assert extraction['end']==bnd['customArray']['offset']
    assert extraction['end']-extraction['start']==len(data)==bnd['FactsDB']['trailing_size']
    count,cursor=vlq(data)
    assert 0<=count<=64 and cursor+8*count==len(data)
    values=struct.unpack_from('<'+'Q'*count,data,cursor)
    root_manifest=read(base/'root_binding_providers_01/manifest.json')
    assessment=read(base/'analysis_01/result.json')
    providers={r['depot']:r for r in root_manifest['resources']+assessment['provider_pins']}
    for r in providers.values():
        assert sha(r['raw'])==r['sha256'] and sha(r['json'])==r['json_sha256']
        assert path64(r['depot'])==int(r['key'])
    bindings=[]
    for i,v in enumerate(values):
        matches=[r for r in root_manifest['resources'] if int(r['key'])==v]
        assert len(matches)==1 and matches[0]['depot'].endswith('.quest')
        bindings.append({'index':i,'resource_path_u64':str(v),'depot':matches[0]['depot']})
    ep1=[r for r in bindings if r['depot']=='ep1\\quest\\ep1.quest'];assert len(ep1)==1
    root_index=ep1[0]['index']
    im=Image();seeds={i:struct.unpack_from('<I',im.data,im.off(0x37015b8+i*4))[0] for i in range(count)}
    def phase_hash(path):
        raw=struct.pack('<'+'H'*len(path),*path)
        return fnv32(raw,seeds[path[0]])
    def key(path,node):return fnv32(struct.pack('<II',node,phase_hash(path)))
    facts=read(base/'stores_autosave8_01/facts.json')
    assert facts['sha256']==extraction['source_sha256'] and facts['metadata_sha256']==extraction['metadata_sha256']
    tables={t['physical_child_ordinal']:{int(e['key_u32']):e['value_u32'] for e in t['entries']} for t in facts['tables']}
    assert set(tables)==set(range(1,11))
    for t in facts['tables']:assert len(t['entries'])==len(tables[t['physical_child_ordinal']])
    models={}
    def model(depot):
        if depot not in models:
            m=Resource(read(providers[depot]['json'])).normalize();assert not m['errors'];models[depot]=m
        return models[depot]
    depot='ep1\\quest\\ep1.quest';graph='root';path=[root_index]
    steps=[];contexts=[]
    hops=[0,10,5,2,50,19,5,1]
    for node in hops:
        g=model(depot)['graphs'][graph];contexts.append((depot,graph,path[:],g))
        n=g['nodes'][str(node)];assert n['type']=='questPhaseNodeDefinition'
        p=n['payload'];external=p.get('phaseResource',{}).get('DepotPath',{}).get('$value')
        if external in ['0','None',0]:external=None
        embedded=graph+'/'+str(node)
        has_embedded=embedded in model(depot)['graphs']
        assert bool(external)^has_embedded,(depot,graph,node,external,has_embedded)
        step={'depot':depot,'graph':graph,'phase_node':node,'phase_path_before':path[:],
              'source_json_sha256':providers[depot]['json_sha256']}
        path.append(node)
        if external:depot=external;graph='root'
        else:graph=embedded
        step.update({'target_depot':depot,'target_graph':graph,'phase_path_after':path[:]});steps.append(step)
    g=model(depot)['graphs'][graph];contexts.append((depot,graph,path[:],g))
    assert path==[root_index,0,10,5,2,50,19,5,1]
    assert depot.endswith('sts_ep1_03_gameplay.questphase') and graph=='root/1'
    hits=[];nodes=[];key_candidates={}
    for resource,gp,pp,g in contexts:
        for node in g['nodes'].values():
            n=int(node['id']);k=key(pp,n)
            row={'depot':resource,'graph':gp,'phase_path':pp,'node':n,'type':node['type'],
                 'phase_path_hash_u32':str(phase_hash(pp)),'key_u32':str(k),
                 'graph_store_rows':[{'store':s,'value_u32':tables[s][k]} for s in range(2,11) if k in tables[s]]}
            nodes.append(row);key_candidates.setdefault(k,[]).append([pp,n])
            if row['graph_store_rows']:hits.append(row)
    collisions={str(k):v for k,v in key_candidates.items() if len(v)>1}
    assert not collisions
    result={'result':'PASS_EXACT_SAVED_ROOT_RESOURCE_BINDING_AND_TARGETED_KEY_LOOKUP',
       'exe_sha256':im.sha,'gap_hex':data.hex(),'gap_sha256':sha(gap),'count':count,'count_bytes':cursor,
       'members':bindings,'ep1_root_index':root_index,'seed_values':{str(i):hex(v) for i,v in seeds.items()},
       'startup_path':path,'startup_phase_path_hash_u32':str(phase_hash(path)),
       'source_ancestry_steps':steps,'candidate_contexts':len(contexts),'candidate_nodes':len(nodes),
       'nodes_with_serialized_graph_rows':hits,'nodes_with_rows_count':len(hits),
       'immediate_startup_actions':[n for n in nodes if n['phase_path']==path and n['node'] in [101,142,143]],
       'candidate_hash_collision_check':'No collisions within these exact inspected graph contexts; global collision freedom not asserted',
       'source_body_sha256':extraction['source_sha256'],'metadata_sha256':extraction['metadata_sha256'],
       'input_hashes':{str(p.relative_to(W)):sha(p) for p in [gap,base/'root_saved_resource_array_01/extraction.json',base/'root_binding_providers_01/manifest.json',base/'stores_autosave8_01/facts.json',base/'analysis_01/result.json']},
       'limits':['Native stream version mapping to WKit header still must be checked; exact17byte gap and both resourcehashes corroborate schema.',
          'All key hits are serialized values in one historical body; not current runtime or executed-node proof.',
          'Missing candidate keys are serialized absence, not generic state0 or owner retirement.',
          'No handler queue, registeredphase tree or external lease liveness decoded.'],
       'save_reads':0,'game_api_calls':0,'runtime_changes':0}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({k:v for k,v in result.items() if k not in ['source_ancestry_steps','input_hashes','nodes_with_serialized_graph_rows']})
    print('Hits',json.dumps(hits,indent=2))

if __name__=='__main__':main()
